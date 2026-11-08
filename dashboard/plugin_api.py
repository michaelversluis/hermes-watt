"""Local receipt ledger, observer and read-only Desktop API.

Kept together so both documented Hermes loaders import the exact same code,
without sys.path changes or imports from private Hermes internals.
"""
import hashlib
import json
import math
import platform
import re
import sqlite3
import statistics
import threading
import time
from contextlib import contextmanager
from pathlib import Path

from fastapi import APIRouter, HTTPException

METHOD = "apple-ioreport-cpu-gpu/v1"
SCOPE = "Local CPU + GPU, system-wide"
LIMITATION = "Includes other processes. Excludes the rest of the computer, electricity supply losses and remote/cloud inference."


def opaque(value):
    return hashlib.sha256(str(value).encode("utf-8")).hexdigest()[:32]


def safe_label(value):
    # Do not persist URLs, arbitrary provider errors, prompts or display names.
    if isinstance(value, str) and re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._:/+-]{0,119}", value) and "://" not in value:
        return value
    return "unknown"


def nonnegative(value):
    if isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value) and value >= 0:
        return float(value)
    return None


def tokens(usage, *keys):
    if not isinstance(usage, dict):
        return None
    for key in keys:
        value = nonnegative(usage.get(key))
        if value is not None and value.is_integer():
            return int(value)
    return None


def storage_root():
    from plugins.plugin_storage import plugin_data_dir
    return plugin_data_dir("hermes-watt")


class AppleSampler:
    """Two chip counters, no sum of overlapping core/cluster/CPU totals."""
    def __init__(self):
        if platform.system() != "Darwin" or platform.machine() != "arm64":
            raise RuntimeError("unsupported_platform")
        from zeus_apple_silicon import AppleEnergyMonitor
        self.monitor = AppleEnergyMonitor()

    def snapshot(self):
        values = self.monitor.get_cumulative_energy()
        cpu = nonnegative(values.cpu_total_mj)
        gpu = nonnegative(values.gpu_mj)
        if cpu is None or gpu is None:
            raise RuntimeError("missing_counters")
        return {"cpu_mj": cpu, "gpu_mj": gpu}

    @staticmethod
    def difference(start, end):
        differences = {k: end[k] - start[k] for k in ("cpu_mj", "gpu_mj")}
        if any(nonnegative(v) is None for v in differences.values()):
            raise ValueError("counter_reset")
        return sum(differences.values()) / 1000.0


