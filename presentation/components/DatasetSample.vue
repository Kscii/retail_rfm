<template>
  <div class="dataset-shell">
    <div class="dataset-stats">
      <div><strong>541,909</strong><span>invoice lines</span></div>
      <div><strong>8</strong><span>fields</span></div>
      <div><strong>25,900</strong><span>distinct InvoiceNo</span></div>
      <div><strong>01 Dec 2010–09 Dec 2011</strong><span>observation window</span></div>
    </div>
    <div class="dataset-main">
      <div>
        <div class="table-title"><b>Invoice 536365</b><span>three of seven invoice lines shown</span></div>
        <table>
          <thead><tr><th>InvoiceNo</th><th>StockCode</th><th>Description</th><th>Qty</th><th>CustomerID</th></tr></thead>
          <tbody>
            <tr><td>536365</td><td>85123A</td><td>WHITE HANGING HEART...</td><td>6</td><td>17850</td></tr>
            <tr><td>536365</td><td>71053</td><td>WHITE METAL LANTERN</td><td>6</td><td>17850</td></tr>
            <tr><td>536365</td><td>84406B</td><td>CREAM CUPID HEARTS COAT...</td><td>8</td><td>17850</td></tr>
          </tbody>
        </table>
        <div class="row-callout">一行 = 一种商品在一张 invoice 中的记录（invoice line）</div>
      </div>
      <div class="relationship">
        <div class="entity"><b>Customer</b><span>17850</span></div>
        <div class="one-many"><span>1</span><i></i><span>N</span></div>
        <div class="entity"><b>Invoice</b><span>536365</span></div>
        <div class="one-many"><span>1</span><i></i><span>N</span></div>
        <div class="entity accent-entity"><b>Invoice line</b><span>one product row</span></div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.dataset-shell { display: grid; gap: 16px; }
.dataset-stats { display: grid; grid-template-columns: .8fr .45fr .8fr 1.5fr; border: 1px solid var(--line); }
.dataset-stats div { padding: 10px 13px; border-right: 1px solid var(--line); }
.dataset-stats div:last-child { border-right: 0; }
.dataset-stats strong { display: block; font-size: 18px; line-height: 1.15; }
.dataset-stats span { color: var(--muted); font-size: 10px; }
.dataset-main { display: grid; grid-template-columns: 1.5fr .5fr; gap: 17px; align-items: stretch; }
.table-title { display: flex; justify-content: space-between; padding: 7px 9px; border: 1px solid var(--line); border-bottom: 0; font-size: 11px; }
.table-title span { color: var(--muted); }
table { width: 100%; border-collapse: collapse; font-size: 10px; }
th, td { padding: 8px 7px; border: 1px solid var(--line); text-align: left; }
th { background: var(--wash); font-weight: 800; }
.row-callout { padding: 9px 11px; border: 1px solid var(--accent); border-top: 0; color: var(--accent); font-size: 12px; font-weight: 750; }
.relationship { display: grid; grid-template-rows: auto auto auto auto auto; align-items: center; }
.entity { padding: 10px 12px; border: 1px solid var(--line); text-align: center; }
.entity b { display: block; font-size: 13px; }
.entity span { color: var(--muted); font-size: 10px; }
.accent-entity { border: 2px solid var(--accent); }
.one-many { display: grid; grid-template-columns: auto 1fr auto; align-items: center; gap: 5px; padding: 2px 12px; color: var(--muted); font-size: 9px; }
.one-many i { height: 1px; background: var(--line); }
</style>
