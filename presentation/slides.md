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
【主讲】

This is an unsupervised clustering problem.

First, I group the invoice lines by CustomerID.
Each customer gets one RFM profile.

Recency means days since the last valid purchase.
Frequency counts distinct valid purchase invoices.
Net Monetary adds all signed transaction amounts in this data period.

We do not have true segment labels.
So I cannot calculate classification accuracy.

【本页Q&A，不读】

1. 为什么必须先把invoice lines转换成customer-level RFM？

原始数据的一行只是一个商品行（invoice line），不是一个客户。聚类输入需要每位客户只有一条行为画像（customer-level profile），所以必须按CustomerID聚合。不能把541,909个商品行说成541,909位客户。

2. 为什么Frequency统计不同的invoice，而不是商品行数或购买件数？

Frequency希望表示购买发生的次数（buying occasions）。同一张invoice可以包含多个商品行和很多件商品；如果统计行数或件数，会把一次大量购买误认为多次购买。

3. 为什么Net Monetary使用有符号金额（signed transaction amounts）？

正向购买金额为正，取消或退款金额通常为负。把它们相加，才能描述当前数据期间内观察到的净交易金额（observed Net value）。这不是利润（profit），也不是客户终身价值（customer lifetime value）。

4. 为什么不能计算accuracy？

分类准确率（classification accuracy）需要把预测标签与真实标签（ground-truth labels）比较。本数据没有真实客群标签，所以只能使用内部聚类指标（internal clustering metrics）、稳定性和原始RFM画像评价结果。

不能说：silhouette或ARI是另一种accuracy；它们衡量的是内部结构或两次聚类结果的一致性。
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
【主讲】

This animation uses 4,338 real customer profiles.
The model uses all three scaled and capped RFM features.
Here, I only show R–F.

The first centroid is selected at random.

For each later centroid, K-means++ uses squared distance from the nearest chosen centroid.
Farther customers get a higher probability.
It does not always choose the farthest customer.
Orange is an initialization weight, not a cluster.

After initialization, K-means repeats assignment and update.
Assignment uses the nearest centroid.
Update recalculates each centroid as the cluster mean.
Hollow diamonds are old centroids.
Solid diamonds are updated centroids.

Across 15 iterations, fewer assignments change.
At iteration 15, zero changes means convergence.
It matches the final model.

Convergence does not guarantee the global optimum.
So I compare 50 seeds and use 20 initializations.

【本页Q&A，不读】

1. 普通K-means和K-means++有什么区别？

这里的普通基线使用随机初始化（random initialization）。K-means++只改变初始centroid的选择方式；完成初始化以后，两者都执行相同的assignment和centroid update循环。K-means++通常更稳定，但不能预设它在所有数据上都一定显著更好。

2. K-means++是不是每次都选择最远的点？

不是。后续点被选中的概率与它到最近已有centroid的平方距离（squared distance，D²）有关。距离越远，概率越高，但不是确定选择最远点。页面的橙色只是经过裁切的相对初始化权重（initialization weight），不是cluster颜色或精确概率。

3. 正式模型使用什么距离？能否换成其他距离？

正式K-means使用平方欧氏距离（squared Euclidean distance）。centroid是cluster内各点的均值位置，因此它与欧氏距离的目标函数相匹配。若改成Manhattan distance或其他距离，通常意味着需要改用不同算法，不能仍把它简单称为同一个K-means模型。

4. centroid、assignment和update分别是什么？

centroid是一个cluster在模型空间中的均值位置。assignment把每位客户分配给最近的centroid；update再根据新成员重新计算centroid。不断重复，直到分配不再变化或满足收敛条件（convergence criteria）。

5. 为什么收敛以后还不能说找到global optimum？

K-means可能停在局部最优解（local optimum），结果可能受初始centroid影响。因此实验使用50个固定seeds比较初始化稳定性，最终模型使用20次初始化（n_init=20），降低依赖一次幸运起点的风险。

补充：scikit-learn使用greedy K-means++，会在D²权重下尝试多个候选并选择当前potential更好的候选；这不改变后续K-means循环。

不能说：iteration 15收敛证明cluster是真实标签，或证明模型已经找到唯一正确答案。
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
【主讲】

S1 is long-inactive, and S2 is regular.
S3 is active and high-value.
S4 has the highest Frequency and value.
This gives a clear behavior pattern.

Together, S3 and S4 contain 457 customers.
They are about 10.5 percent of all customers.
But they contribute 58.71 percent of observed Net value.

This 3D chart uses the scaled and capped model inputs.
The diamonds are centroids.
I do not use PCA, because RFM already has three features.

Customer 13777 has Recency 1, Frequency 33, and Net Monetary of 25,748 pounds.
Its 41 invoices include eight cancellations.
This is an observation, not a response prediction.

【本页Q&A，不读】

1. 这四个cluster的实际意义是什么？

它们是在当前观察窗口中，根据RFM距离总结出的探索性行为模式（exploratory behavior patterns）。S1到S4表现出从长期不活跃、常规购买，到近期高价值和最高频高价值的行为阶梯。它们用于总结和筛选客户，不是真实标签或永久身份。

2. 为什么3D图不使用PCA？

正式模型只有R、F、M三个特征，所以3D图可以直接让每个轴对应一个模型特征。图中使用的正是scaled/capped model coordinates，不是原始英镑和订单数。PCA会把三个特征组合成新的主成分，反而降低本项目的直接解释性。

不能说：二维或三维图看起来分得开，所以证明cluster正确。可视化只帮助解释，模型选择还需要inertia、silhouette、ARI、簇规模和原始画像。

3. S4只有51人，是否只是异常值？

51人约占全部客户的1.18%，超过项目预设的1%检查线。S4在原始RFM画像中具有一致的高Frequency和高Net Monetary，而且定向敏感性分析没有显示它完全由重复行、特殊StockCode或地域造成。因此它值得作为顶端行为群体解释，但不能说它是客观存在的真实客户类型。

4. 为什么Customer 13777有41张invoice，但Frequency只有33？

Frequency只统计33张有效正向购买invoice。其余8张是C开头的取消记录（cancellation invoices），不会增加或扣减Frequency，只通过负金额调整Net Monetary。选择13777是因为它接近S4 centroid，适合作为真实代表案例，不是因为它最极端。

5. 这些segments能够直接产生商业价值吗？

它们可以帮助提出客户管理假设（customer-management hypotheses），例如S1唤回、S2促进复购、S3留存和S4高接触服务。但模型没有营销响应数据（response data），不能预测谁一定会回应，也不能证明这些策略会带来利润。实际效果仍需通过A/B tests验证。

不能说：10.5%的客户“创造了58.71%的利润”。正确口径是他们贡献了当前数据中58.71%的observed Net value。
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
