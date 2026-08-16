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
【主讲】

Good morning. I am Xuejian Fang.
This presentation examines whether purchasing behavior can reveal meaningful customer groups.
I represent customer behavior with Recency, Frequency, and Net Monetary.
Next, I use RFM and K-means++ to identify four exploratory patterns.
Finally, I evaluate their stability and interpretation.

【本页Q&A，不读】

1. 为什么研究问题只说meaningful，没有说actionable？

meaningful表示这些客群在RFM行为上有清楚、稳定且可以解释的差异。项目没有营销响应或实验数据，因此不能提前保证分群一定产生可执行效果（actionable outcomes）。

2. 这是不是一个预测项目？

不是。项目使用无监督聚类（unsupervised clustering）总结现有客户行为，不预测未来购买、营销响应或利润。
-->

---

# 2. Dataset — From invoice lines to customers

<p class="lead">UCI Online Retail: real transactions from a UK-based non-store retailer</p>

<DatasetSampleEn />

<p class="source-note">Source: UCI Machine Learning Repository, Online Retail (ID 352)</p>

<!--
【主讲】

First, I describe the dataset.
It contains about half a million invoice lines and about twenty-six thousand invoices across eight fields.
It covers about one year, from late twenty ten to late twenty eleven.

This example shows one customer with two invoices.
A customer may have many invoices, and each invoice may have many lines.

For RFM, I use date, invoice number, quantity, price, and customer ID.
Therefore, each row is an invoice line, not an invoice or customer.

【本页Q&A，不读】

1. 为什么一行不是一张完整invoice？

同一个InvoiceNo会在多行重复，因为每行记录一个商品行（invoice line），包括StockCode、Quantity和UnitPrice。一张invoice可以包含多个商品行，因此不能把CSV行数当作订单数。

2. Customer、Invoice和Product的关系是什么？

对可识别交易而言，一个Customer可以有多张Invoice，每张Invoice属于一个Customer；一张Invoice可以有多个InvoiceLine。若建立完整规范化schema，同一种Product可以出现在多张Invoice中，因此Invoice与Product是通过InvoiceLine形成的多对多关系（many-to-many）。主页面只保留分析所需的Customer 1:N Invoice 1:N InvoiceLine。

3. 为什么StockCode、Description和Country不进入聚类？

正式距离只使用RFM三个客户级数值特征。这些字段用于数据审计、客户背景和敏感性检查。不能说它们不存在或没有价值，只是它们不属于本项目的正式聚类输入。
-->

---

# 3. Problem formulation — Unsupervised segmentation

<p class="lead">Turn the transaction table into one behavior profile per customer, then find similar groups</p>

<RfmFlow />

<!--
【主讲】

Next, I define the analysis problem.
This is an unsupervised clustering problem.

First, I group invoice lines by customer ID to create one RFM profile per customer.
Recency means days since the last valid purchase.
Frequency counts distinct valid purchase invoices.
Net Monetary adds signed transaction amounts within the observed period.

Without ground-truth segment labels, I cannot calculate classification accuracy.

【本页Q&A，不读】

1. 为什么必须先把invoice lines转换成customer-level RFM？

原始数据的一行只是一个商品行（invoice line），不是一个客户。聚类输入需要每位客户只有一条行为画像（customer-level profile），所以必须按CustomerID聚合。不能把541,909个商品行说成541,909位客户。

2. 为什么Frequency统计不同的invoice，而不是商品行数或购买件数？

Frequency希望表示购买发生的次数（buying occasions）。同一张invoice可以包含多个商品行和很多件商品；如果统计行数或件数，会把一次大量购买误认为多次购买。

3. 为什么Net Monetary使用有符号金额，以及为什么不能计算accuracy？

