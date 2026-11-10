# Measurement and reproduction

## Units and scope

The pinned Apple backend provides cumulative CPU-total and GPU energy counters in millijoules. Watt subtracts the two start counters from the two end counters, sums those non-overlapping components, divides by 1,000 for joules and by 3,600 for Wh. It never sums CPU core/cluster counters on top of CPU-total.

Apple IOReport is model-based hardware telemetry. **Estimated** is the correct label; this is not a calibrated wall meter. No quantitative uncertainty interval is claimed. Repeated-run ranges show observed variation only. The scope is system-wide local CPU + GPU, including unrelated processes; it excludes RAM/ANE/display and other device components, supply losses, networking infrastructure, model training and remote inference. Provider inference energy remains unknown, even when the selected model is local, because the chip window cannot isolate that model's energy.

Concurrent windows observed by the same recorder are marked overlapping and excluded from the aggregate. Unknown readings, resets and unavailable counters remain `null`, not zero. Process crashes can leave unfinished receipt rows; they are not evidence of completed tasks or assessed quality. Only correlated API events count; missing request IDs or completion events mark the count incomplete. Background calls with no turn/session context cannot be attributed. A linked background call completing after the turn can be counted in the receipt, but its post-turn activity is outside the energy window. An explicit experiment also checks this profile's ledger for overlapping observed work from another process and excludes those windows from the report and aggregate. Other profiles, unobserved applications and hardware-level scheduling cannot be isolated; background activity remains part of the estimate.

## Controlled demonstration

- Machine: Apple M3 Max. Operating environment was not an isolated lab; unrelated processes contribute noise.
- Model: official Qwen3-1.7B-Q8_0 GGUF, [source and checksum](evidence/model-source.json), served locally by llama.cpp b11669 / commit 620d2225c.
- Two fixed workloads in `dashboard/workloads.json`: twelve support tickets (three categories), and twelve fictional invoice notes (reference plus exact integer amount in euro cents). No customer data. The expected answers are never sent to the model.
- Baseline: one request per item. Candidate: one request for all twelve items. Same model, instructions and answer checks.
- Warm up both shapes, then alternate baseline/candidate and candidate/baseline for ten repetitions of each approach. Model loading and warm-up are outside the reported windows.
- Temperature 0, seed 42, thinking disabled, max output 1024, prompt cache disabled. JSON schema constrains structure, types and allowed ticket categories, not the expected answer for each item.
- All IDs must appear exactly once. Missing, duplicate or extra IDs fail the run. Every answer must exactly match every expected field and its type. Extra fields fail; booleans are not accepted as integers.
- A lower-energy claim requires at least three complete valid runs in each group, all checks passed, no overlapping windows, and the candidate's highest energy below the baseline's lowest. This conservative gate is not a statistical significance test.
- The displayed summary is recomputed from raw samples when loaded. Reports are operator-controlled local evidence, not signed independent attestations.

An earlier Qwen3-0.6B run failed quality (baseline 10/12; batch invalid). Its record is retained as inconclusive. That exploratory run used a concrete JSON example; the successful run removed that example and constrained array length for **both** variants. Do not compare energy between those two experiments as if model and prompt were held constant.

## November 10 results

Both runs were started through the actual `POST /experiment` route and polled through `GET /experiment`; the displayed report was fetched through `GET /comparison`. This used the development HTTP host with the same plugin router and engine, not a claim of native Desktop activation.

| Workload | Individual median [range], J | Batch median [range], J | Checks | Reduction in median |
|---|---|---|---|---|
| Tickets | 55.063 [54.018–57.189] | 23.0595 [20.156–25.235] | 240/240 | 58.1% |
| Extraction | 83.015 [80.644–87.543] | 55.884 [35.135–59.252] | 240/240 | 32.7% |

All forty measured runs completed without observed overlap. There were 260 measured model requests plus four excluded warm-up requests. Repetitions measure variability of these same twelve items; they are not 480 independently sampled real-world tasks. Background desktop and tool activity was not eliminated. No confidence interval or cross-model conclusion is inferred.

The earlier 0.1.0 result used max output 768 and three repetitions. Its evidence remains unchanged; the new result uses the shipped 0.2.0 engine and two workloads.

## Run it yourself

Install Hermes 0.23+, Python test dependencies, and on Apple Silicon `zeus-apple-silicon==1.1.0` in the Python environment used below. Install llama.cpp from its official source and download the pinned [Qwen GGUF](https://huggingface.co/Qwen/Qwen3-1.7B-GGUF/tree/90862c4b9d2787eaed51d12237eafdfe7c5f6077). Verify the checksum in `model-source.json`.

```sh
llama-server -m /path/to/Qwen3-1.7B-Q8_0.gguf \
  --host 127.0.0.1 --port 18082 --alias Qwen3-1.7B-Q8_0 \
  --ctx-size 4096 --parallel 1 --threads 4 --jinja --n-gpu-layers 99
```

Open Hermes Watt in Desktop, select the task and repetition count, give consent and press **Test a lower-energy approach**. Or run the same engine from another terminal:

```sh
.venv/bin/python scripts/benchmark.py \
  --endpoint http://127.0.0.1:18082/v1 --model Qwen3-1.7B-Q8_0 \
  --output /tmp/hermes-watt-experiment --workload tickets --repetitions 10 --consent
node demo/build.mjs
.venv/bin/python demo/serve.py --data /tmp/hermes-watt-experiment
```

Use `--workload extraction` for the second task. `--consent` is mandatory. The engine rejects remote hosts, redirects and proxy variables. Each comparison is bounded to five minutes plus at most the current 20-second request; cancellation takes effect between requests. Only one API-launched job may be active per profile.

View the real component at `http://127.0.0.1:18180`. To view your own result in native Desktop, point `--output` at the current test profile's Hermes Watt data directory, obtained using the documented plugin storage API. Never copy demonstration receipts over an existing user's ledger.

Results depend on hardware, software, workload and background activity. On unsupported machines the experiment can check answers but cannot establish an energy saving.
