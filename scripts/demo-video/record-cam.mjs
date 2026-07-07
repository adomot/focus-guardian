import { chromium } from 'playwright'
import { fileURLToPath } from 'node:url'
import { dirname, join } from 'node:path'
import { readdirSync, renameSync } from 'node:fs'

const dir = dirname(fileURLToPath(import.meta.url))
const outDir = join(dir, 'cam-rec')

const browser = await chromium.launch()
const context = await browser.newContext({
  viewport: { width: 480, height: 360 },
  recordVideo: { dir: outDir, size: { width: 480, height: 360 } },
})
const page = await context.newPage()
await page.goto('file://' + join(dir, 'cam.html'))
await page.waitForTimeout(31_000)
await context.close()
await browser.close()

const webm = readdirSync(outDir).find((f) => f.endsWith('.webm'))
renameSync(join(outDir, webm), join(dir, 'cam-raw.webm'))
console.log('saved cam-raw.webm')
