# Final English Presentation

This directory contains the strict 10-page English Slidev deck used for the final presentation. The earlier Chinese deck remains available as `slides.zh.md` for reference.

Live presentation: <https://kscii.github.io/retail_rfm/>

## Rebuild the safe static presentation data

From the project root, rebuild the auditable static demo data when needed:

```bash
uv run retail-rfm export-presentation \
  --csv "resource/Online Retail.csv" \
  --db artifacts/retail_rfm.sqlite \
  --output-dir presentation/public/static-demo
```

The export contains lightweight point IDs, the four centroids, public model evidence, and selected real customer examples. Real CustomerID values are allowed in the presentation; the bulk 3D point cloud remains anonymized simply to keep the public demo focused.

## Start the final presentation locally

```bash
cd presentation
pnpm install --frozen-lockfile
pnpm dev
```

Open `http://localhost:3030/`. Slide 8 uses the same static browser-only explorer as GitHub Pages. It does not need Dash or a local database at presentation time.

## Build final outputs

```bash
pnpm notes
pnpm capture:fallback
pnpm build
pnpm build:pages
pnpm export
```

Outputs:

- `dist/final/`: final browser build;
- `dist/pages/`: GitHub Pages build using the `/retail_rfm/` base path;
- `dist/online-retail-rfm-final.pdf`: strict 10-page PDF;
- `dist/speaker-notes.en.md`: English speaker notes.

The PDF uses the verified static image instead of the interactive iframe. The presentation fallback order is: GitHub Pages, the same local static Slidev build, then PDF.

## Validate locally

With Slidev running:

```bash
pnpm smoke:browser
```

This checks static WebGL, marker sizes, all three 2D slices, Customer 13777, both target viewports, the real-data K-means++ animation, the English title, and absence of remote requests.

## Publish boundary

GitHub Pages may publish source code, selected real CustomerID examples, and the static demo. It must not publish `resource/`, SQLite databases, joblib models, build caches, or `presentation/dist/`. Local visual acceptance and an English timed rehearsal are required before the first commit, push, or Pages deployment.

The repository workflow rebuilds and deploys this directory automatically after each push to `main`.
