import { chromium } from 'playwright'
import { fileURLToPath } from 'node:url'
import { dirname, join } from 'node:path'

const dir = dirname(fileURLToPath(import.meta.url))
const browser = await chromium.launch()
const page = await browser.newPage({ viewport: { width: 960, height: 720 } })

for (const name of ['title', 'outro']) {
  await page.goto('file://' + join(dir, `${name}.html`))
  await page.waitForTimeout(400)
  await page.screenshot({ path: join(dir, `${name}.png`) })
}
await browser.close()
console.log('cards done')
