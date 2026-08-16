---
theme: default
title: Online Retail Customer Segmentation
info: |
  DS431 Final Project — Online Retail customer segmentation
author: Xuejian Fang
aspectRatio: 16/9
canvasWidth: 980
colorSchema: light
class: cover-slide
download: false
favicon: /favicon.svg
fonts:
  sans: Noto Sans
  mono: Noto Sans Mono
  local: Noto Sans, Noto Sans Mono
  provider: none
---

<div class="cover-shell">
  <div>
    <p class="cover-kicker">DS431 Final Project</p>
    <h1 class="cover-title">Online Retail Customer Segmentation</h1>
    <p class="cover-subtitle">RFM + K-means++ based on purchasing behavior</p>
    <div class="research-question"><b>Research question</b><br>Can customers be grouped into meaningful segments based on their recency, frequency, and monetary value?</div>
  </div>
  <div class="cover-meta">
    <div><strong>Xuejian Fang</strong>Presenter</div>
    <div><strong>Professor Osman Yagan</strong>Project supervision</div>
    <div><strong>DS431 · 17 August 2026</strong>Final presentation</div>
  </div>
</div>

<!--
Good morning. I am Xuejian Fang. This project asks a simple question. If we only use how recently a customer bought, how often they bought, and their observed monetary value, can we find meaningful customer groups? I will move from invoice data to RFM features, K-means++, model evaluation, and four final behavior patterns.
-->

---

# 2. Dataset — From invoice lines to customers

<p class="lead">UCI Online Retail: real transactions from a UK-based non-store retailer</p>

<DatasetSampleEn />

<p class="source-note">Source: UCI Machine Learning Repository, Online Retail (ID 352)</p>

<!--
The dataset has 541,909 rows, eight fields, and 25,900 different invoice numbers. It covers December 2010 to December 2011. Here are two real invoices from Customer 17850. Invoice 536365 has seven product lines, while 536366 has two. All eight source fields are shown. InvoiceDate creates Recency; distinct InvoiceNo creates Frequency; and Quantity times UnitPrice creates Net Monetary. CustomerID is the aggregation key. StockCode, Description, and Country support auditing and context, but they are not clustering features. One row is an invoice line, not a complete order or a customer.
-->

---

# 3. Problem formulation — Unsupervised segmentation

<p class="lead">Turn the transaction table into one behavior profile per customer, then find similar groups</p>

<RfmFlow />

<!--
I define this as customer-level unsupervised clustering. Recency is the number of days since the customer's last valid purchase. Frequency is the number of distinct valid purchase invoices, not the number of product rows or units. Net Monetary is the sum of all signed transaction amounts in the observation window. Each customer becomes one RFM profile. There are no known segment labels, so classification accuracy cannot be calculated.
-->

---

# 4. EDA — Three data issues we cannot ignore

<p class="lead">First understand what happened in the data; then choose the processing rules</p>

<EdaTriptychEn />

<!--
EDA shows three main issues. First, 24.93 percent of invoice lines have no CustomerID, so they cannot be linked to a customer profile. Second, returns can completely change the value story. Customer 16446 has more than 168 thousand pounds in positive purchases, but only 2 pounds 90 in Net value. Gross value would create a false high-value customer. Third, Frequency and Net Monetary have long right tails, so a few extreme values may dominate distances and centroids.
-->

---

# 5. Preprocessing — An interpretable Net RFM

<p class="lead">Cleaning rules, return accounting, and model inputs must be explained separately</p>

<PreprocessingFlow />

<!--
I first remove 5,268 extra exact duplicate rows. This leaves 536,641 rows. I keep 401,604 signed transaction lines with a known CustomerID. Among them, 392,692 valid positive purchase lines define Recency and Frequency. The final analysis has 4,338 customers. A cancellation does not increase or reduce Frequency. It only adjusts Net Monetary with its negative amount. For example, a 100-pound purchase with a full cancellation gives Frequency one and Net Monetary zero. I cap only the model copy of Frequency and Net Monetary at the 99.5th percentile. This affects 29 customers but deletes nobody. StandardScaler then makes the three feature scales comparable.
-->

---

# 6. Methods — K-means++ on the actual RFM data

<p class="lead">The model calculates in three dimensions; this page shows an R–F view of the same 4,338 customers</p>

<KMeansRealData />

<!--
This animation uses the actual 4,338 customer profiles, not artificial groups. The calculation always uses all three scaled and capped RFM features; the slide only displays Recency and Frequency. The first center is selected at random. For each later center, orange intensity shows the squared distance from the nearest chosen center. This orange is an initialization weight, not a cluster color. Farther customers receive a higher probability, but the method does not simply choose the farthest point. After four starting centers, each graph shows one complete K-means iteration. Customer colors show the assignment, hollow diamonds show the old centroids, arrows show movement, and solid diamonds show the recalculated means. I will move quickly through all 15 iterations. The number of changed assignments generally becomes smaller, reaching zero at iteration 15. The result matches the final model assignment. Scikit-learn uses a greedy K-means++ implementation that evaluates several weighted candidates; this detail does not change the later K-means loop. Convergence still does not prove a global optimum, so I also compare 50 seeds and use 20 initializations for the final model.
-->

