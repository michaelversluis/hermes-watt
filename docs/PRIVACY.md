# Data and dependency disclosure

## Runtime

- **Inputs:** public observer-hook fields: session/turn/request correlation identifiers, model label, usage counts, lifecycle flags. Raw prompt, history, output and error fields are ignored.
- **Storage:** `plugin_data_dir("hermes-watt")/receipts.sqlite3` in the active Hermes profile. IDs are SHA-256-derived, not reversible plaintext. These identifiers are pseudonymous, not an anonymity guarantee. Model labels, timestamps, counts and hardware estimates are retained locally until the operator removes the data. There is no automatic retention deletion in 0.1.0.
- **Network:** no third-party runtime calls. Desktop fetches only the plugin's authenticated read-only Hermes endpoints through `ctx.rest`. No uploads or remote metrics.
- **Hardware:** opt-in Apple IOReport access in-process. No sudo, shell subprocess, permanent sampler service or polling daemon. Two snapshots per task window.
- **Secrets:** no declared secrets, credentials or environment keys. No reads from credential files. No telemetry payload or raw exception logging.
- **Hooks:** nine declared public observer hooks, no tools or middleware, plus `/watt`. Never mutates conversation messages or starts a model request.
- **Failure behavior:** observer exceptions are caught; missing estimates remain unknown. Storage operations have a 200 ms SQLite lock timeout. This is low-overhead synchronous observation, not a zero-overhead guarantee. A native backend failure below Python cannot be guaranteed recoverable.
- **Access:** `/watt` uses only the host's bound session. Desktop uses the active profile namespace and host authentication, never a client-supplied path/session selector.

## Dependencies

`zeus-apple-silicon==1.1.0` is installed only on Darwin arm64. Its Python bindings read Apple IOReport counters through native CoreFoundation/IOReport code. Source reviewed before use; no network or command execution in the measurement path. This is third-party native code, not a sandbox boundary. No dependency version float or self-updater. FastAPI and React/SDK come from Hermes; development dependencies are separately pinned.

Sources: [Zeus Apple backend](https://github.com/ml-energy/zeus-apple-silicon), [Zeus measurement documentation](https://ml.energy/zeus/measure/).

## Manually run development tools

`scripts/benchmark.py` sends only the included synthetic tickets to a user-started unauthenticated loopback model endpoint. It refuses non-loopback URLs and HTTP redirects. It creates local reports and receipts in an explicitly supplied directory. It does not download or launch a model. `demo/serve.py` is an unauthenticated loopback-only development preview; do not port-forward it. The plugin does not start either tool.

The public evidence contains synthetic answers only. Developer environments, model files, local Hermes settings and original runtime logs are excluded from Git. No WVE customer data is used.
