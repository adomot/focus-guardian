import { chromium } from 'playwright'
import { fileURLToPath } from 'node:url'
import { dirname, join } from 'node:path'
import { readdirSync, renameSync, rmSync } from 'node:fs'

const dir = dirname(fileURLToPath(import.meta.url))
const name = process.argv[2]
const sec = Number(process.argv[3])

const browser = await chromium.launch()
const recDir = join(dir, 'rec-' + name)
const context = await browser.newContext({
  viewport: { width: 1280, height: 720 },
  recordVideo: { dir: recDir, size: { width: 1280, height: 720 } },
})
const page = await context.newPage()
await page.goto('file://' + join(dir, name + '.html'))
await page.waitForTimeout(sec * 1000)
await context.close()
await browser.close()
const webm = readdirSync(recDir).find((f) => f.endsWith('.webm'))
renameSync(join(recDir, webm), join(dir, name + '.webm'))
rmSync(recDir, { recursive: true, force: true })
console.log(name + ' recorded')
