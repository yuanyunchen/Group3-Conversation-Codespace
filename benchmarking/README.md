# Benchmarking Toolkit

The `benchmarking/` package provides a reproducible pipeline for evaluating conversation players across a wide variety of scenarios. It emphasizes:

- **Fair comparisons** — every run shares the same simulation engine and reporting utilities.
- **Configurability** — extend scenarios, add players, and customise hyperparameters without shell scripting.
- **Consistency** — results share a unified CSV schema and naming convention, and every run stores its configuration alongside the outputs.

## Directory Overview

```
benchmarking/
├── cli.py                 # Command-line entry point
├── pipeline.py            # Core orchestration logic
├── player_registry.py     # Mapping from short codes to player classes
├── sample_scenarios.py    # Ready-to-run benchmark scenario definitions
├── scenario.py            # Dataclasses describing suites & variants
├── utils.py               # Helper functions for IO and naming
├── visualization.py       # Bar/column chart generation helpers
├── scripts/
│   └── run_default.py     # Convenience launcher (python script)
├── results/               # Auto-generated results (timestamped per run)
└── outputs/               # Reserved for downstream artefacts/plots
```

Each timestamped run records inputs (`scenario_config.json`), tabular outputs (`summary.csv`, per-variant `variant_summary.csv`), human-readable reports, detailed per-round artefacts (JSON, TXT, CSV), and PNG charts.

## Quick Start

Run the default benchmark suite:

```bash
python -m benchmarking.cli --scenario default
```

- Use `--detailed` to force per-round artefacts for every variant.
- Use `--output-root <path>` to redirect outputs.
- Use `--list` to print the available scenario keys (see `sample_scenarios.py`).

A convenience script is also available:

```bash
python benchmarking/scripts/run_default.py
```

### Player Evaluation Pipelines

Run the **single-player pipeline** (focus on one model) in either *simple* (<10 test cases) or *complex* (≥100 test cases) mode:

```bash
# Simple mode
python -m benchmarking.cli --pipeline single --mode simple --targets p3 --detailed

# Complex mode
python -m benchmarking.cli --pipeline single --mode complex --targets p3 --detailed
```

The single-player pipeline automatically sweeps opponent ratios, conversation length, roster size, memory capacity, and competitor matchups. Every sweep includes at least five points so the generated line charts surface meaningful trends. In complex mode it also executes a 4-parameter hyperparameter grid (≥256 runs) with multiple rounds per setting for statistical robustness.

Run the **multi-player comparison pipeline** to test several models under identical conditions:

```bash
# Simple shared pipeline
python -m benchmarking.cli --pipeline multi --mode simple --targets p3 p_bst_medium --detailed

# Complex shared pipeline (grid ≥100 variants)
python -m benchmarking.cli --pipeline multi --mode complex --targets p3 p_bst_medium p_bst_high --detailed
```

Use the **compare pipeline** when you want to benchmark multiple players separately but under the *same test cases* and then line up the results:

```bash
python -m benchmarking.cli \
  --pipeline compare \
  --mode simple \
  --targets p3 p_bst_medium p_bst_high \
  --rounds-per-variant 2 \
  --detailed
```

This runs the single-player suite for each target individually (identical parameters, identical opponents), then builds a `comparison_summary/` folder containing CSV + Markdown tables that juxtapose every case.

These pipelines accept overrides for specific sweeps when needed:

- `--lengths`, `--player-counts`, `--memory-sizes`, `--subject-counts`
- `--ratio-steps` (ratio of targets vs random opponents)
- `--competitors` (competitor roster codes)
- `--rounds-per-variant`, `--base-seed`

Shell helpers are provided:

- `shells/bench_single_pipeline.sh <player> [simple|complex] [output_root]`
- `shells/bench_multi_pipeline.sh <player1> <player2> [...] [--mode simple|complex] [--output <dir>]`
- `shells/bench_player_eval.sh` — runs representative simple flows, with optional complex runs when `RUN_COMPLEX=true`.
- `shells/run_benchmark.sh` — one-stop launcher for `single`, `multi`, `compare`, and static `scenario` runs (same flags as the CLI).

### Output Structure

```
benchmarking/results/<timestamp>_<scenario_slug>/
├── summary.csv                # Aggregated table (primary output)
├── summary_report.txt         # Human-readable report (secondary output)
├── scenario_config.json       # Frozen configuration
├── <suite_slug>/              # One directory per suite
│   ├── suite_focus_<suite>.png# Trend chart (line for numeric sweeps, bar otherwise)
│   └── <variant_slug>/        # Individual variant outputs
│       ├── config.json        # Variant settings
│       ├── variant_summary.csv# Per-player metrics averaged over rounds
│       ├── player_comparison.png
│       └── round_<NN>/        # (If detailed) raw per-round data
│           ├── simulation_results.json
│           ├── analysis.txt
│           └── player_metrics.csv
├── README.md                  # Run overview with suite tables and links
├── latest_* symlink/LATEST.txt# Convenience pointer when using --clean-output
└── comparison_summary/        # Only for compare pipeline: CSV + Markdown ranking tables
```

