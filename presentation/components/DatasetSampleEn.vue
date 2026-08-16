<template>
  <div class="dataset-shell">
    <div class="dataset-stats">
      <div><strong>541,909</strong><span>invoice lines</span></div>
      <div><strong>8</strong><span>fields</span></div>
      <div><strong>25,900</strong><span>distinct InvoiceNo</span></div>
      <div><strong>01 Dec 2010–09 Dec 2011</strong><span>observation window</span></div>
    </div>
    <div>
      <div class="table-title"><b>One customer · two real invoices</b><span>all 8 original fields</span></div>
      <table>
        <thead><tr><th>InvoiceNo</th><th>StockCode</th><th>Description</th><th>Quantity</th><th>InvoiceDate</th><th>UnitPrice</th><th>CustomerID</th><th>Country</th></tr></thead>
        <tbody>
          <tr><td>536365</td><td>85123A</td><td>WHITE HANGING HEART...</td><td>6</td><td>01 Dec 08:26</td><td>£2.55</td><td>17850</td><td>United Kingdom</td></tr>
          <tr><td>536365</td><td>71053</td><td>WHITE METAL LANTERN</td><td>6</td><td>01 Dec 08:26</td><td>£3.39</td><td>17850</td><td>United Kingdom</td></tr>
          <tr><td>536365</td><td>84406B</td><td>CREAM CUPID HEARTS...</td><td>8</td><td>01 Dec 08:26</td><td>£2.75</td><td>17850</td><td>United Kingdom</td></tr>
          <tr class="continuation"><td colspan="8">Invoice 536365 has four more product lines</td></tr>
          <tr><td>536366</td><td>22633</td><td>HAND WARMER UNION JACK</td><td>6</td><td>01 Dec 08:28</td><td>£1.85</td><td>17850</td><td>United Kingdom</td></tr>
          <tr><td>536366</td><td>22632</td><td>HAND WARMER RED POLKA...</td><td>6</td><td>01 Dec 08:28</td><td>£1.85</td><td>17850</td><td>United Kingdom</td></tr>
        </tbody>
      </table>
    </div>
    <div class="dataset-bottom">
      <div class="relationship-line"><b>Customer</b><span>1 : N</span><b>Invoice</b><span>1 : N</span><b class="accent-label">Invoice line</b></div>
      <div class="field-map">
        <span><b>R</b> ← InvoiceDate</span>
        <span><b>F</b> ← distinct InvoiceNo</span>
        <span><b>Net M</b> ← Quantity × UnitPrice</span>
        <span><b>CustomerID</b> ← customer aggregation</span>
        <span class="context"><b>StockCode · Description · Country</b> → audit and context</span>
      </div>
    </div>
    <div class="row-callout">One row is an invoice line—not a complete invoice or a customer.</div>
  </div>
</template>

<style scoped>
.dataset-shell { display: grid; gap: 8px; }
.dataset-stats { display: grid; grid-template-columns: .8fr .45fr .8fr 1.5fr; border: 1px solid var(--line); }
.dataset-stats div { padding: 7px 11px; border-right: 1px solid var(--line); }
.dataset-stats div:last-child { border-right: 0; }
.dataset-stats strong { display: block; font-size: 18px; line-height: 1.15; }
.dataset-stats span { color: var(--muted); font-size: 10px; }
.table-title { display: flex; justify-content: space-between; padding: 5px 8px; border: 1px solid var(--line); border-bottom: 0; font-size: 10px; }
.table-title span { color: var(--muted); }
table { width: 100%; table-layout: fixed; border-collapse: collapse; font-size: 7.6px; }
th, td { overflow: hidden; padding: 4px 4px; border: 1px solid var(--line); text-align: left; text-overflow: ellipsis; white-space: nowrap; }
th { background: var(--wash); font-weight: 800; }
th:nth-child(1), td:nth-child(1) { width: 9%; } th:nth-child(2), td:nth-child(2) { width: 9%; }
th:nth-child(3), td:nth-child(3) { width: 23%; } th:nth-child(4), td:nth-child(4) { width: 8%; }
th:nth-child(5), td:nth-child(5) { width: 14%; } th:nth-child(6), td:nth-child(6) { width: 8%; }
th:nth-child(7), td:nth-child(7) { width: 10%; } th:nth-child(8), td:nth-child(8) { width: 19%; }
.continuation td { padding: 2px 5px; background: #fbfbfa; color: var(--muted); font-style: italic; text-align: center; }
.dataset-bottom { display: grid; grid-template-columns: .9fr 1.7fr; gap: 8px; }
.relationship-line { display: flex; align-items: center; justify-content: center; gap: 7px; padding: 7px; border: 1px solid var(--line); font-size: 8px; text-align: center; }
.relationship-line span { color: var(--accent); font-weight: 850; }.accent-label { color: var(--accent); }
.field-map { display: flex; flex-wrap: wrap; gap: 3px 5px; padding: 5px; border: 1px solid var(--line); font-size: 7.5px; }
.field-map span { padding: 3px 5px; background: var(--wash); }.field-map b { color: var(--accent); }.field-map .context b { color: var(--muted); }
.row-callout { padding: 5px 9px; border-left: 5px solid var(--accent); background: var(--wash); color: var(--accent); font-size: 10px; font-weight: 750; }
</style>