class Store:
    def __init__(self, root):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.path = self.root / "receipts.sqlite3"
        self.path.touch(mode=0o600, exist_ok=True)
        with self.connect() as db:
            db.executescript("""
            CREATE TABLE IF NOT EXISTS runs (
              id TEXT PRIMARY KEY, session TEXT NOT NULL, started REAL NOT NULL,
              ended REAL, status TEXT NOT NULL, model TEXT NOT NULL,
              joules REAL, method TEXT, reason TEXT, overlap INTEGER NOT NULL DEFAULT 0);
            CREATE TABLE IF NOT EXISTS attempts (
              id TEXT PRIMARY KEY, run_id TEXT NOT NULL, kind TEXT NOT NULL,
              model TEXT NOT NULL, status TEXT NOT NULL,
              input_tokens INTEGER, output_tokens INTEGER);
            CREATE TABLE IF NOT EXISTS accounting_gaps (run_id TEXT PRIMARY KEY);
            CREATE INDEX IF NOT EXISTS attempt_run ON attempts(run_id);
            CREATE INDEX IF NOT EXISTS run_session ON runs(session, started);
            """)

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.path, timeout=0.2)
        db.row_factory = sqlite3.Row
        try:
            with db:
                yield db
        finally:
            db.close()

    def start(self, run_id, session, model, *, tracked=True, now=None):
        with self.connect() as db:
            db.execute("INSERT OR IGNORE INTO runs(id,session,started,status,model,reason) VALUES(?,?,?,?,?,?)",
                       (run_id, opaque(session), time.time() if now is None else now, "running", safe_label(model),
                        None if tracked else "missing_start"))

    def finish(self, run_id, *, status, joules=None, reason=None, overlap=False, now=None):
        with self.connect() as db:
            db.execute("UPDATE runs SET ended=?,status=?,joules=?,method=?,reason=COALESCE(?,reason),overlap=? WHERE id=? AND status='running'",
                       (time.time() if now is None else now, status, joules, METHOD if joules is not None else None,
                        reason, int(overlap), run_id))

    def attempt(self, run_id, payload, kind, status):
        request_id = payload.get("api_request_id")
        # Without a correlation ID we cannot deduplicate. Preserve a visible gap.
        if not request_id:
            with self.connect() as db:
                db.execute("INSERT OR IGNORE INTO accounting_gaps VALUES(?)", (run_id,))
            return
        ident = opaque(run_id + ":" + str(request_id))
        usage = payload.get("usage")
        model = safe_label(payload.get("response_model") or payload.get("model"))
        with self.connect() as db:
            db.execute("""INSERT INTO attempts VALUES(?,?,?,?,?,?,?)
              ON CONFLICT(id) DO UPDATE SET
                status=CASE WHEN attempts.status='pending' THEN excluded.status ELSE attempts.status END,
                input_tokens=COALESCE(attempts.input_tokens,excluded.input_tokens),
                output_tokens=COALESCE(attempts.output_tokens,excluded.output_tokens),
                model=CASE WHEN attempts.model='unknown' THEN excluded.model ELSE attempts.model END""",
                       (ident, run_id, kind, model, status, tokens(usage, "prompt_tokens", "input_tokens"),
                        tokens(usage, "completion_tokens", "output_tokens")))

    def receipts(self, *, session=None, limit=100):
        where, args = ("WHERE session=?", [opaque(session)]) if session is not None else ("", [])
        with self.connect() as db:
            rows = db.execute(f"SELECT * FROM runs {where} ORDER BY started DESC LIMIT ?", [*args, min(max(limit, 1), 200)]).fetchall()
            answer = []
            for row in rows:
                receipt = dict(row)
                attempts = [dict(a) for a in db.execute("SELECT kind,model,status,input_tokens,output_tokens FROM attempts WHERE run_id=?", (row["id"],))]
                receipt.pop("session")
                receipt["attempts"] = attempts
                receipt["requests"] = len(attempts)
                receipt["accounting_complete"] = not db.execute("SELECT 1 FROM accounting_gaps WHERE run_id=?", (row["id"],)).fetchone() and all(a["status"] != "pending" for a in attempts)
                receipt["failed_requests"] = sum(a["status"] == "error" for a in attempts)
                receipt["auxiliary_requests"] = sum(a["kind"] == "auxiliary" for a in attempts)
                receipt["duration_s"] = max(0, (row["ended"] or time.time()) - row["started"])
                known = row["joules"] is not None
                receipt["energy"] = {"status": "estimated" if known else "unknown", "joules": row["joules"],
                                     "wh": row["joules"] / 3600 if known else None, "method": row["method"],
                                     "scope": SCOPE, "limitation": LIMITATION, "overlap": bool(row["overlap"])}
                receipt["inference_energy"] = {"status": "unknown", "reason": "No provider energy telemetry. Local chip activity is shown separately."}
                receipt["quality"] = "not assessed"
                receipt["tips"] = advice(receipt)
                answer.append(receipt)
            return answer

    def latest(self, session):
        rows = self.receipts(session=session, limit=1)
        return rows[0] if rows else None


def advice(receipt):
    tips = []
    if not receipt.get("accounting_complete", True):
        tips.append("Request accounting is incomplete: correlation IDs or completion events were missing. The observed count is a lower bound.")
    if receipt["failed_requests"]:
        tips.append("Some requests failed. Inspect the cause before rerunning the task; failed attempts may still consume energy.")
    if receipt["auxiliary_requests"]:
        tips.append("Background model calls are included in the request count. Review whether that work is useful for this workflow.")
    if receipt["requests"] >= 3:
        tips.append("For independent, repetitive items, test batching against the same quality checks before adopting it.")
    if receipt["energy"]["overlap"]:
        tips.append("Tasks overlapped. Their local energy windows must not be added together or treated as exclusive task energy.")
    if not tips:
        tips.append("Compare repeated tasks with the same acceptance checks. Fewer tokens alone do not prove an energy saving.")
    return tips


