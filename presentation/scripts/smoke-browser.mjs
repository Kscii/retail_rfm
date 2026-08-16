import fs from 'node:fs'
import path from 'node:path'
import { chromium } from 'playwright-chromium'

const outputDir = path.resolve('dist/browser-smoke')
fs.mkdirSync(outputDir, { recursive: true })
const baseUrl = new URL(process.env.SLIDEV_URL || 'http://localhost:3030/')
const slideUrl = number => new URL(String(number), baseUrl).href
const allowedOrigin = baseUrl.origin

const browser = await chromium.launch({
  executablePath: '/usr/bin/chromium',
  headless: true,
  args: [
    '--no-sandbox',
    '--use-gl=angle',
    '--use-angle=swiftshader',
    '--enable-unsafe-swiftshader',
    '--enable-webgl',
    '--ignore-gpu-blocklist',
  ],
})

const report = { baseUrl: baseUrl.href, checks: {}, consoleErrors: [], failedRequests: [], remoteRequests: [] }
const page = await browser.newPage({ viewport: { width: 1440, height: 900 } })
page.on('console', message => {
  if (message.type() === 'error') report.consoleErrors.push(message.text())
})
page.on('requestfailed', request => {
  if (request.failure()?.errorText !== 'net::ERR_ABORTED')
    report.failedRequests.push(`${request.method()} ${request.url()} · ${request.failure()?.errorText}`)
})
page.on('request', request => {
  const origin = new URL(request.url()).origin
  if (origin !== allowedOrigin) report.remoteRequests.push(request.url())
})

await page.goto(slideUrl(7), { waitUntil: 'networkidle' })
await page.keyboard.press('ArrowRight')
await page.waitForURL(url => url.pathname.endsWith('/8'))
report.checks.noSourceSwitch = await page.getByText(/Live Dash|Static fallback/).count() === 0
report.checks.noOuterDemoBar = await page.getByText('Interactive RFM explorer', { exact: true }).count() === 0
const visibleDemoFrame = page.locator('iframe.live-demo-frame:visible')
await visibleDemoFrame.waitFor({ state: 'visible' })
const staticFrame = await (await visibleDemoFrame.elementHandle()).contentFrame()
if (!staticFrame) throw new Error('Static presentation iframe was not found')
await staticFrame.locator('#plot').waitFor({ state: 'visible' })
await staticFrame.locator('canvas').first().waitFor({ state: 'visible' })
await staticFrame.waitForFunction(() => {
  const element = document.querySelector('#plot')
  const viewportWidth = document.documentElement.clientWidth
  return element?._fullLayout && document.documentElement.scrollWidth <= viewportWidth + 1
    && Math.abs(element._fullLayout.width - viewportWidth) <= 1
})
report.checks.firstNavigationSizing = await staticFrame.locator('#plot').evaluate(element => ({
  viewportWidth: document.documentElement.clientWidth,
  documentScrollWidth: document.documentElement.scrollWidth,
  plotClientWidth: element.clientWidth,
  plotLayoutWidth: element._fullLayout?.width,
}))
report.checks.static3dCanvas = await staticFrame.locator('canvas').count()
report.checks.staticCustomerCountCopy = await staticFrame.getByText(/4,338 customers/).count()
report.checks.noProfilesButton = await staticFrame.getByRole('button', { name: 'Profiles', exact: true }).count() === 0
report.checks.noStaticFooter = await staticFrame.locator('footer').count() === 0
report.checks.markerContract = await staticFrame.locator('#plot').evaluate(element => {
  const traces = element.data || []
  const customers = traces.filter(trace => ['S1', 'S2', 'S3', 'S4'].includes(trace.name))
  const centroids = traces.find(trace => trace.name === 'Centroids')
  return {
    customerTraceCount: customers.length,
    normal: customers.filter(trace => trace.marker.size === 1.8 && trace.marker.opacity === 0.35).length,
    capped: customers.filter(trace => trace.marker.size === 2.8 && trace.marker.opacity === 0.65).length,
    centroidSize: centroids?.marker?.size,
    centroidSymbol: centroids?.marker?.symbol,
    hoverFontSize: element.layout?.hoverlabel?.font?.size,
  }
})
const plotBox = await staticFrame.locator('#plot').boundingBox()
let hoverFontSize = null
await staticFrame.locator('#plot').evaluate(element => {
  try { Plotly.Fx.hover(element, [{ curveNumber: 7, pointNumber: 0 }]) } catch {}
})
await page.waitForTimeout(150)
const programmedHover = staticFrame.locator('.hoverlayer .hovertext text').first()
if (await programmedHover.count() && await programmedHover.isVisible())
  hoverFontSize = await programmedHover.evaluate(element => getComputedStyle(element).fontSize)
