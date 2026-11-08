Adds only `plugin-catalog/hermes-watt.yaml`, pinned to public v0.1.0 source at `ead82379e6329e8c55c279665c6e09481234a18f`. Submitted by the repository owner for the Hermes Plugin Hackathon.

Hermes Watt offers a native Desktop page and `/watt` for profile-scoped task receipts: observed model requests, linked auxiliary calls, failures and duration. Opt-in Apple CPU/GPU energy is labelled estimated and system-wide; cloud inference energy stays unknown. Its separate local batching experiment applies identical answer checks before showing an efficiency result. Original plugin code; README acknowledges Traceverse's existing energy observability.

### Disclosure

No runtime third-party network, uploads, credentials, shell processes or background service. Local SQLite stores hashed IDs, timestamps, safe model labels, usage counts and energy estimates; no prompt/response text or raw provider errors. Apple-only `zeus-apple-silicon==1.1.0` reads IOReport through native code in-process, explicitly opt-in. The manually launched developer benchmark sends synthetic tickets only to a loopback model server. Its preview is loopback-only and is not started by the plugin. [Full disclosure](https://github.com/michaelversluis/hermes-watt/blob/ead82379e6329e8c55c279665c6e09481234a18f/docs/PRIVACY.md).

### Verification

Full pinned Git tree passed `hermes plugins validate --install-deps` on official Hermes 0.23.0: all 16 checks, no warnings. [Green GitHub CI](https://github.com/michaelversluis/hermes-watt/actions/runs/42451700498): Python 3.11/3.14 tests (41 each), Desktop render checks and official catalog validation. A real isolated CLI/gateway task recorded main plus auxiliary requests; `/watt` displayed its receipt on resume. Catalog structural validation passed locally. No core changes or full Hermes test-suite claim.

The successful local experiment had 72/72 correct answers across both variants and 59.4% lower median estimated CPU/GPU energy for batching on one M3 Max. Earlier failed-quality evidence is retained with no saving claim. No cloud/CO2/general savings claim.

### Visual QA limitation

Native Desktop interactive QA is still unverified because the available browser/capture tooling failed. Component render tests and SDK validation pass. Known issues declare this limitation. This [60-second evidence video](https://github.com/michaelversluis/hermes-watt/blob/ead82379e6329e8c55c279665c6e09481234a18f/docs/evidence/hermes-watt-demo.mp4) and the evidence image are labelled data replay, not fabricated native screenshots. A native screenshot remains to be supplied.

Maintainers retain catalog admission and merge authority.