class Recorder:
    HOOKS = ("pre_llm_call", "pre_api_request", "post_api_request", "api_request_error",
             "pre_auxiliary_call", "post_auxiliary_call", "on_session_end", "on_session_finalize", "on_session_reset")

    def __init__(self, root_provider, *, local_energy=lambda: False, enabled=lambda: True, sampler_factory=AppleSampler,
                 clock=time.time):
        self.root_provider = root_provider
        self.local_energy = local_energy
        self.enabled = enabled
        self.sampler_factory = sampler_factory
        self.clock = clock
        self.lock = threading.RLock()
        self.active = {}
        self.samplers = {}
        self.errors = 0

    def handle(self, event, payload):
        # Telemetry must never change, block, retry or crash the agent's work.
        try:
            with self.lock:
                self.observe(event, payload)
        except Exception:
            self.errors += 1  # No raw exception/payload logging.
        return None

    def observe(self, event, p):
        if not self.enabled():
            for key, item in list(self.active.items()):
                Store(item["root"]).finish(key[1], status="incomplete", reason="recording_disabled", overlap=item["overlap"], now=self.clock())
                self.active.pop(key)
            return
        session = p.get("old_session_id") if event == "on_session_reset" else p.get("session_id")
        if not session:
            return
        root = str(Path(self.root_provider()).resolve())
        store = Store(root)
        turn = p.get("turn_id")
        if event in {"on_session_finalize", "on_session_reset"}:
            for key, item in list(self.active.items()):
                if item["root"] == root and item["session"] == opaque(session):
                    self.close(key, store, "interrupted")
            return
        if not turn:
            return  # Never guess which concurrent turn owns an event.
        run_id = opaque(json.dumps([str(session), str(turn)]))
        key = (root, run_id)
        if event == "pre_llm_call":
            if key in self.active:
                return
            store.start(run_id, session, p.get("model"), now=self.clock())
            item = {"root": root, "session": opaque(session), "start": None, "overlap": bool(self.active),
                    "reason": "local_measurement_disabled"}
            for active in self.active.values():
                active["overlap"] = True
            if self.local_energy():
                try:
                    if root not in self.samplers:
                        self.samplers[root] = self.sampler_factory()
                    item["start"] = self.samplers[root].snapshot()
                    item["reason"] = None
                except Exception:
                    item["reason"] = "local_measurement_unavailable"
            self.active[key] = item
        elif event == "on_session_end":
            status = "interrupted" if p.get("interrupted") else "completed" if p.get("completed") and not p.get("failed") else "incomplete"
            if key not in self.active:
                store.start(run_id, session, p.get("model"), tracked=False, now=self.clock())
            self.close(key, store, status)
        elif event in {"pre_api_request", "post_api_request", "api_request_error", "pre_auxiliary_call", "post_auxiliary_call"}:
            store.start(run_id, session, p.get("model"), tracked=False, now=self.clock())
            kind = "auxiliary" if "auxiliary" in event else "main"
            status = "pending" if event.startswith("pre_") else "error" if event == "api_request_error" or p.get("error") else "ok"
            store.attempt(run_id, p, kind, status)

    def close(self, key, store, status):
        item = self.active.pop(key, None)
        joules, reason, overlap = None, "missing_start", False
        if item:
            reason, overlap = item["reason"], item["overlap"]
            if item["start"] is not None:
                try:
                    sampler = self.samplers[item["root"]]
                    joules = AppleSampler.difference(item["start"], sampler.snapshot())
                except Exception:
                    reason = "local_measurement_failed"
        store.finish(key[1], status=status, joules=joules, reason=reason, overlap=overlap, now=self.clock())


def render_receipt(r):
    energy = r["energy"]
    amount = f'{energy["wh"]:.5f} Wh (estimated)' if energy["wh"] is not None else "unknown"
    return (f'Hermes Watt · {r["status"]}\nLocal CPU + GPU: {amount}\n'
            f'{r["requests"]} observed model requests · {r["auxiliary_requests"]} background · {r["failed_requests"]} failed\n'
            f'Duration: {r["duration_s"]:.1f}s\nProvider inference energy: unknown\n'
            f'{LIMITATION}\n{r["tips"][0]}')


def summary(store):
    rows = store.receipts(limit=200)
    # Never silently add overlapping measurement windows.
    eligible = [r for r in rows if r["energy"]["wh"] is not None and not r["energy"]["overlap"]]
    return {"version": "0.1.0", "receipts": rows,
            "summary": {"tasks": len(rows), "requests": sum(r["requests"] for r in rows),
                        "estimated_local_wh": sum(r["energy"]["wh"] for r in eligible) if eligible else None,
                        "included_energy_windows": len(eligible), "excluded_energy_windows": len(rows)-len(eligible),
                        "scope": "Latest 200 task windows; overlapping and unknown windows excluded. Not a total AI footprint."},
            "accounting_complete": all(r["accounting_complete"] for r in rows),
            "privacy": "Local metadata only. No prompt text, responses, keys or telemetry uploads."}