if (plotBox) {
  for (const yRatio of [0.15, 0.25, 0.35, 0.45, 0.55, 0.65, 0.75, 0.85]) {
    for (const xRatio of [0.35, 0.45, 0.55, 0.65, 0.75, 0.85]) {
      if (hoverFontSize) break
      await page.mouse.move(plotBox.x + plotBox.width * xRatio, plotBox.y + plotBox.height * yRatio)
      await page.waitForTimeout(35)
      const hoverText = staticFrame.locator('.hoverlayer .hovertext text').first()
      if (await hoverText.count() && await hoverText.isVisible()) {
        hoverFontSize = await hoverText.evaluate(element => getComputedStyle(element).fontSize)
        break
      }
    }
    if (hoverFontSize) break
  }
}
report.checks.hoverTooltipFontSize = hoverFontSize
if (hoverFontSize) await page.screenshot({ path: path.join(outputDir, 'slide8-hover-1440x900.png') })
await page.screenshot({ path: path.join(outputDir, 'slide8-static-1440x900.png') })

for (const [label, check] of [['R–F', 'staticRfVisible'], ['R–M', 'staticRmVisible'], ['F–M', 'staticFmVisible']]) {
  await staticFrame.getByRole('button', { name: label }).click()
  await staticFrame.locator('.scatterlayer').waitFor({ state: 'visible' })
  report.checks[check] = true
}
await staticFrame.getByRole('button', { name: 'Customer 13777' }).click()
await staticFrame.getByText('41 recorded invoices').waitFor({ state: 'visible' })
await staticFrame.locator('#timeline.js-plotly-plot').waitFor({ state: 'visible' })
report.checks.staticCustomer13777 = await staticFrame.evaluate(() => {
  const summary = document.querySelector('.customer-summary').getBoundingClientRect()
  const timeline = document.querySelector('#timeline').getBoundingClientRect()
  return {
    customer: document.querySelector('.customer-summary h2')?.textContent,
    invoices: document.body.innerText.includes('41 recorded invoices'),
    cancellations: document.body.innerText.includes('8 C-prefixed cancellations'),
    twoColumns: Math.abs(summary.top - timeline.top) < 3,
    summaryVisible: summary.bottom <= window.innerHeight && summary.left >= 0,
    timelineVisible: timeline.bottom <= window.innerHeight && timeline.right <= window.innerWidth,
    timelineHeight: timeline.height,
  }
})
await page.screenshot({ path: path.join(outputDir, 'slide8-customer-1440x900.png') })

await page.goto(slideUrl(6), { waitUntil: 'networkidle' })
const step0 = page.locator('[data-kmeans-step="0"]:visible')
await step0.waitFor({ state: 'visible' })
report.checks.animationImagesLoaded = await page.locator('[data-kmeans-step]').evaluateAll(images => ({
  count: images.length,
  loaded: images.filter(image => image.complete && image.naturalWidth > 0).length,
}))
report.checks.animationSteps = [await step0.count()]
report.checks.animationOpacity = [await step0.evaluate(element => Number(getComputedStyle(element).opacity))]
for (let step = 1; step <= 19; step += 1) {
  await page.keyboard.press('ArrowRight')
  await page.waitForTimeout(100)
  const frame = page.locator(`[data-kmeans-step="${step}"]`)
  await frame.waitFor({ state: 'attached' })
  report.checks.animationSteps.push(await frame.count())
  report.checks.animationOpacity.push(await frame.evaluate(element => Number(getComputedStyle(element).opacity)))
}
report.checks.animationFinalText = await page.getByText(/iteration 15 stable · ARI=1 vs final/i).count()
await page.screenshot({ path: path.join(outputDir, 'slide6-final-1440x900.png') })

await page.setViewportSize({ width: 1280, height: 720 })
await page.goto(slideUrl(8), { waitUntil: 'networkidle' })
report.checks.width1280 = await page.evaluate(() => ({
  body: document.body.scrollWidth,
  viewport: window.innerWidth,
  horizontalOverflow: document.body.scrollWidth > window.innerWidth,
}))
await page.screenshot({ path: path.join(outputDir, 'slide8-static-1280x720.png') })

