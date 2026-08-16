<script setup>
import { useNav } from '@slidev/client'
import { nextTick, onBeforeUnmount, onMounted, ref } from 'vue'

const { isPrintMode } = useNav()
const staticSrc = new URL('static-demo/index.html?view=3d', document.baseURI).href
const printImage = new URL('images/slide8-demo.png', document.baseURI).href
const findingsRoot = ref(null)
const demoFrame = ref(null)
const resizeTimers = new Set()
let visibilityObserver

function requestDemoResize() {
  demoFrame.value?.contentWindow?.postMessage({ type: 'retail-rfm:resize' }, window.location.origin)
}

function scheduleDemoResize() {
  nextTick(() => {
    for (const delay of [0, 80, 220, 500]) {
      const timer = window.setTimeout(() => {
        resizeTimers.delete(timer)
        requestDemoResize()
      }, delay)
      resizeTimers.add(timer)
    }
  })
}

onMounted(() => {
  visibilityObserver = new IntersectionObserver((entries) => {
    if (entries.some(entry => entry.isIntersecting && entry.intersectionRatio >= 0.5)) scheduleDemoResize()
  }, { threshold: [0.5] })
  if (findingsRoot.value) visibilityObserver.observe(findingsRoot.value)
})

onBeforeUnmount(() => {
  visibilityObserver?.disconnect()
  for (const timer of resizeTimers) window.clearTimeout(timer)
  resizeTimers.clear()
})

const profiles = [
  { code:'S1', name:'Long-inactive', customers:'1,054 · 24.30%', net:'5.71%', r:'246d', f:'1', m:'£300', color:'var(--s1)' },
  { code:'S2', name:'Regular', customers:'2,827 · 65.17%', net:'35.58%', r:'37d', f:'3', m:'£716', color:'var(--s2)' },
  { code:'S3', name:'Active high-value', customers:'406 · 9.36%', net:'27.68%', r:'11d', f:'12', m:'£4,804', color:'var(--s3)' },
  { code:'S4', name:'Top-frequency high-value', customers:'51 · 1.18%', net:'31.03%', r:'4d', f:'34', m:'£30,301', color:'var(--s4)' },
]
</script>

<template>
  <div ref="findingsRoot" class="findings">
    <div class="hook"><strong>457 customers</strong><span>about 10.5%</span><i>→</i><strong>58.71%</strong><span>of observed Net value</span></div>
    <div class="findings-body">
      <section class="profiles">
        <article v-for="profile in profiles" :key="profile.code" :style="{'--segment':profile.color}">
          <div class="profile-head"><b>{{ profile.code }}</b><h2>{{ profile.name }}</h2></div>
          <dl>
            <dt>Customers</dt><dd>{{ profile.customers }}</dd>
            <dt>Net share</dt><dd>{{ profile.net }}</dd>
            <dt>Median R / F</dt><dd>{{ profile.r }} / {{ profile.f }}</dd>
            <dt>Median Net M</dt><dd>{{ profile.m }}</dd>
          </dl>
        </article>
      </section>
      <section class="demo-window">
        <iframe v-if="!isPrintMode" ref="demoFrame" class="live-demo-frame" :src="staticSrc" title="RFM compact interactive demo" @load="scheduleDemoResize" />
        <img v-else class="demo-print-fallback" :src="printImage" alt="Static RFM 3D plot with four segments and centroids" />
      </section>
    </div>
    <div class="scale-note"><b>Profiles:</b> original days, orders and pounds <span>·</span> <b>3D:</b> scaled/capped model coordinates <span>·</span> <b>No PCA:</b> one axis per RFM feature</div>
  </div>
</template>

<style scoped>
.findings { margin-top: -9px; }
.hook { display: grid; grid-template-columns: auto auto auto auto 1fr; align-items: baseline; gap: 9px; padding: 8px 12px; border-left: 6px solid var(--accent); background: var(--wash); }
.hook strong { color: var(--accent); font-size: 22px; }.hook span { color: var(--muted); font-size: 11px; }.hook i { color: var(--accent); font-size: 22px; font-style: normal; font-weight: 900; }
.findings-body { display: grid; grid-template-columns: 42% 58%; gap: 10px; margin-top: 10px; }
.profiles { display: grid; grid-template-columns: 1fr 1fr; gap: 7px; }
.profiles article { min-height: 151px; padding: 8px 9px; border: 1px solid var(--line); border-top: 5px solid var(--segment); }
.profile-head { display: grid; grid-template-columns: auto 1fr; align-items: start; gap: 6px; }
.profile-head b { color: var(--segment); font-size: 12px; }.profile-head h2 { min-height: 31px; margin: 0; font-size: 11px; line-height: 1.2; }
dl { display: grid; grid-template-columns: 1fr auto; gap: 3px 5px; margin: 7px 0 0; font-size: 8.5px; }
dt { color: var(--muted); } dd { margin: 0; font-weight: 750; }
.demo-window { overflow: hidden; height: 318px; border: 1px solid #999; background: white; }
iframe { width: 100%; height: 316px; border: 0; background: white; }
.demo-print-fallback { display: block; width: 100%; height: 316px; object-fit: cover; object-position: top; }
.scale-note { margin-top: 7px; color: var(--muted); font-size: 8px; text-align: right; }.scale-note span { color: var(--accent); }
</style>