---

# 7. Evaluation — Why choose k = 4?

<p class="lead">No single score can choose the number of customer groups; the evidence must be read together</p>

<KEvidenceGrid />

<!--
I use four types of evidence. Inertia falls quickly before k equals 4, then the improvement becomes smaller. Silhouette is highest at k equals 2, but that solution gives only a broad split between most customers and high-value customers. At k equals 4, silhouette is still strong at 0.563. Median pairwise ARI is 1, so the 50 different starts give the same customer assignment. The smallest group is 1.18 percent, still above my one-percent check line. Therefore, k equals 4 is a practical balance of compactness, separation, stability, size, and clear profiles. These internal scores are not accuracy, and k equals 4 is not the only possible truth.
-->

---

# 8. Findings — Four customer behavior patterns

<FindingsDemo />

<!--
The four groups form a clear behavior ladder. S1 customers have been inactive for a long time and have low Frequency and Net value. S2 contains most regular customers. S3 customers are recent, repeat buyers with higher value. S4 customers buy most often and have the highest value. Together, S3 and S4 contain 457 customers, about 10.5 percent of all customers, but contribute 58.71 percent of observed Net value.

Now I will use the small window for a short demo. This is the static, browser-based version that also runs on GitHub Pages. I rotate the 3D chart once. Its three axes are the actual scaled and capped model inputs, and the diamonds are centroids. I do not use PCA because RFM already has three features, so each axis keeps its original role. Then I open Customer 13777. This real customer has Recency 1 day, Frequency 33, and Net Monetary of 25,748 pounds. The timeline contains 41 recorded invoices, including eight cancellations. This connects the segment back to real transactions, but it does not predict marketing success.
-->

---

# 9. Limitations — Boundaries of the result

<div class="plain-grid-3">
  <article class="plain-panel limitation-panel">
    <p class="eyebrow">Data</p><h2>Data limits</h2>
    <ul><li>Only customers with a known CustomerID</li><li>About one year of observations</li><li>Some returns may relate to earlier purchases</li><li>No demographics, channel, profit, or response data</li></ul>
  </article>
  <article class="plain-panel limitation-panel">
    <p class="eyebrow">Model</p><h2>Model limits</h2>
    <ul><li>No ground-truth segment labels</li><li>K-means prefers compact, distance-based groups</li><li>Results depend on k, scaling, and capping</li><li>The cap compresses differences at the top</li></ul>
  </article>
  <article class="plain-panel limitation-panel">
    <p class="eyebrow">Business</p><h2>Business limits</h2>
    <ul><li>Net value is not profit or CLV</li><li>Clusters do not predict customer response</li><li>Value concentration does not prove causality</li><li>Strategies still need experiments</li></ul>
  </article>
</div>

<div class="warning-strip"><b>Interpretation boundary:</b> these are stable exploratory behavior patterns in this dataset—not permanent customer identities or proven treatment effects.</div>

<!--
The result has three boundaries. For the data, I can only analyze customers with an ID, and the window is about one year. Some returns may also refer to purchases before the window. For the model, there are no true labels, and the result depends on k, scaling, and capping. Capping also compresses differences among the highest customers. For business use, Net value is not profit or customer lifetime value, and a cluster does not predict response. These groups are exploratory behavior patterns, not permanent identities or proven marketing rules.
-->

---

# 10. Conclusion — From segments to testable questions

<div class="conclusion-grid">
  <article><b>01</b><strong>Four stable exploratory groups</strong><span>Behavior patterns, not permanent identities</span></article>
  <article><b>02</b><strong>about 10.5% → 58.71%</strong><span>Customers → observed Net value</span></article>
  <article><b>03</b><strong>Segments do not predict response</strong><span>Business actions still require evidence</span></article>
</div>

<div class="behavior-strip"><span style="--segment:var(--s1)"><b>S1</b> reactivate</span><span style="--segment:var(--s2)"><b>S2</b> repeat</span><span style="--segment:var(--s3)"><b>S3</b> retain</span><span style="--segment:var(--s4)"><b>S4</b> protect</span></div>

<div class="future-title">Future validation</div>
<div class="future-flow"><span>Update RFM with<br><b>future transactions</b></span><i>→</i><span>Track<br><b>segment movement</b></span><i>→</i><span>Run controlled<br><b>A/B tests</b></span><i>→</i><span>Measure<br><b>future behavior</b></span></div>

<p class="closing-line">The segments support better questions; future data must validate the actions.</p>

<!--
The answer to my research question is yes. RFM reveals four meaningful and stable exploratory behavior patterns in this dataset. About 10.5 percent of customers contribute 58.71 percent of observed Net value. But the segments do not predict response. They create testable hypotheses: reactivate S1, encourage repeat buying in S2, retain S3, and protect S4. Next, I would update RFM with future transactions, track movement between groups, run controlled A/B tests, and measure future behavior. With extra profit, product-category, and response data, the decisions could become more specific. The segments support better questions; future evidence must validate the actions. Thank you.
-->