正向购买金额为正，取消或退款金额通常为负。把它们相加，才能描述当前数据期间内观察到的净交易金额（observed Net value）。这不是利润（profit），也不是客户终身价值（customer lifetime value）。
分类准确率（classification accuracy）需要把预测标签与真实标签（ground-truth labels）比较。本数据没有真实客群标签，所以只能使用内部聚类指标（internal clustering metrics）、稳定性和原始RFM画像评价结果。

不能说：silhouette或ARI是另一种accuracy；它们衡量的是内部结构或两次聚类结果的一致性。
-->

---

# 4. EDA — Three data issues we cannot ignore

<p class="lead">First understand what happened in the data; then choose the processing rules</p>

<EdaTriptychEn />

<!--
【主讲】

Before modelling, I examine three data issues.

First, about one quarter of lines lack customer ID, so they cannot form customer profiles.

Second, returns can change the value story.
This customer's Gross value is about one hundred and seventy thousand pounds, but Net value is about three pounds.
Gross would incorrectly suggest high value.

Third, Frequency and Net Monetary have long tails, so extremes may dominate distances and centroids.

【本页Q&A，不读】

1. 缺失CustomerID的交易是否应该删除？

它们仍是真实交易，也保留在原始数据审计中；但无法可靠聚合到某位客户，所以不能进入customer-level RFM。不能说这些交易无效，只能说它们不适合本项目的客户分群单位。

2. Gross与Net案例说明了什么？长尾为什么重要？

该客户的Gross金额很高，但几乎全部被负向交易抵消。只使用Gross会制造虚假的高价值画像。与此同时，F和M的长尾会让少数极端客户强烈影响欧氏距离和centroid，因此需要比较变换和截尾方案。
-->

---

# 5. Preprocessing — An interpretable Net RFM

<p class="lead">Cleaning rules, return accounting, and model inputs must be explained separately</p>

<PreprocessingFlow />

<!--
【主讲】

Based on these issues, I preprocess the data.

First, I remove about five thousand three hundred extra exact duplicate copies.
Next, I retain about four hundred thousand known-customer signed lines and obtain about four thousand three hundred profiles.

A cancellation does not change Frequency; its negative amount only adjusts Net Monetary.
For example, a fully cancelled one-hundred-pound purchase has Frequency one and Net Monetary zero.

Then, I apply the ninety-nine-point-five percentile cap to a model copy.
It affects about thirty customers but removes nobody.
Finally, StandardScaler makes the feature scales comparable.

【本页Q&A，不读】

1. 为什么删除exact duplicates？

这里删除的是所有字段完全相同的额外副本（exact duplicate copies），避免同一商品行被重复计入金额和订单画像。没有按部分字段盲目去重，原始CSV也保持只读。

2. 取消订单如何影响R、F和Net M？

R和F只由有效正向购买定义，因此C开头的取消invoice不会增加或扣减Frequency。它的有符号负金额会调整同一客户观察窗口内的Net Monetary。负净额只代表当前窗口内净额为负，不代表完整历史中退款超过全部付款。

3. cap和StandardScaler分别解决什么问题？

99.5%上端截尾只限制模型副本中的极端F和M，不删除客户，原始值仍用于画像。StandardScaler让R、F、M的数值尺度可比较，但不保证三项业务权重绝对相同，也不会把结果统一映射到零到一。
-->

---

# 6. Methods — K-means++ on the actual RFM data

<p class="lead">The model calculates in three dimensions; this page shows an R–F view of the same 4,338 customers</p>

<KMeansRealData />

<!--
【主讲】

After preprocessing, I apply K-means++ clustering.
The model uses scaled and capped RFM in three dimensions; this page shows R–F.

First, it selects one centroid at random.
Next, K-means++ gives farther customers a higher probability based on squared distance.
Orange is an initialization weight, not a cluster.

After initialization, K-means repeats assignment and update.
It selects the nearest centroid, then recalculates each cluster mean.
Hollow diamonds are old centroids; solid diamonds are updated centroids.

