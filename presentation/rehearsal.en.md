# Final English Rehearsal and Timing Sheet

This file is not an extra slide. It is a rehearsal checklist for the strict 10-page final deck.

The speaker notes are the single script to read. The delivery should be calm, structured, and suitable for reading aloud. Numerals on the slides stay exact, while business scale and findings use approximate spoken values. Method settings stay exact. Customer IDs and invoice numbers remain visible evidence but are not read aloud. Keep `S1–S4`, `K-means++`, and `R–F` unchanged. This shortened version leaves detailed evidence in the slides and Q&A so the spoken delivery can stay within the course limit.

| Slide | Target | Total | One sentence that must be clear |
|---:|---:|---:|---|
| 1 | 0:25 | 0:25 | The question is whether RFM can reveal meaningful customer groups. |
| 2 | 0:55 | 1:20 | One row is an invoice line, so the data must be aggregated to customers. |
| 3 | 0:45 | 2:05 | RFM is feature engineering; unlabeled clustering has no classification accuracy. |
| 4 | 0:50 | 2:55 | Missing IDs, cancellations, and long tails make direct clustering unsuitable. |
| 5 | 0:55 | 3:50 | The cancellation example explains Net M; capping deletes nobody; scaling makes units comparable. |
| 6 | 1:30 | 5:20 | The real-data animation separates K-means++ initialization, assignment, recentering, and convergence. |
| 7 | 0:55 | 6:15 | Four evaluation measures together support k=4 over a broad k=2 split. |
| 8 | 1:50 | 8:05 | Four behavior profiles support four possible management strategies. |
| 9 | 1:00 | 9:05 | A longer observation window and within-segment A/B tests address different limitations. |
| 10 | 0:05 | 9:10 | Thank the audience and move to Q&A. |

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

## Slide 8: findings and short demo path

1. Explain S1–S4 in order using behavior first and the `Possible strategy:` line second; do not read every exact median.
2. State the concentration finding using `about ten percent` and `nearly sixty percent`.
3. Point out that the three-dimensional chart uses the same scaled and capped RFM inputs.
4. Rotate once, then open the example customer and describe it only as one real customer close to the S4 centroid.

## Slide 9: future validation

Distinguish temporal validation from business validation. Expanding the observation window and tracking movement checks whether profiles remain useful over time. A/B tests must randomize treatment and control within the same segment before comparing future purchase or retention.

## Slide 10: closing

Say only “Thank you.” The slide is the visual background for Q&A, not another content page.

## Short answer anchors

- Frequency: “It counts distinct valid purchase invoices because I want buying occasions, not product rows or units.”
- Net Monetary: “Cancellations do not change Frequency; their negative amounts adjust value in the observed window.”
- Cap: “It limits extreme influence in the model copy, deletes no customers, and keeps raw values for interpretation.”
- K-means++: “It gives farther customers a higher probability of becoming a starting center; the later K-means loop is the same.”
- Greedy K-means++: “Scikit-learn samples several candidates using D² weights and keeps the candidate that best reduces the current potential.”
- k=4: “k=2 separates about ninety-six percent from a high-value four percent, so it is too broad. k=4 gives a useful four-level profile.”
- ARI: “Different starting seeds produced the same assignments here. It does not prove true labels.”
- Business meaning: “The groups support customer-management hypotheses, not guaranteed outcomes.”
