# Source package

`src` contains reusable, side-effect-free project modules. Root `main.py` is
the only executable entry point and orchestrates every stage.

- `analysis/`: dataset audit, missing-data, post-corona, and structural-break analysis.
- `cleaning/`: DataFrame cleaning and schema harmonization functions.
- `models/`: demographic summaries and engagement-model functions.
- `visualization/`: functions that save figures supplied by the orchestrator.
