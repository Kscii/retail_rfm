# Final English Rehearsal and Timing Sheet

This file is not an extra slide. It is a rehearsal checklist for the strict 10-page final deck.

The speaker notes are the single script to read. The delivery should be calm, structured, and suitable for reading aloud. Numerals on the slides stay exact, while business scale and findings use approximate spoken values. Method settings stay exact. Customer IDs and invoice numbers remain visible evidence but are not read aloud. Keep `S1–S4`, `K-means++`, and `R–F` unchanged.

| Slide | Target | Total | One sentence that must be clear |
|---:|---:|---:|---|
| 1 | 0:25 | 0:25 | The question is whether RFM can reveal meaningful customer groups. |
| 2 | 0:45 | 1:10 | One row is an invoice line, so the data must be aggregated to customers. |
| 3 | 0:45 | 1:55 | RFM is feature engineering; unlabeled clustering has no classification accuracy. |
| 4 | 0:50 | 2:45 | Missing IDs, returns, and long tails make direct clustering unsuitable. |
| 5 | 1:05 | 3:50 | Cancellations adjust Net M, capping deletes nobody, and scaling makes units comparable. |
| 6 | 1:20 | 5:10 | The real-data animation separates K-means++ initialization, assignment, recentering, and convergence. |
| 7 | 1:10 | 6:20 | k=4 balances compactness, separation, stability, size, and meaning. |
| 8 | 1:10 | 7:30 | About ten percent of customers contribute nearly sixty percent of observed Net value. |
| 9 | 0:45 | 8:15 | Clusters are not permanent labels, Net is not profit, and there is no causal result. |
| 10 | 0:45 | 9:00 | Segments create testable questions; actions still need A/B tests. |

## Slide 6: click path

1. Start with all customers in gray and state that calculation uses the full three-dimensional RFM space.
2. Click for C1 and say that the first center is random.
3. Click three times for C2, C3, and C4. Orange is the relative D² initialization weight—not a cluster color—and is clipped only for display.
4. Say: “Farther points receive a higher probability; K-means++ does not simply choose the farthest point.”
5. Pause at iteration 1. Point colors show assignment; hollow diamonds are old centroids; arrows and solid diamonds show recentering.
6. Move quickly through iterations 2–14. Say that outlined customers changed assignment and the number generally falls as the centroids stabilize.
7. Pause at the final iteration: zero assignments changed and the result matches the formal model.
8. Say: “Convergence does not guarantee the global minimum.”

Keep the method settings exact: fifteen iterations, fifty seeds, twenty initializations, and ARI equals one. Do not add `about` to these settings.

## Slide 8: 50-second demo path

1. Point out that the three-dimensional chart uses the real scaled and capped model inputs, and the four diamonds are centroids.
2. Rotate the chart once. Do not use visual separation as proof that the clusters are correct.
3. Open the example customer, but do not read the customer ID. Describe one-day Recency, about thirty purchase invoices, about forty total invoices, and eight cancellations.
4. End with: “This is a real observed customer, not a fictional persona or a response prediction.”

## Slide 10: future validation path

Say the sequence in order: “Update RFM with future transactions, track segment movement, run controlled A/B tests, and measure future behavior.” Mention profit, product-category, and response data only if time allows.

## Short answer anchors

- Frequency: “It counts distinct valid purchase invoices because I want buying occasions, not product rows or units.”
- Net Monetary: “Cancellations do not change Frequency; their negative amounts adjust value in the observed window.”
- Cap: “It limits extreme influence in the model copy, deletes no customers, and keeps raw values for interpretation.”
- K-means++: “It gives farther customers a higher probability of becoming a starting center; the later K-means loop is the same.”
- Greedy K-means++: “Scikit-learn samples several candidates using D² weights and keeps the candidate that best reduces the current potential.”
- k=4: “k=2 separates strongly but is too broad. k=4 gives a useful and stable four-level profile.”
- ARI: “Different starting seeds produced the same assignments here. It does not prove true labels.”
- Business meaning: “The groups support customer-management hypotheses, not guaranteed outcomes.”