def make_comparison(samples, *, model, workload_sha256):
    groups = {name: [s for s in samples if s["variant"] == name] for name in ("baseline", "candidate")}
    rows = {}
    valid = True
    for name, values in groups.items():
        energies = [nonnegative(s.get("joules")) for s in values]
        times = [nonnegative(s.get("seconds")) for s in values]
        valid = valid and len(values) >= 3 and all(e is not None for e in energies) and all(t is not None for t in times)
        valid = valid and all(s.get("passed") == s.get("checked") and s.get("checked", 0) > 0 and not s.get("overlap") for s in values)
        rows[name] = {"label": "One request per item" if name == "baseline" else "Batched items",
                      "runs": len(values), "passed": sum(s.get("passed", 0) for s in values),
                      "checked": sum(s.get("checked", 0) for s in values),
                      "median_joules": statistics.median([e for e in energies if e is not None]) if any(e is not None for e in energies) else None,
                      "median_seconds": statistics.median([t for t in times if t is not None]) if any(t is not None for t in times) else None,
                      "range_joules": [min(energies), max(energies)] if energies and all(e is not None for e in energies) else None}
    baseline, candidate = rows['baseline'], rows['candidate']
    valid = valid and baseline['checked'] == candidate['checked']
    reduction = None
    if valid and baseline['median_joules'] > 0:
        reduction = (1 - candidate['median_joules']/baseline['median_joules']) * 100
    separated = valid and candidate['range_joules'][1] < baseline['range_joules'][0]
    verdict = 'lower_energy' if separated and reduction is not None and reduction > 0 else 'inconclusive'
    return {"schema":"hermes-watt-comparison/v1", "model":safe_label(model), "workload_sha256":workload_sha256,
            "method":METHOD, "baseline":baseline, "candidate":candidate, "verdict":verdict,
            "observed_reduction_percent": reduction,
            "explanation": "Every answer passed the same checks. Candidate energy was lower in every measured repetition." if verdict=='lower_energy' else "Quality, measurement coverage or the repeated energy ranges do not support a saving claim.",
            "scope": SCOPE + ". Alternating run order after warm-up; prompt cache disabled; model loading excluded.",
            "limitations": "Estimated chip energy on this machine and workload only. Includes other processes. Does not prove savings on other models, tasks or cloud providers. No CO2 claim.",
            "samples":samples}


def read_comparison(root):
    path = Path(root) / "comparison.json"
    if not path.is_file():
        return None
    if path.stat().st_size > 1_000_000:
        raise ValueError("comparison_too_large")
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or data.get("schema") != "hermes-watt-comparison/v1":
        raise ValueError("invalid_comparison")
    try:
        samples = data["samples"]
        if not isinstance(samples, list) or len(samples) > 100:
            raise ValueError("invalid_samples")
        for sample in samples:
            if not isinstance(sample, dict) or sample.get("variant") not in {"baseline", "candidate"}:
                raise ValueError("invalid_sample")
            for field in ("passed", "checked"):
                if type(sample.get(field)) is not int or sample[field] < 0:
                    raise ValueError("invalid_checks")
            if sample["passed"] > sample["checked"]:
                raise ValueError("invalid_checks")
        # Never trust an edited summary percentage over its sample evidence.
        report = make_comparison(samples, model=data["model"], workload_sha256=data["workload_sha256"])
        for key in ("created_at", "run_parameters"):
            if key in data:
                report[key] = data[key]
        return report
    except (TypeError, KeyError, AttributeError) as exc:
        raise ValueError("invalid_comparison") from exc


router = APIRouter()


@router.get("/overview")
def overview():
    try:
        return summary(Store(storage_root()))
    except (OSError, sqlite3.Error):
        raise HTTPException(503, "Energy receipts are temporarily unavailable.") from None


@router.get("/comparison")
def comparison():
    try:
        return {"comparison": read_comparison(storage_root())}
    except (OSError, ValueError):
        raise HTTPException(503, "The comparison report could not be read.") from None
