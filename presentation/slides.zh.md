---
theme: default
title: 基于购买行为的在线零售客户分群
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
  sans: Noto Sans CJK SC
  mono: Noto Sans Mono
  local: Noto Sans CJK SC, Noto Sans, Noto Sans Mono
  provider: none
---

<div class="cover-shell">
  <div>
    <p class="cover-kicker">DS431 Final Project</p>
    <h1 class="cover-title">基于购买行为的<br>在线零售客户分群</h1>
    <p class="cover-subtitle">RFM feature engineering + K-means++ clustering</p>
    <div class="research-question"><b>Research question</b><br>Can customers be grouped into meaningful segments based on their recency, frequency, and monetary value?</div>
  </div>
  <div class="cover-meta">
    <div><strong>Xuejian Fang</strong>Presenter</div>
    <div><strong>DS431</strong>Professor Osman Yagan</div>
    <div><strong>17 August 2026</strong>Final presentation</div>
  </div>
</div>

<!--
大家好，我是 Xuejian Fang。这个项目研究一个简单的问题：如果我们只观察客户最近多久购买、购买多少次，以及观察窗口内的净交易金额，能不能把客户分成有意义的行为群体？我会从原始交易数据开始，介绍 RFM、K-means++、模型选择，最后展示四个客群和它们能支持什么样的业务问题。
-->

---

# 2. Dataset — 从 invoice lines 到客户

<p class="lead">UCI Online Retail：一家英国非实体零售商的真实交易记录</p>

<DatasetSample />

<p class="source-note">Source: UCI Machine Learning Repository, Online Retail (ID 352)</p>

<!--
数据来自 UCI Online Retail，共 541,909 行、8 个字段和 25,900 个不同的 InvoiceNo，覆盖 2010 年 12 月到 2011 年 12 月。这里最重要的数据单位是 invoice line。左边三行都属于同一张 invoice 536365，但每行是不同商品。因此一行不是一个完整订单，更不是一个客户。我的分析必须先把商品行聚合成订单，再聚合成客户级特征。
-->

---

# 3. Problem formulation — 无监督客户分群

<p class="lead">把交易表转换成每位客户的一条行为描述，再寻找相似群体</p>

<RfmFlow />

<!--
我把问题定义为客户级无监督聚类。R 是 Recency：以 2011 年 12 月 10 日为参考日，距离最后一次有效购买经过多少天。F 是 Frequency：有效正向购买中不重复的 invoice 数，而不是商品行数。M 使用 Net Monetary：同一观察窗口内所有有符号交易金额之和。最后每位客户只有一条 RFM 记录，再由模型分群。因为没有真实客群标签，所以没有 classification accuracy；后面使用内部结构、稳定性、簇规模和业务语义来评价。
-->

---

# 4. EDA — 三个不能忽略的数据问题

<p class="lead">先说明数据中发生了什么，再决定如何处理</p>

<EdaTriptych />

<!--
EDA 给出三个主要问题。第一，24.93% 的商品行缺少 CustomerID，无法可靠归到某位客户。第二，取消和退款会改变客户价值的解释。客户 16446 的正向购买总额超过 16.8 万英镑，但加入取消记录后净额只有 2.90 英镑；只看 Gross 会把他误认为大客户。第三，Frequency 和 Net Monetary 都有很长的右尾，少数极端值可能主导距离和 centroid。这一页只展示数据事实，下一页才说明处理规则。
-->

---

# 5. Preprocessing — 可解释的 Net RFM

<p class="lead">清洗规则、退款口径与模型输入必须分开说明</p>

<PreprocessingFlow />

<!--
我先删除 5,268 个完全重复的额外副本，保留 536,641 行。只有能识别 CustomerID 的 401,604 条有符号交易进入客户分析，其中 392,692 条有效正向购买用于计算 R 和 F，最终得到 4,338 位至少购买过一次的客户。取消 invoice 不增加也不扣减 Frequency，只通过负金额调整 Net M。例如一张 100 英镑购买被完全退款，F 仍是 1，Net M 是 0。为了限制长尾对 centroid 的影响，我只在模型输入副本上把 F 和 Net M 的上端限制到 99.5% 分位；29 位客户受到影响，但没有客户被删除，原始值仍用于画像。最后 StandardScaler 让三个特征的数值尺度可以比较。
-->

---

# 6. Methods — K-means++ 只改进初始化

<p class="lead">受控随机基线说明初始化问题；主方法保持同一套 K-means 迭代</p>

<KMeansInit />

<!--
普通 K-means 的随机初始化是我的简单基线。随机中心可能一开始靠得很近。K-means++ 的区别只在初始化：第一个中心随机选择，后续中心更可能从距离已有中心较远的点中抽到，所以起点通常更分散。初始化完成后，两者都执行相同循环：把客户分给最近的 centroid，再把 centroid 更新为簇内均值，直到稳定。它仍然可能得到局部最优，不保证全局最优。我比较 k 等于 2 到 8，并用相同的 50 个种子检查稳定性；最终模型运行 20 次初始化。
-->

---

# 7. Evaluation — 为什么选择 k = 4？

<p class="lead">没有一个分数可以单独决定客户群数；证据需要组合阅读</p>

<KEvidenceGrid />

