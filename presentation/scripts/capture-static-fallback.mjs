import path from 'node:path'
import { chromium } from 'playwright-chromium'

const baseUrl = new URL(process.env.SLIDEV_URL || 'http://localhost:3030/')
const demoUrl = new URL('static-demo/index.html?view=3d', baseUrl)
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
const page = await browser.newPage({ viewport: { width: 900, height: 550 }, deviceScaleFactor: 1 })
await page.goto(demoUrl.href, { waitUntil: 'networkidle' })
await page.locator('canvas').first().waitFor({ state: 'visible' })
await page.waitForTimeout(500)
await page.screenshot({
  path: path.resolve('public/images/slide8-demo.png'),
  animations: 'disabled',
})
await browser.close()
console.log(`Captured ${demoUrl.href} -> public/images/slide8-demo.png`)
