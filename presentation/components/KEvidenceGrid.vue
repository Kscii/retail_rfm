<script setup>
const ks = [2,3,4,5,6,7,8]
const panels = [
  { title: 'Inertia / elbow', subtitle: 'lower is tighter', values: [8069.997,4528.706,2911.490,2285.276,1862.233,1564.056,1422.321], min: 1200, max: 8500, format: v => Math.round(v).toLocaleString() },
  { title: 'Silhouette', subtitle: 'higher separation', values: [.724968,.547319,.563198,.490094,.463964,.437442,.405997], min: .35, max: .78, format: v => v.toFixed(3) },
  { title: 'Median pairwise ARI', subtitle: 'higher seed stability', values: [.990584,.979997,1,.634902,.979902,.771907,.6754], min: .55, max: 1.04, format: v => v.toFixed(3) },
  { title: 'Smallest cluster', subtitle: '1% is a check line', values: [4.1955,3.4578,1.1757,.9912,.8529,.7838,.7838], min: 0, max: 4.6, format: v => `${v.toFixed(2)}%`, check: 1 },
]
function y(panel, value) { return 111 - ((value-panel.min)/(panel.max-panel.min))*82 }
function points(panel) { return panel.values.map((value,index)=>`${30+index*49},${y(panel,value)}`).join(' ') }
</script>

<template>
  <div>
    <div class="evidence-grid">
      <article v-for="panel in panels" :key="panel.title">
        <div class="panel-head"><div><h2>{{ panel.title }}</h2><p>{{ panel.subtitle }}</p></div><strong>k=4: {{ panel.format(panel.values[2]) }}</strong></div>
        <svg viewBox="0 0 340 145" role="img" :aria-label="panel.title">
          <line x1="30" x2="324" y1="111" y2="111" class="axis" />
          <line v-if="panel.check" x1="30" x2="324" :y1="y(panel,panel.check)" :y2="y(panel,panel.check)" class="check" />
          <polyline :points="points(panel)" class="series" />
          <g v-for="(value,index) in panel.values" :key="index">
            <circle :cx="30+index*49" :cy="y(panel,value)" :r="index===2?6:3.5" :class="index===2?'selected':'dot'" />
            <text :x="30+index*49" y="129" text-anchor="middle">{{ ks[index] }}</text>
          </g>
          <text x="176" y="142" text-anchor="middle" class="axis-label">number of clusters (k)</text>
        </svg>
      </article>
    </div>
    <div class="decision">
      <b>Decision:</b> k=2 has strong separation but gives a coarse split; <strong>k=4</strong> keeps a clear elbow, perfect median seed agreement, a 1.18% smallest cluster and interpretable four-level profiles.
      <span>These are internal evaluation signals—not accuracy and not proof of ground-truth groups.</span>
    </div>
  </div>
</template>

<style scoped>
.evidence-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 8px 13px; }
article { min-height: 145px; padding: 7px 11px 3px; border: 1px solid var(--line); }
.panel-head { display: flex; justify-content: space-between; gap: 8px; align-items: flex-start; }
h2 { margin: 0; font-size: 14px; }.panel-head p { color: var(--muted); font-size: 9px; }.panel-head strong { color: var(--accent); font-size: 10px; }
svg { width: 100%; height: 94px; overflow: visible; }.axis { stroke: #aaa; stroke-width: 1; }.series { fill: none; stroke: #666; stroke-width: 2; }.dot { fill: #666; }.selected { fill: var(--accent); stroke: white; stroke-width: 1.5; }.check { stroke: var(--refund); stroke-dasharray: 4 3; stroke-width: 1; } text { fill: #666; font-size: 8px; }.axis-label { font-size: 7px; }
.decision { display: grid; grid-template-columns: auto 1fr; column-gap: 6px; margin-top: 7px; padding: 6px 10px; border-left: 5px solid var(--accent); background: var(--wash); font-size: 9px; line-height: 1.3; }
.decision strong { color: var(--accent); }.decision span { grid-column: 1 / -1; margin-top: 4px; color: var(--muted); font-size: 9px; }
</style>