<!--
我从四个方面选择 k。左上 inertia 在 k 等于 4 前下降较快，之后边际改善变小。右上 silhouette 中 k 等于 2 最高，但它主要给出“多数客户对高价值客户”的粗分。k 等于 4 的 silhouette 是 0.563，仍然清晰。左下 median pairwise ARI 在 k 等于 4 是 1，说明 50 个不同初始化得到完全一致的客户划分。右下最小簇为 1.18%，仍高于我的 1%检查线；从 k 等于 5 开始，小簇低于 1%。所以 k 等于 4 是分离、稳定、规模和语义之间的折中，不是唯一真实答案。这些指标也不是 accuracy。
-->

---

# 8. Findings — 四种行为模式与价值集中

<FindingsDemo />

<!--
最终四群形成清晰的行为阶梯。S1 很久没有购买，频率和净额都低；S2 是占多数的常规客户；S3 最近、重复购买并具有较高净额；S4 的购买最频繁、净额最高。S3 和 S4 合计 457 人，大约占客户 10.5%，却贡献观察到的 Net value 的 58.71%。

接下来我用右边的小窗做一分钟以内演示。先旋转一次 3D 图；这里三个轴是模型真正使用的 scaled 和 capped RFM，菱形是 centroid。然后打开 Customer 13777。他接近 S4 centroid，原始 R 是 1 天、F 是 33 张有效购买、Net M 是 25,748.35 英镑。时间线有 41 张记录 invoice，其中 8 张是 C 开头取消。这个例子说明分群能连接回真实交易，但它不是 persona，也不预测营销成功。
-->

---

# 9. Limitations — 聚类结果的边界

<div class="plain-grid-3">
  <article class="plain-panel limitation-panel">
    <p class="eyebrow">Data</p><h2>数据限制</h2>
    <ul><li>只覆盖可识别 CustomerID</li><li>约一年的观察窗口</li><li>窗口前购买可能对应窗口内退款</li><li>缺少人口、渠道、利润和营销响应</li></ul>
  </article>
  <article class="plain-panel limitation-panel">
    <p class="eyebrow">Model</p><h2>模型限制</h2>
    <ul><li>没有真实客群标签</li><li>K-means 偏好 distance-based、较紧凑的群</li><li>结果依赖 k、scaling 与 capping</li><li>cap 压缩顶端客户之间的差异</li></ul>
  </article>
  <article class="plain-panel limitation-panel">
    <p class="eyebrow">Business</p><h2>业务限制</h2>
    <ul><li>Net value 不是利润或 CLV</li><li>cluster 不预测客户是否响应</li><li>价值集中不证明因果效果</li><li>策略建议必须由实验验证</li></ul>
  </article>
</div>

<div class="warning-strip"><b>Interpretation boundary:</b> these are stable exploratory behavior patterns in this dataset—not permanent customer identities or proven treatment effects.</div>

<!--
这个结果有三类边界。数据方面，只能分析有 CustomerID 的客户，而且窗口只有约一年；窗口内的退款也可能对应更早的购买。模型方面，没有真实标签，K-means 的结果依赖 k、缩放和截尾；截尾还会压缩最顶端客户内部的差异。业务方面，Net value 不是利润，也不是 customer lifetime value；cluster 不会预测客户对活动的响应。因此这些群是当前数据中的稳定探索性行为模式，不是永久身份，更不是已经证明有效的营销规则。
-->

---

# 10. Conclusion — 从分群到可检验问题

<div class="answer-line">RFM revealed four meaningful and stable exploratory behavior patterns.</div>

<div class="strategy-grid">
  <article class="strategy-card" style="--segment:var(--s1)"><strong>S1</strong><h2>Long-inactive</h2><p>测试低成本唤回信息，而不是默认大规模优惠。</p></article>
  <article class="strategy-card" style="--segment:var(--s2)"><strong>S2</strong><h2>Regular</h2><p>测试复购提醒或商品组合，关注重复购买。</p></article>
  <article class="strategy-card" style="--segment:var(--s3)"><strong>S3</strong><h2>Active high-value</h2><p>测试忠诚度和留存方案，衡量增量行为。</p></article>
  <article class="strategy-card" style="--segment:var(--s4)"><strong>S4</strong><h2>Top-frequency high-value</h2><p>测试 VIP 或高接触服务，同时记录服务成本。</p></article>
</div>

<div class="test-flow"><span><b>1. Segment hypothesis</b><br>选择一个客群与措施</span><span class="arrow">→</span><span><b>2. Controlled A/B test</b><br>保留明确对照组</span><span class="arrow">→</span><span><b>3. Future KPI</b><br>repeat purchase · retention · future Net value · service cost</span></div>

<p class="closing-line">The segments support better questions; experiments are needed before actions.</p>

<!--
回到研究问题：可以。RFM 在这份数据中识别出四个有意义且稳定的探索性行为模式。但最终成果不是把客户贴上永久标签，而是把交易数据压缩成可查询的行为结构，并提出更具体的问题。例如对 S1 测试低成本唤回，对 S2 测试复购提醒，对 S3 测试留存权益，对 S4 测试 VIP 服务。所有措施都要设置对照组，并用未来复购、留存、Net value 和服务成本验证。结论是：分群帮助我们提出更好的问题，但行动之前仍需要实验。谢谢。
-->
