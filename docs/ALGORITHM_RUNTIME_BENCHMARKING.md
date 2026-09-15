# Algorithm/runtime benchmarking

P7 measures implementation performance **after the mathematical model has been selected and validated**. It is not a model-selection engine and does not certify scientific correctness.

## Benchmark contract

A benchmark manifest is explicit JSON. Example:

```json
{
  "schema_version": 1,
  "name": "production-solver",
  "argv": ["${PYTHON}", "scripts/solve.py"],
  "cwd": ".",
  "timeout_seconds": 300,
  "warmup_runs": 1,
  "measured_runs": 5,
  "expected_outputs": ["results/result.json"],
  "require_stable_outputs": true
}
```

Commands run with `shell=False`. Paths must remain inside the workspace. `${PYTHON}` resolves to the current interpreter.

## Run

```text
mmkit benchmark run . config/benchmark.json --json coordination/benchmark.json
```

The report records warmups, measured runs, wall-clock min/mean/median/max/population standard deviation, environment identity, and SHA-256/size fingerprints for expected output files.

Wall-clock timings are observations for a particular host/run. They can move with CPU, OS, system load, Python/solver versions, cache state, and other environmental factors. MMKit therefore does not treat a small timing change as deterministic truth.

If `require_stable_outputs` is true, output fingerprints must agree across measured runs. This protects optimization work from silently changing deterministic outputs.

## Lock a baseline

A runtime regression threshold is never implicit. Lock it explicitly:

```text
mmkit benchmark lock coordination/benchmark.json \
  --output coordination/benchmark.baseline.json \
  --max-regression-percent 15
```

By default the baseline also locks expected-output identity. Use `--ignore-output-identity` only when outputs are intentionally nondeterministic and another correctness check exists.

For tightly controlled environments, `--require-same-environment` makes an environment mismatch a blocker. Otherwise it is a warning.

## Compare

```text
mmkit benchmark compare \
  coordination/benchmark.json \
  coordination/benchmark.baseline.json \
  --json coordination/benchmark.compare.json
```

The comparison blocks when the benchmark contract changes, the locked output identity changes, or median runtime regression exceeds the explicit threshold. Environment drift is reported separately.

## Interpretation boundary

A benchmark `PASS` means the declared engineering/runtime contract satisfied its current baseline rules. It does **not** mean:

- the mathematical model is correct;
- the solution is globally optimal;
- paper claims are scientifically valid;
- a faster implementation is preferable if it violates other verified requirements.

Use P3 claim/evidence provenance and problem-specific scientific validation for those questions.