After fifteen iterations, zero changes indicate convergence.
However, convergence does not guarantee the global optimum.
Therefore, I compare fifty seeds and use twenty initializations in the final model.

【本页Q&A，不读】

1. 普通K-means和K-means++有什么区别？

这里的普通基线使用随机初始化（random initialization）。K-means++只改变初始centroid的选择方式；完成初始化以后，两者都执行相同的assignment和centroid update循环。K-means++通常更稳定，但不能预设它在所有数据上都一定显著更好。

2. K-means++是不是每次都选择最远的点？

不是。后续点被选中的概率与它到最近已有centroid的平方距离（squared distance，D²）有关。距离越远，概率越高，但不是确定选择最远点。页面的橙色只是经过裁切的相对初始化权重（initialization weight），不是cluster颜色或精确概率。

3. 正式模型使用什么距离？能否换成其他距离？

正式K-means使用平方欧氏距离（squared Euclidean distance）。centroid是cluster内各点的均值位置，因此它与欧氏距离的目标函数相匹配。若改成Manhattan distance或其他距离，通常意味着需要改用不同算法，不能仍把它简单称为同一个K-means模型。

4. centroid、assignment和update分别是什么？为什么收敛后还要比较多个seeds？

centroid是一个cluster在模型空间中的均值位置。assignment把每位客户分配给最近的centroid；update再根据新成员重新计算centroid。不断重复，直到分配不再变化或满足收敛条件（convergence criteria）。
K-means可能停在局部最优解（local optimum），结果可能受初始centroid影响。因此实验使用50个固定seeds比较初始化稳定性，最终模型使用20次初始化（n_init=20），降低依赖一次幸运起点的风险。

补充：scikit-learn使用greedy K-means++，会在D²权重下尝试多个候选并选择当前potential更好的候选；这不改变后续K-means循环。

不能说：iteration 15收敛证明cluster是真实标签，或证明模型已经找到唯一正确答案。
-->

---

# 7. Evaluation — Why choose k = 4?

<p class="lead">No single score can choose the number of customer groups; the evidence must be read together</p>

<KEvidenceGrid />

<!--
【主讲】

To select k, I compare four types of evidence.

First, inertia bends near k equals four.
Second, silhouette peaks at k equals two, but this split is too broad.
At k equals four, it remains about zero point five six.

Third, median pairwise ARI equals one across fifty seeds.
Finally, the smallest group is just above one percent.

Together, k equals four balances separation, stability, size, and clear profiles.
However, these measures are not accuracy, and k equals four is not the only possible truth.

【本页Q&A，不读】

1. inertia和elbow分别表示什么？

inertia是每个点到所属centroid的平方距离总和，越小表示簇内更紧密。随着k增加，inertia必然下降；elbow关注下降速度何时明显变缓，而不是机械选择最小inertia。

2. silhouette在k=2最高，为什么选择k=4？

silhouette比较点与本簇的紧密程度和与最近其他簇的分离程度。k=2虽然分数最高，但只形成“多数客户与高价值客户”的宽泛切分。k=4仍有较强silhouette，并提供更有区分度的稳定画像，因此综合证据选择k=4。

3. median pairwise ARI为1说明什么？

ARI比较不同运行的客户分配是否一致，并校正随机一致。中位数为1表示这50个起点在该设置下得到相同分配，说明初始化稳定；它不表示与真实标签完全一致，也不是accuracy。

4. 最小簇只有1.18%，是否说明k=4错误？

1%只是预先设定的检查线，不是自动淘汰规则。该簇仍有51位客户且画像一致。k=4是基于当前数据和口径的实用选择，不是唯一客观真值。
-->

---

# 8. Findings — Four customer behavior patterns

<FindingsDemo />

<!--
【主讲】

Based on this evidence, I obtain four customer profiles.
They range from long-inactive S1 to top-frequency high-value S4.

Together, S3 and S4 contain about four hundred and sixty customers: about ten percent, contributing nearly sixty percent of observed Net value.

