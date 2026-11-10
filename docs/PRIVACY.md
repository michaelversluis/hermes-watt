# Data and dependency disclosure

## Runtime

- **Inputs:** public observer-hook fields: session/turn/request correlation identifiers, model label, usage counts, lifecycle flags. Raw prompt, history, output and error fields are ignored.
- **Storage:** `plugin_data_dir("hermes-watt")/receipts.sqlite3` in the active Hermes profile. IDs are SHA-256-derived, not reversible plaintext. These identifiers are pseudonymous, not an anonymity guarantee. Model labels, timestamps, counts and hardware estimates are retained locally until the operator removes the data. There is no automatic retention deletion in 0.2.0.
- **Network:** ordinary observation makes no model or third-party calls. Desktop uses authenticated Hermes endpoints through `ctx.rest`. After explicit consent, `POST /experiment` sends fixed fictional examples to a user-configured HTTP endpoint on literal `127.0.0.1` or `::1`, with an explicit port and `/v1` path. No DNS hostnames, credentials in URLs, proxy environment variables or HTTP redirects. Only loopback transport is enforced; the operator must ensure that their local server itself serves a local model rather than forwarding remotely.
- **Hardware:** opt-in Apple IOReport access in-process. No sudo, shell subprocess, permanent sampler service or polling daemon. Two snapshots per task window.
- **Secrets:** no declared secrets, credentials or environment keys. No reads from credential files. No telemetry payload or raw exception logging.
- **Hooks:** nine declared public observer hooks, no tools or middleware, plus `/watt`. Observer hooks never mutate conversation messages or start a model request. The separate, explicitly requested comparison does start bounded synthetic model requests.
- **Failure behavior:** observer exceptions are caught; missing estimates remain unknown. Storage operations have a 200 ms SQLite lock timeout. This is low-overhead synchronous observation, not a zero-overhead guarantee. A native backend failure below Python cannot be guaranteed recoverable.
- **Access:** `/watt` uses only the host's bound session. Desktop uses the active profile namespace and host authentication, never a client-supplied path/session selector.

## Explicit comparisons

The button requires a consent flag and accepts only a fixed workload identifier, 3–10 repetitions and a request ID. Clients cannot submit a prompt, endpoint, model, filesystem path or expected answer. The endpoint and model come from this plugin's profile settings through the public read-only config API. The owner profile and settings are captured before the worker thread starts.

One daemon thread runs per active comparison; there is no permanent worker or subprocess. SQLite atomically claims a job and deduplicates repeated request IDs, including concurrent requests. Cancellation is cooperative between local requests (20-second request timeout); the overall deadline is five minutes. If the host exits, an old running state expires and the last completed report is retained. Successful reports replace the previous `comparison.json` atomically; failures and cancellation do not replace it. A cancellation during completion may leave a small pending report file inside the plugin data directory.

The ledger also stores job ID, workload, repetition count, status and progress. `comparison.json` includes synthetic answers, check results, timings and hardware estimates. This storage is separate from ordinary conversation observation, which does not retain prompt or response text. No real conversation is used in the experiment. Energy collection for the experiment is authorized by its checkbox even when ordinary `local_energy` collection is disabled. On unsupported hardware, answers can be checked but energy stays unknown and no saving is claimed.

The experiment detects overlapping observed work in the same profile, including another process, and excludes those windows from savings and totals. It cannot isolate other profiles or unrelated applications from the system-wide counters. Users should close unrelated workloads. Generic failure codes are shown; raw HTTP bodies, URLs and provider exceptions are not logged.

## Dependencies

`zeus-apple-silicon==1.1.0` is installed only on Darwin arm64. Its Python bindings read Apple IOReport counters through native CoreFoundation/IOReport code. Source reviewed before use; no network or command execution in the measurement path. This is third-party native code, not a sandbox boundary. No dependency version float or self-updater. FastAPI and React/SDK come from Hermes; development dependencies are separately pinned.

Sources: [Zeus Apple backend](https://github.com/ml-energy/zeus-apple-silicon), [Zeus measurement documentation](https://ml.energy/zeus/measure/).

## Manually run development tools

`scripts/benchmark.py` sends only the included synthetic workloads to a user-started unauthenticated loopback model endpoint. It uses the same bounded engine as the plugin button and requires `--consent`. It creates local reports and receipts in an explicitly supplied directory. Do not run the standalone CLI and Desktop comparison simultaneously against the same output directory; the API job lock applies to API jobs. It does not download or launch a model. `demo/serve.py` is an unauthenticated loopback-only development preview; do not port-forward it. The plugin does not start either tool.

The public evidence contains synthetic answers only. Developer environments, model files, local Hermes settings and original runtime logs are excluded from Git. No WVE customer data is used.
