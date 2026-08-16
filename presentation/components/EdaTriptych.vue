<template>
  <div class="eda-grid">
    <article>
      <p class="number">24.93%</p>
      <h2>CustomerID 缺失</h2>
      <div class="bar"><span></span></div>
      <p class="detail">135,080 / 541,909 invoice lines</p>
      <p class="meaning">无法可靠聚合到客户级 RFM。</p>
    </article>
    <article>
      <p class="customer">Customer 16446</p>
      <h2>退款会改变客户价值解释</h2>
      <div class="refund-flow"><b>Gross<br>£168,472.50</b><span>→</span><b>Net<br><em>£2.90</em></b></div>
      <p class="meaning">只看正向购买会制造“虚假的大客户”。</p>
    </article>
    <article>
      <p class="customer">Customer-level long tails</p>
      <h2>Frequency 与 Net M 高度偏斜</h2>
      <div class="tail-row"><b>F</b><span>median 2</span><i></i><span>99.5% 41.9</span><i class="long"></i><span>max 209</span></div>
      <div class="tail-row"><b>M</b><span>£650</span><i></i><span>£33.4k</span><i class="long"></i><span>£279.5k</span></div>
      <p class="meaning">极端值可能把 distance 和 centroid 拉向长尾。</p>
    </article>
  </div>
</template>

<style scoped>
.eda-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 14px; }
article { min-height: 300px; padding: 17px; border: 1px solid var(--line); border-top: 5px solid var(--accent); }
article:nth-child(2) { border-top-color: var(--refund); }
article:nth-child(3) { border-top-color: var(--cap); }
.number { color: var(--accent); font-size: 40px; font-weight: 850; line-height: 1; }
h2 { min-height: 48px; margin: 7px 0 17px; font-size: 17px; line-height: 1.25; }
.customer { color: var(--muted); font-size: 11px; font-weight: 800; text-transform: uppercase; }
.bar { width: 100%; height: 22px; border: 1px solid var(--line); background: var(--wash); }
.bar span { display: block; width: 24.93%; height: 100%; background: var(--accent); }
.detail { margin-top: 7px; color: var(--muted); font-size: 11px; }
.meaning { margin-top: 24px; padding-top: 10px; border-top: 1px solid var(--line); color: var(--muted); font-size: 12px; line-height: 1.45; }
.refund-flow { display: grid; grid-template-columns: 1fr auto 1fr; align-items: center; gap: 7px; padding: 17px 8px; background: var(--wash); text-align: center; font-size: 14px; }
.refund-flow span { color: var(--refund); font-size: 25px; }.refund-flow em { color: var(--refund); font-style: normal; }
.tail-row { display: grid; grid-template-columns: auto auto 1fr auto 1.5fr auto; align-items: center; gap: 5px; margin: 17px 0; font-size: 9px; }
.tail-row b { color: var(--cap); font-size: 13px; }.tail-row i { height: 2px; background: var(--line); }.tail-row i.long { background: var(--cap); }
</style>