### CSV Schema

`summary.csv` consolidates all suites/variants (floating-point values are formatted to four decimal places for easier comparison). Key columns:

- `scenario`, `suite`, `variant`, `variant_description`
- `player_type`, `player_instances`
- `avg_score`, `avg_shared_score`, `avg_individual_score`, `avg_involvement_ratio`
- Shared-score components per turn: `importance_per_turn`, `coherence_per_turn`, `freshness_per_turn`, `nonmonotone_per_turn`
- `rounds`, `seed_start`, `length`, `memory_size`, `subjects`
- `average_actual_length`, `average_pauses`
- Optional metadata columns prefixed with `meta_` (mirrors variant `metadata`)

Suites produced by the pipeline builders carry numeric metadata (`target_ratio`, `length`, `player_count`, `memory_size`) enabling the line charts that visualise how each model performs as the hyperparameters change. Suite-level charts plot one line per player (up to six) so comparisons across models remain visible in every sweep.

### Keeping Results Manageable

- Pass `--clean-output` to the CLI (or helper scripts) to delete previous runs in the chosen output directory before launching a new benchmark. This keeps the folder focused on the fresh results and updates the `latest_<scenario>` symlink plus `LATEST.txt` marker.
- Each run emits a `README.md` at the root summarising suites, variants, and direct links to charts/CSVs. Every suite folder also receives a `suite_index.md` so you can open a single Markdown file to inspect all cases and plots without diving into nested folders.

## Creating New Benchmarks

1. **Add or reuse players** via `player_registry.py` (`PlayerRegistry.register`).
2. **Define scenarios** by composing `BenchmarkSuite`/`SimulationVariant` instances (see `sample_scenarios.py`).
   - Each variant specifies player rosters, simulation hyperparameters, number of rounds, base seed, and optional metadata tags.
   - Set `detailed_outputs=True` on a variant for persistent per-round artefacts.
   - Attach metadata values to track hyperparameter sweeps; they appear in CSV columns (`meta_<key>`).
3. **Run the pipeline** using `BenchmarkPipeline` directly or through the CLI.

```python
from benchmarking.pipeline import BenchmarkPipeline
from benchmarking.scenario import BenchmarkScenario, BenchmarkSuite, SimulationVariant, PlayerSpec

scenario = BenchmarkScenario(
    name="Custom Sweep",
    description="Example hyperparameter sweep",
    suites=[
        BenchmarkSuite(
            name="Sweep",
            description="Conversation length sweep",
            focus_player="p_bst_medium",
            variants=[
                SimulationVariant(
                    label="Length_20",
                    players=[PlayerSpec(code="p_bst_medium", count=4)],
                    length=20,
                    memory_size=12,
                    subjects=20,
                    rounds=2,
                    seed=123,
                    metadata={"length": 20},
                ),
                SimulationVariant(
                    label="Length_40",
                    players=[PlayerSpec(code="p_bst_medium", count=4)],
                    length=40,
                    memory_size=12,
                    subjects=20,
                    rounds=2,
                    seed=125,
                    metadata={"length": 40},
                ),
            ],
        )
    ],
)

pipeline = BenchmarkPipeline(scenario)
pipeline.run()
```

## Visualisations

- `player_comparison.png`: column chart ranking players by average score per variant.
- `suite_focus_<suite>.png`: bar chart tracking a focus player (or best performer) across variants in the suite.

Matplotlib is required for plots; if unavailable the pipeline emits a warning and continues without charts.

## Reproducibility

- Every variant fixes a base `seed`; rounds use `seed + round_index`.
- Configuration is saved to `config.json` and `scenario_config.json` for auditability.
- CSV + TXT outputs provide both machine-readable and narrative summaries.

## Extensibility Tips

- Add new suites/variants to `sample_scenarios.py` for reusable bundles.
- Metadata tags (dict on `SimulationVariant`) automatically propagate to CSV columns and textual reports.
- To plug in new models, register them once in `player_registry.py` and reference their code in scenarios.
- Charts automatically adapt to new variants and focus players.

## Maintenance

- Keep runtime manageable by tuning `rounds` and `conversation_length`.
- For quick smoke checks, reduce `rounds` to 1 or shorten conversations.
- For deeper analysis, increase `rounds` or add additional variants.

Happy benchmarking!
