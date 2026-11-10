# Verification — 10 November 2026

## Version 0.2.0

- 63 Python tests passed locally on Python 3.11 and 3.14. Added real loopback HTTP and redirect checks, exact-answer validation, concurrent job claims, cancellation, preserved results, interrupted-host recovery, profile binding and incomplete/overlapping measurement rejection.
- React rendering and DOM interaction tests passed: consent gate, synchronous double-click, bounded request body, progress/cancel states, StrictMode completion refresh, a pending response after a profile switch, and failed/interrupted jobs. These interaction tests execute the real shipped React component with the documented SDK adapter.
- Official Hermes 0.23.0 validation of the runtime package with dependencies: all 16 checks passed, no warnings, safe scan, host isolation compatible.
- **Actual Hermes host integration passed**, using `hermes serve --isolated` from revision `2bd378ed1b8d6bf2192cb26e0a55ff3091e6bd19`. Unauthenticated plugin reads returned 401; authenticated reads returned 200. A repeated start ID reused one job, a distinct concurrent start returned 409, and the worker completed through the real plugin host. Six receipts, 39 observed requests and 72/72 checked answers. [Sanitized proof](evidence/host-v02.json). This is separate from the benchmark results below and makes no additional savings claim.
- Both ten-repeat evidence runs were started and polled through the shipped HTTP routes. All 480 answers passed. Ticket batching: 58.1% lower median estimated local CPU/GPU energy; extraction: 32.7%. Raw data, answer checks and run parameters are public. These are narrow M3 Max/Qwen results, not a general or cloud claim.
- New 60-second 1280×720 H.264 evidence replay and 1200×600 data illustration generated from those exact public samples. The banner and result slide were visually inspected. Both are labelled as recorded evidence, not native UI capture.
- Runtime source: `ee0471b8fe58e51e24b7d6ec3978b6afcb4b8618`. [PR #3](https://github.com/michaelversluis/hermes-watt/pull/3) merged after every check passed. The exact release commit `e77ad6987ff67a116cc54126b0eee358afee93b9` also passed [all CI jobs](https://github.com/michaelversluis/hermes-watt/actions/runs/42777978293), including full-Git-tree catalog validation. The [0.2.0 preview release](https://github.com/michaelversluis/hermes-watt/releases/tag/v0.2.0) is published with the verified MP4 and image assets.

- Catalog 0.2.0 branch `michael/hermes-watt-catalog-v02` is prepared against upstream `825322b1`; one added YAML file, structural validation passed, all 15 upstream checks passed. Creating the Nous PR was refused by GitHub account permissions; the form and X post have not been submitted.

## Earlier 0.1.0 verification (8 November)


- 41 Python tests passed on Python 3.11 and 3.14: units, missing readings, errors, deduplication, concurrent callbacks, overlapping windows, opt-out, reset/disable lifecycle, profile separation, privacy, read-only API and comparison gates.
- Desktop source syntax and React server-render tests passed: empty/unknown states, quality gate, displayed energy and HTML escaping. The preview bundles the exact shipped Desktop component through a development-only SDK adapter.
- Official Hermes 0.23.0 catalog validation with dependency installation: all 16 checks passed, no warnings, security scan safe and host-isolation compatible. Hermes revision `2bd378ed1b8d6bf2192cb26e0a55ff3091e6bd19`.
- Actual isolated Hermes CLI + gateway run against a local Qwen model: plugin loaded through the real loader; one completed receipt, two observed model requests including one background request, no failures, estimated local energy, cloud unknown. `/watt` in the resumed conversation displayed that receipt without another model request. See the raw receipt and formatted command output in `evidence/`.
- The integration smoke used 65,536 context with YaRN scaling because Hermes requires at least 64K. This is separate from the 4,096-context classification benchmark and contributes no claimed saving. The small model's textual answer was not evaluated for quality in this smoke test.
- Genuine local hardware benchmark, three repetitions per variant. All 72 answers correct in the successful run. Earlier failed-quality experiment retained. Raw samples and pinned model source are public.
- 60-second evidence video generated directly from the recorded samples; 1280x720, H.264. It is explicitly labelled an evidence replay, **not a live screen recording**.

- Full published Git tree (including developer tools) passed the official validator with no warnings. GitHub CI passed all jobs for both the source PR and its main merge.
- Plugin [PR #1](https://github.com/michaelversluis/hermes-watt/pull/1) merged after green checks; [0.1.0 preview release](https://github.com/michaelversluis/hermes-watt/releases/tag/v0.1.0) published.
- Prepared upstream catalog branch passed structural validation and all 15 repository checks. Opening the actual Nous PR is blocked by GitHub account/integration permissions; no upstream PR URL exists yet.

## Limits and remaining external checks

Native Hermes Desktop activation and interactive screenshot review remain unverified. On 10 November the Mac was locked and browser navigation failed in the automation layer; earlier native capture also failed with ScreenCaptureKit -3811. Server rendering and SDK validation are completed, but do not substitute for native interactive QA. The repository's chart is an evidence illustration, not a screenshot of native Hermes Desktop.

The test-only FastAPI/Starlette TestClient emits a deprecation warning for httpx; tests pass. Unsupported hardware is handled as unknown; physical Linux/Windows energy telemetry is not implemented. There is no cloud energy or CO2 estimate.

Catalog admission remains the Nous maintainers' decision. The owner supplied submission contact details privately on 10 November; they are intentionally absent from this public repository. Hackathon submission still needs an open catalog PR, an X demo-post URL and form confirmation. Building the plugin, opening the catalog PR, publishing a post and submitting the form are distinct states.
