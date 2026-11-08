# Verification — 8 November 2026

## Completed

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

Native Hermes Desktop activation and interactive screenshot review could not be performed: the available browser automation failed on `timeoutMs`; native capture failed with ScreenCaptureKit -3811. Server rendering and SDK validation are completed, but do not substitute for native interactive QA. The repository's chart is an evidence illustration, not a screenshot of native Hermes Desktop.

The test-only FastAPI/Starlette TestClient emits a deprecation warning for httpx; tests pass. Unsupported hardware is handled as unknown; physical Linux/Windows energy telemetry is not implemented. There is no cloud energy or CO2 estimate.

Catalog admission remains the Nous maintainers' decision. Hackathon submission additionally needs the owner's contact details and an X demo-post URL. Building the plugin, opening the catalog PR, publishing a post and submitting the form are distinct states.
