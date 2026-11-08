# Hermes Watt

**Good work. Less waste.** Energy receipts and quality-checked efficiency experiments for [Hermes Agent](https://github.com/NousResearch/hermes-agent).

Token counts tell you how much text moved. They do not tell you how much electricity AI used. Hermes Watt shows what can be estimated locally, keeps cloud energy explicitly unknown, and checks the answers before celebrating a more efficient workflow.

## What works

- A native Hermes Desktop page with task receipts, observed model requests, linked background calls, failures and duration.
- `/watt` for the latest receipt in the current conversation.
- Optional Apple Silicon CPU + GPU energy estimates, always labelled **estimated** and **system-wide**.
- A repeatable local-model experiment: twelve separate classification requests versus one batch, with the same answer checks and three repetitions each.
- No automatic model switching or prompt rewriting. The observer cannot modify agent output.

[60-second evidence video](docs/evidence/hermes-watt-demo.mp4) · [Actual /watt output](docs/evidence/watt-output.txt)

## A real experiment, with boundaries

On an Apple M3 Max, Qwen3-1.7B-Q8_0 classified the same twelve synthetic tickets:

| | One request per ticket | One batched request |
|---|---:|---:|
| Correct answers across three repetitions | 36 / 36 | 36 / 36 |
| Requests per repetition | 12 | 1 |
| Median estimated local CPU + GPU energy | 59.597 J | 24.201 J |
| Range across repetitions | 57.459–59.704 J | 23.259–25.443 J |
| Median duration | 4.79 s | 2.00 s |

That is **59.4% lower estimated local CPU + GPU energy in this experiment**. It includes other local processes, excludes model loading and is not a total-device, cloud, CO₂ or universal AI savings claim. Three repetitions are a small demonstration, not a statistical guarantee. The checks establish correctness for this narrow task only.

[Raw successful evidence](docs/evidence/qwen-1.7b.json) · [Earlier failed experiment](docs/evidence/qwen-0.6b-inconclusive.json) · [Method and reproduction](docs/METHOD.md)

The earlier 0.6B experiment failed the answer checks. Its lower energy did **not** earn a saving claim. That is the point: less computation is only useful when the work still succeeds.

## Install

Requires **Hermes 0.23.0 or newer**. Existing older Hermes installations must be upgraded separately. Nothing in this repository updates your agent automatically.

```sh
hermes plugins install michaelversluis/hermes-watt
hermes plugins enable hermes-watt
```

For an audited immutable install, add `--ref` followed by the full forty-character commit from the catalog PR. Restart your Hermes session. Enable the agent plugin and Desktop plugin for the same profile, then choose **Hermes Watt** in the sidebar or command palette. After a task, `/watt` shows the conversation's receipt.

Request metadata stays local when the plugin is enabled. Hardware energy collection is **off by default**. Opt in through the plugin settings, or merge this into the active profile's `config.yaml` (preserve your other settings):

```yaml
plugins:
  enabled: [hermes-watt]  # append to your existing enabled list
  entries:
    hermes-watt:
      settings:
        recording: true
        local_energy: true
```

Restart the session after changing settings. On unsupported hardware, with collection disabled, or if the hardware backend fails, energy remains **Unknown**. Requests and receipts still work. Apple users may need Xcode Command Line Tools to build the pinned native dependency if no wheel matches their Python.

## Privacy and permissions

No cloud account, API key, telemetry service or plugin-created background process is needed. The runtime reads Hermes observer metadata and, with consent, local hardware counters. It writes a profile-scoped SQLite ledger through Hermes's public plugin storage API. It does not store prompt text, response text, tool arguments or raw provider errors.

The Desktop API is read-only and inherits Hermes authentication. The command uses the host-provided conversation identity. The development preview and benchmark are separate, manually run loopback tools; never expose the preview to the internet. See [full disclosures](docs/PRIVACY.md).

## Development

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/python -m pytest -q
npm ci --ignore-scripts
npm test
python3 scripts/stage.py /tmp/hermes-watt-package
hermes plugins validate /tmp/hermes-watt-package --install-deps
```

The staged package contains only runtime sources, README and license. Demo tools, test environments, model weights and local receipts are never installed with it. The repository also supports ordinary Git installation; its `.gitignore` excludes all local data.

For a local browser preview of the real Desktop component:

```sh
node demo/build.mjs
.venv/bin/python demo/serve.py --data /path/to/your/test-output
```

Open `http://127.0.0.1:18180`. This development adapter is not proof of native Desktop activation. [Verification status](docs/VERIFICATION.md) distinguishes the checks.

## What it deliberately does not infer

- A local CPU/GPU counter is not a cloud datacenter meter.
- Missing energy is not zero.
- Overlapping task windows cannot be summed as exclusive task energy.
- Token reductions alone do not prove energy reductions.
- A cheaper result that fails the answer checks is not an efficiency win.
- Ordinary task quality is **not assessed**; only the synthetic benchmark has answer checks.

Energy observability already exists in projects such as [Traceverse Hermes OTel](https://github.com/Mandark-droid/hermes-otel-plugin). Watt focuses on understandable task receipts and controlled, quality-checked workflow comparisons.

MIT license. Built by Michael Versluis for the Hermes Plugin Hackathon.