This three-dimensional chart uses scaled and capped inputs; diamonds show centroids.
I keep one axis for each RFM feature, without PCA.

The example near S4 has one-day Recency and about thirty purchase invoices.
It has about forty invoices, including eight cancellations.
This observation is not a response prediction.

【本页Q&A，不读】

1. 这四个cluster的实际意义是什么？S4只有51人是否只是异常值？

它们是在当前观察窗口中，根据RFM距离总结出的探索性行为模式（exploratory behavior patterns）。S1到S4表现出从长期不活跃、常规购买，到近期高价值和最高频高价值的行为阶梯。它们用于总结和筛选客户，不是真实标签或永久身份。
51人约占全部客户的1.18%，超过项目预设的1%检查线。S4在原始RFM画像中具有一致的高Frequency和高Net Monetary，而且定向敏感性分析没有显示它完全由重复行、特殊StockCode或地域造成。因此它值得作为顶端行为群体解释，但不能说它是客观存在的真实客户类型。

2. 为什么3D图不使用PCA？

正式模型只有R、F、M三个特征，所以3D图可以直接让每个轴对应一个模型特征。图中使用的正是scaled/capped model coordinates，不是原始英镑和订单数。PCA会把三个特征组合成新的主成分，反而降低本项目的直接解释性。

不能说：二维或三维图看起来分得开，所以证明cluster正确。可视化只帮助解释，模型选择还需要inertia、silhouette、ARI、簇规模和原始画像。

3. 为什么Customer 13777有41张invoice，但Frequency只有33？

Frequency只统计33张有效正向购买invoice。其余8张是C开头的取消记录（cancellation invoices），不会增加或扣减Frequency，只通过负金额调整Net Monetary。选择13777是因为它接近S4 centroid，适合作为真实代表案例，不是因为它最极端。

4. 这些segments能够直接产生商业价值吗？

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
【主讲】

However, the result has three important boundaries.

First, the data covers known customers for about one year; some returns may refer to earlier purchases.

Second, the model has no ground-truth labels.
Results depend on k, scaling, and capping; the cap compresses top differences.

Third, observed Net value is not profit or customer lifetime value.
The clusters neither predict response nor prove causality.
Therefore, they are exploratory patterns, not permanent identities.

【本页Q&A，不读】

1. 这些数据限制会怎样影响解释？

未知CustomerID无法进入客户级分析；约一年的观察窗口可能遗漏更早购买；部分退货可能对应窗口开始前的订单。因此结果描述的是当前可观察数据，不是客户的完整历史。

2. 模型和业务限制的核心边界是什么？

cluster会随k、缩放和截尾口径变化，也没有真实标签证明其唯一正确。Net value不是利润或CLV，客群与价值的关联也不证明某项营销措施会造成结果（causality）。不能把segment直接当作永久身份或响应预测。
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
【主讲】

Finally, I return to the research question.
RFM reveals four stable, meaningful exploratory behavior patterns.

About ten percent of customers contribute nearly sixty percent of observed Net value, but the segments do not predict response.

They support tests: reactivate S1, encourage S2, retain S3, and protect S4.

Next, I would update RFM, track segment movement, run controlled A/B tests, and measure future behavior.

Future evidence must validate actions.
Thank you.

【本页Q&A，不读】

1. 为什么可以说meaningful和stable？

meaningful来自四群在原始RFM画像上的清楚行为差异；stable主要指固定预处理和k=4时，对不同初始化的结果一致，并且定向敏感性没有破坏主要画像。不能把stable解释为这些群体永远不变或是真实标签。

2. 为什么未来工作需要A/B tests和额外数据？

当前分群只能提出策略假设。A/B tests用于比较措施是否真正改变复购、留存或未来Net value；利润、商品类别和响应数据可以让决策目标更接近实际业务。没有实验前不能声称分群造成收益。
-->
