<template>
  <div>
    <div class="flow">
      <div class="source"><b>Invoice lines</b><span>transaction-level table</span></div>
      <div class="arrow">→</div>
      <div class="rfm-group">
        <div class="rfm r"><strong>R</strong><b>Recency</b><span>days since last valid purchase</span><small>reference: 10 Dec 2011</small></div>
        <div class="rfm f"><strong>F</strong><b>Frequency</b><span>distinct valid purchase invoices</span><small>not product rows or units</small></div>
        <div class="rfm m"><strong>M</strong><b>Net Monetary</b><span>signed amount in the window</span><small>purchase + cancellation lines</small></div>
      </div>
      <div class="arrow">→</div>
      <div class="target"><b>Behavioral cluster</b><span>S1 · S2 · S3 · S4</span></div>
    </div>
    <div class="unsupervised">
      <b>Unsupervised learning</b><span>No target label</span><span>No classification accuracy</span><span>We evaluate separation, stability, size and meaning</span>
    </div>
  </div>
</template>

<style scoped>
.flow { display: grid; grid-template-columns: .65fr auto 2.1fr auto .7fr; align-items: center; gap: 10px; }
.source, .target { padding: 18px 10px; border: 1px solid var(--line); text-align: center; }
.source b, .target b { display: block; font-size: 15px; }
.source span, .target span { color: var(--muted); font-size: 10px; }
.target { border: 2px solid var(--accent); }
.arrow { color: var(--accent); font-size: 28px; font-weight: 900; }
.rfm-group { display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; }
.rfm { min-height: 175px; padding: 12px; border: 1px solid var(--line); border-top: 5px solid var(--tone); }
.rfm strong { display: block; color: var(--tone); font-size: 32px; line-height: 1; }
.rfm b { display: block; margin: 8px 0 5px; font-size: 14px; }
.rfm span { display: block; color: var(--muted); font-size: 11px; line-height: 1.4; }
.rfm small { display: block; margin-top: 12px; color: var(--tone); font-size: 9px; font-weight: 700; }
.r { --tone: var(--s1); }.f { --tone: var(--s3); }.m { --tone: var(--s4); }
.unsupervised { display: grid; grid-template-columns: 1.1fr .8fr 1fr 2fr; gap: 0; margin-top: 19px; border: 1px solid var(--line); background: var(--wash); font-size: 11px; }
.unsupervised > * { padding: 9px 11px; border-right: 1px solid var(--line); }
.unsupervised > *:last-child { border-right: 0; }
.unsupervised b { color: var(--accent); }
</style>
