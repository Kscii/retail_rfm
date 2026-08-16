<script setup>
const points = [
  [32, 42], [41, 50], [46, 36], [38, 31], [54, 45],
  [121, 48], [132, 39], [138, 55], [127, 61], [146, 45],
  [67, 120], [76, 111], [82, 126], [91, 116], [73, 135],
  [143, 127], [151, 115], [160, 132], [136, 139], [166, 119],
]
</script>

<template>
  <div>
    <div class="method-grid">
      <article>
        <div class="method-head"><b>Baseline</b><h2>Random initialization</h2></div>
        <svg viewBox="0 0 190 165" role="img" aria-label="Random initial centers can start close together">
          <circle v-for="([x,y], i) in points" :key="i" :cx="x" :cy="y" r="3.3" class="point" />
          <g v-click><path d="M43 42 l9 9 m0 -9 l-9 9" class="center random"/><path d="M55 45 l9 9 m0 -9 l-9 9" class="center random"/><path d="M57 58 l9 9 m0 -9 l-9 9" class="center random"/><path d="M68 50 l9 9 m0 -9 l-9 9" class="center random"/></g>
        </svg>
        <p>Initial centers may be close; the fitted result can depend on the start.</p>
      </article>
      <article class="main-method">
        <div class="method-head"><b>Main method</b><h2>K-means++ initialization</h2></div>
        <svg viewBox="0 0 190 165" role="img" aria-label="K-means plus plus spreads the initial centers">
          <circle v-for="([x,y], i) in points" :key="i" :cx="x" :cy="y" r="3.3" class="point" />
          <g v-click><path d="M38 38 l10 10 m0 -10 l-10 10" class="center spread"/><path d="M129 43 l10 10 m0 -10 l-10 10" class="center spread"/><path d="M72 115 l10 10 m0 -10 l-10 10" class="center spread"/><path d="M146 119 l10 10 m0 -10 l-10 10" class="center spread"/></g>
        </svg>
        <p>Later initial centers are more likely to come from points far from existing centers.</p>
      </article>
    </div>
    <div v-click class="same-loop">
      <span><b>1 Assign</b> each customer to the nearest centroid</span><i>→</i>
      <span><b>2 Update</b> each centroid to the cluster mean</span><i>→</i>
      <span><b>3 Repeat</b> until assignments stabilize</span>
    </div>
    <div class="parameters"><span>Squared Euclidean distance</span><span>k = 2…8</span><span>50 fixed seeds for stability</span><span>final: n_init = 20</span></div>
  </div>
</template>

<style scoped>
.method-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
article { display: grid; grid-template-columns: 1fr 1.25fr; grid-template-rows: 1fr auto; min-height: 225px; padding: 12px; border: 1px solid var(--line); }
.main-method { border: 2px solid var(--accent); }
.method-head { align-self: center; }.method-head b { color: var(--accent); font-size: 10px; text-transform: uppercase; }.method-head h2 { margin: 5px 0; font-size: 17px; line-height: 1.25; }
svg { width: 100%; height: 175px; border-left: 1px solid var(--line); }.point { fill: #c9c9c9; }.center { fill: none; stroke-width: 4; stroke-linecap: round; }.random { stroke: var(--refund); }.spread { stroke: var(--accent); }
article p { grid-column: 1 / -1; padding-top: 7px; border-top: 1px solid var(--line); color: var(--muted); font-size: 10px; }
.same-loop { display: grid; grid-template-columns: 1fr auto 1fr auto 1fr; align-items: center; gap: 7px; margin-top: 13px; padding: 9px 12px; border: 1px solid var(--line); background: var(--wash); text-align: center; font-size: 10px; }
.same-loop b { color: var(--accent); }.same-loop i { color: var(--accent); font-size: 18px; font-style: normal; font-weight: 900; }
.parameters { display: grid; grid-template-columns: repeat(4, 1fr); margin-top: 11px; border: 1px solid var(--line); font-size: 9px; text-align: center; }
.parameters span { padding: 6px; border-right: 1px solid var(--line); }.parameters span:last-child { border-right: 0; }
</style>
