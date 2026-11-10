Adds only `plugin-catalog/hermes-watt.yaml`, pinning the public 0.2.0 release to `e77ad6987ff67a116cc54126b0eee358afee93b9`. Submitted by the repository owner for the Hermes Plugin Hackathon.

Hermes Watt offers a Desktop page and `/watt` for profile-scoped energy receipts: observed main/auxiliary model requests, failures and duration. Apple CPU/GPU estimates are opt-in, system-wide and explicitly estimated; provider inference energy stays unknown. Its new comparison button runs two fixed synthetic workloads, with identical answer checks before any efficiency claim. This is original plugin code; the README acknowledges Traceverse's existing energy observability.

### Disclosure

Ordinary hooks only observe metadata and cannot change agent output. No conversation prompts/responses, raw errors, credentials or telemetry uploads are retained. Hashed IDs, model labels, counts and estimates remain in profile-local SQLite. The pinned Apple-only native dependency `zeus-apple-silicon==1.1.0` reads IOReport in-process, explicitly opt-in.

**The comparison is an explicit action:** after a consent checkbox it starts one bounded worker thread, sends only built-in fictional examples to the configured literal-loopback HTTP model server, and stores synthetic answers plus check results. No arbitrary client prompt/URL/path, DNS endpoint, proxy, redirect, model download, subprocess or automatic model switching. The local model must be started separately by the operator. Maximum 3–10 repetitions per approach; five-minute deadline plus the current request, 20-second HTTP timeout, cooperative cancel. One API job per profile, atomic request-ID deduplication, captured profile ownership, old report retained on failure/cancel. This is not a permanent background service. [Full disclosure](https://github.com/michaelversluis/hermes-watt/blob/e77ad6987ff67a116cc54126b0eee358afee93b9/docs/PRIVACY.md).

### Verification

- Official Hermes 0.23.0 runtime validation with dependency installation: all 16 checks passed, no warnings, safe scan, host-isolation compatible. The full Git tree passed locally and in [green CI for the exact release commit](https://github.com/michaelversluis/hermes-watt/actions/runs/42777978293). Catalog structural validation and all 15 upstream repository checks passed; only one catalog entry differs from current upstream main.
- 63 Python tests on both Python 3.11 and 3.14; real HTTP/redirect tests, concurrent start/retry/cancel cases, profile ownership and incomplete/overlapping measurement gates.
- React render and DOM interaction tests: consent, rapid double-click, bounded body, progress/cancel, StrictMode and stale responses after a profile switch.
- Real isolated `hermes serve` and plugin-host integration: unauthorized GET 401; authorized GET 200; repeated start ID reused one job; a distinct simultaneous start returned 409; worker completed, 6 receipts/39 requests/72 checked answers. [Sanitized host proof](https://github.com/michaelversluis/hermes-watt/blob/e77ad6987ff67a116cc54126b0eee358afee93b9/docs/evidence/host-v02.json).
- Two real M3 Max/Qwen experiments, ten repetitions per approach, 480/480 answers correct. Ticket batching used 58.1% lower median estimated local CPU/GPU energy; extraction 32.7%. Raw samples and checks are public. Earlier failed-quality evidence remains inconclusive. No cloud, CO2 or universal savings claim.

### Visual QA limitation

Native Desktop interaction and screen recording remain unverified: the Mac is locked and available browser/capture tooling failed. Automated component interaction tests and actual host integration pass, but are not a native visual test. The catalog banner and [60-second evidence replay](https://github.com/michaelversluis/hermes-watt/releases/download/v0.2.0/hermes-watt-evidence-v02.mp4) are labelled recorded data, not fabricated screenshots. `known_issues` declares the limitation; a native screenshot remains to be supplied.

No core changes. Maintainers retain catalog admission and merge authority.
