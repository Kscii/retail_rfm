# Retail RFM

Reproducible UCI Online Retail customer segmentation and a localhost Dash decision-support prototype.

## Run

```bash
uv sync --locked
uv run retail-rfm build
uv run retail-rfm verify
uv run retail-rfm dashboard
```

Open <http://127.0.0.1:8050/?tab=overview>.

The optional full evidence audit reruns 1,600 single-initialization K-means fits with full-population silhouette:

```bash
uv run retail-rfm verify --deep
```

Generated SQLite, joblib and manifest files are written to `artifacts/`. The source CSV is read-only and is never modified.

## Project boundaries

- RFM and clustering summarize observed purchasing behavior.
- Segment names are descriptive, not ground-truth customer labels.
- Strategy cards are hypotheses for future controlled tests, not predicted treatment effects.
- Observed Net value is not profit.

## Final presentation

The strict 10-page English Slidev deck and its static explorer are in [`presentation/`](presentation/README.md). Build the GitHub Pages variant with:

- Live presentation: <https://kscii.github.io/retail_rfm/>
- Deployment workflow: [`.github/workflows/pages.yml`](.github/workflows/pages.yml)

```bash
cd presentation
pnpm install --frozen-lockfile
pnpm build:pages
```

Every push to `main` automatically rebuilds and redeploys the presentation through GitHub Actions.

Local course resources, exploratory reports, SQLite databases, and model artifacts are deliberately excluded from the public repository.
