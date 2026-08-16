<script setup>
const asset = name => new URL(`static-demo/${name}`, document.baseURI).href
</script>

<template>
  <div class="method-shell">
    <div class="animation-stage" aria-label="K-means++ trajectory on the actual RFM data">
      <img :src="asset('kmeans-step-0.svg')" alt="All 4,338 customers shown in gray" data-kmeans-step="0" />
      <img v-click :src="asset('kmeans-step-1.svg')" alt="Choose the first initial center at random" data-kmeans-step="1" />
      <img v-click :src="asset('kmeans-step-2.svg')" alt="Choose the second center using D-squared weights" data-kmeans-step="2" />
      <img v-click :src="asset('kmeans-step-3.svg')" alt="Choose the third center using updated D-squared weights" data-kmeans-step="3" />
      <img v-click :src="asset('kmeans-step-4.svg')" alt="Choose the fourth K-means++ center" data-kmeans-step="4" />
      <img v-click :src="asset('kmeans-step-5.svg')" alt="Complete K-means iteration 1" data-kmeans-step="5" />
      <img v-click :src="asset('kmeans-step-6.svg')" alt="Complete K-means iteration 2" data-kmeans-step="6" />
      <img v-click :src="asset('kmeans-step-7.svg')" alt="Complete K-means iteration 3" data-kmeans-step="7" />
      <img v-click :src="asset('kmeans-step-8.svg')" alt="Complete K-means iteration 4" data-kmeans-step="8" />
      <img v-click :src="asset('kmeans-step-9.svg')" alt="Complete K-means iteration 5" data-kmeans-step="9" />
      <img v-click :src="asset('kmeans-step-10.svg')" alt="Complete K-means iteration 6" data-kmeans-step="10" />
      <img v-click :src="asset('kmeans-step-11.svg')" alt="Complete K-means iteration 7" data-kmeans-step="11" />
      <img v-click :src="asset('kmeans-step-12.svg')" alt="Complete K-means iteration 8" data-kmeans-step="12" />
      <img v-click :src="asset('kmeans-step-13.svg')" alt="Complete K-means iteration 9" data-kmeans-step="13" />
      <img v-click :src="asset('kmeans-step-14.svg')" alt="Complete K-means iteration 10" data-kmeans-step="14" />
      <img v-click :src="asset('kmeans-step-15.svg')" alt="Complete K-means iteration 11" data-kmeans-step="15" />
      <img v-click :src="asset('kmeans-step-16.svg')" alt="Complete K-means iteration 12" data-kmeans-step="16" />
      <img v-click :src="asset('kmeans-step-17.svg')" alt="Complete K-means iteration 13" data-kmeans-step="17" />
      <img v-click :src="asset('kmeans-step-18.svg')" alt="Complete K-means iteration 14" data-kmeans-step="18" />
      <img v-click :src="asset('kmeans-step-19.svg')" alt="Stable K-means iteration 15" data-kmeans-step="19" />
    </div>
    <div class="method-notes">
      <p><b>Initialization</b> Orange shows relative D² weight—not a cluster. Farther points receive a higher probability of being selected.</p>
      <p><b>Each iteration</b> Point colors show assignment. Hollow → solid centroids show recentering.</p>
      <p><b>Boundary</b> Colors use all three RFM features. This R–F projection is not a 2D decision boundary.</p>
    </div>
    <div class="method-meta"><span><b>4,338</b> customers</span><span><b>3D</b> assignment</span><span><b>R–F</b> projection</span><span><b>seed 431</b> · k=4</span><span><b>iteration 15</b> stable · ARI=1 vs final</span></div>
  </div>
</template>

<style scoped>
.method-shell { display: grid; grid-template-columns: 1.55fr .75fr; gap: 12px; }
.animation-stage { position: relative; height: 318px; overflow: hidden; border: 1px solid var(--line); background: white; }
.animation-stage img { position: absolute; inset: 0; width: 100%; height: 100%; object-fit: contain; background: white; }
.animation-stage img.slidev-vclick-target { transition: none !important; }
.method-notes { display: grid; align-content: start; gap: 9px; }
.method-notes p { padding: 10px 11px; border: 1px solid var(--line); border-left: 5px solid var(--accent); color: var(--muted); font-size: 10.5px; line-height: 1.42; }
.method-notes b { display: block; margin-bottom: 2px; color: var(--ink); font-size: 11px; }
.method-meta { grid-column: 1 / -1; display: flex; justify-content: space-between; gap: 7px; padding: 7px 10px; background: var(--wash); color: var(--muted); font-size: 8.5px; }
.method-meta b { color: var(--ink); }
</style>