await page.goto(slideUrl(1), { waitUntil: 'networkidle' })
report.checks.titleName = await page.getByText('Xuejian Fang', { exact: true }).count()
report.checks.supervisor = await page.getByText('Professor Osman Yagan', { exact: true }).count()
report.checks.supervisedBy = await page.getByText(/Supervised by/i).count()
report.checks.englishTitle = await page.getByText('Online Retail Customer Segmentation', { exact: true }).count()
report.checks.studentIdText = await page.getByText(/student\s*id|sid/i).count()
report.checks.visibleCjk = await page.locator('body').evaluate(body => /[\u3400-\u9fff]/.test(body.innerText))
await page.screenshot({ path: path.join(outputDir, 'slide1-1280x720.png') })

report.checks.allSlides = []
for (const viewport of [{ width: 1440, height: 900 }, { width: 1280, height: 720 }]) {
  await page.setViewportSize(viewport)
  for (let slide = 1; slide <= 10; slide += 1) {
    await page.goto(slideUrl(slide), { waitUntil: 'domcontentloaded' })
    const activeLayout = page.locator('.slidev-layout:visible')
    await activeLayout.waitFor({ state: 'visible' })
    const layout = await activeLayout.evaluate(element => ({
      clientWidth: element.clientWidth,
      scrollWidth: element.scrollWidth,
      clientHeight: element.clientHeight,
      scrollHeight: element.scrollHeight,
      hasCjk: /[\u3400-\u9fff]/.test(element.innerText),
    }))
    report.checks.allSlides.push({ slide, viewport: `${viewport.width}x${viewport.height}`, ...layout })
  }
}

report.remoteRequests = [...new Set(report.remoteRequests)]
report.failedRequests = [...new Set(report.failedRequests)]
fs.writeFileSync(path.join(outputDir, 'report.json'), JSON.stringify(report, null, 2))
await browser.close()

const markers = report.checks.markerContract
const customer = report.checks.staticCustomer13777
if (report.checks.static3dCanvas < 1) throw new Error('Static WebGL canvas is missing')
const firstSizing = report.checks.firstNavigationSizing
if (firstSizing.documentScrollWidth > firstSizing.viewportWidth + 1 || firstSizing.plotClientWidth !== firstSizing.viewportWidth || Math.abs(firstSizing.plotLayoutWidth - firstSizing.viewportWidth) > 1)
  throw new Error(`First-navigation plot sizing failed: ${JSON.stringify(firstSizing)}`)
if (!report.checks.noSourceSwitch || !report.checks.noProfilesButton || !report.checks.noOuterDemoBar || !report.checks.noStaticFooter) throw new Error('Obsolete demo chrome remains')
if (markers.customerTraceCount !== 8 || markers.normal !== 4 || markers.capped !== 4 || markers.centroidSize !== 4 || markers.centroidSymbol !== 'diamond' || markers.hoverFontSize !== 8)
  throw new Error(`3D marker contract failed: ${JSON.stringify(markers)}`)
if (customer.customer !== '13777' || !customer.invoices || !customer.cancellations || !customer.twoColumns || !customer.summaryVisible || !customer.timelineVisible)
  throw new Error(`Customer 13777 layout contract failed: ${JSON.stringify(customer)}`)
if (report.checks.animationImagesLoaded.count !== 20 || report.checks.animationImagesLoaded.loaded !== 20 || report.checks.animationSteps.some(count => count !== 1) || report.checks.animationOpacity.some(opacity => opacity < 0.99) || report.checks.animationFinalText < 1)
  throw new Error(`K-means++ animation contract failed: ${JSON.stringify({ steps: report.checks.animationSteps, opacity: report.checks.animationOpacity })}`)
if (report.checks.width1280.horizontalOverflow) throw new Error('1280px viewport has horizontal overflow')
if (report.checks.titleName !== 1 || report.checks.supervisor !== 1 || report.checks.supervisedBy !== 0 || report.checks.englishTitle !== 1 || report.checks.studentIdText !== 0)
  throw new Error('Title identity contract failed')
if (report.checks.visibleCjk) throw new Error('Chinese text remains in the final English deck')
const invalidSlide = report.checks.allSlides.find(check =>
  check.scrollWidth > check.clientWidth || check.scrollHeight > check.clientHeight || check.hasCjk)
if (invalidSlide) throw new Error(`Slide layout/language contract failed: ${JSON.stringify(invalidSlide)}`)
if (report.remoteRequests.length) throw new Error(`Unexpected remote requests: ${report.remoteRequests.join(', ')}`)
if (report.failedRequests.length) throw new Error(`Unexpected failed requests: ${report.failedRequests.join(', ')}`)

console.log(JSON.stringify(report, null, 2))
