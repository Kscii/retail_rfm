<template>
  <div>
    <div class="funnel">
      <div><strong>541,909</strong><span>raw lines</span></div><i>→</i>
      <div><strong>536,641</strong><span>after exact deduplication</span><small>5,268 extra copies removed</small></div><i>→</i>
      <div><strong>401,604</strong><span>known-customer signed lines</span></div><i>→</i>
      <div><strong>392,692</strong><span>valid positive lines for R/F</span></div><i>→</i>
      <div class="customer"><strong>4,338</strong><span>customer RFM profiles</span></div>
    </div>

    <div v-click class="branch-row">
      <article>
        <b>R / F branch</b>
        <p>Only valid positive purchase invoices</p>
        <span>Cancellation does not add or subtract Frequency</span>
      </article>
      <div class="refund-example">
        <span>£100 purchase</span><b>+</b><span class="negative">£100 cancellation</span><b>→</b>
        <strong>F = 1<br>Net M = £0</strong>
      </div>
      <article>
        <b>Net M branch</b>
        <p>All signed known-customer line amounts</p>
        <span>Net describes this observation window</span>
      </article>
    </div>

    <div v-click class="model-input">
      <div><b>99.5% upper cap on F / Net M</b><span>29 customers affected · 0 customers removed · raw RFM kept for profiles</span></div>
      <i>→</i>
      <div><b>StandardScaler</b><span>makes R, F and M scales comparable for Euclidean distance</span></div>
      <i>→</i>
      <div class="ready"><b>Model input</b><span>scaled R · scaled capped F · scaled capped Net M</span></div>
    </div>
  </div>
</template>

<style scoped>
.funnel { display: grid; grid-template-columns: 1fr auto 1.4fr auto 1.25fr auto 1.25fr auto 1fr; align-items: stretch; gap: 5px; }
.funnel div { padding: 10px 8px; border: 1px solid var(--line); text-align: center; }
.funnel div.customer { border: 2px solid var(--accent); }
.funnel strong { display: block; font-size: 18px; }.funnel span { display: block; color: var(--muted); font-size: 9px; }.funnel small { color: var(--refund); font-size: 8px; }
.funnel i, .model-input i { align-self: center; color: var(--accent); font-size: 18px; font-style: normal; font-weight: 900; }
.branch-row { display: grid; grid-template-columns: 1fr 1.2fr 1fr; gap: 10px; margin-top: 15px; }
article, .refund-example { padding: 10px 12px; border: 1px solid var(--line); }
article b { font-size: 12px; } article p { margin: 3px 0 !important; font-size: 11px; font-weight: 700; } article span { color: var(--muted); font-size: 9px; }
.refund-example { display: grid; grid-template-columns: 1fr auto 1fr auto 1fr; align-items: center; background: var(--wash); font-size: 10px; text-align: center; }
.refund-example b { color: var(--refund); }.refund-example strong { color: var(--ink); font-size: 11px; }.negative { color: var(--refund); }
.model-input { display: grid; grid-template-columns: 1.25fr auto 1fr auto 1.25fr; gap: 7px; align-items: stretch; margin-top: 15px; }
.model-input > div { padding: 10px 11px; border: 1px solid var(--line); border-top: 4px solid var(--cap); }
.model-input .ready { border-top-color: var(--accent); }
.model-input b { display: block; font-size: 11px; }.model-input span { display: block; margin-top: 3px; color: var(--muted); font-size: 9px; line-height: 1.35; }
</style>
