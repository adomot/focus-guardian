import { chromium } from 'playwright'
import { fileURLToPath } from 'node:url'
import { dirname, join } from 'node:path'

const dir = dirname(fileURLToPath(import.meta.url))

const CAPTIONS = [
  { name: 'cap1', color: '#3c3c3c', text: '① AIヒアリング｜目標とやめたい悪習慣をチャットで設定' },
  { name: 'cap2', color: '#3c3c3c', text: '悪習慣ごとに通知方法を設定（音声 / BGM）' },
  { name: 'cap3', color: '#3c3c3c', text: '② 集中セッション｜カメラ画像を AI が定期判定' },
  { name: 'cap4', color: '#ea2b2b', text: '③ スマホいじりを検知 → 音声でしばく！' },
  { name: 'cap5', color: '#ea2b2b', text: '④ 居眠りを検知 → BGM でしばく！' },
  { name: 'cap6', color: '#58a700', text: '⑤ 成果はサマリーで可視化' },
]

const html = (color, text) => `<!doctype html><html><head><meta charset="utf-8"><style>
  * { margin: 0; padding: 0; }
  body { width: 960px; height: 90px; background: transparent; overflow: hidden;
    display: flex; align-items: center; justify-content: center;
    font-family: "Hiragino Maru Gothic ProN", "Hiragino Sans", sans-serif; }
  .cap { background: ${color}; color: #fff; font-size: 28px; font-weight: 800;
    padding: 14px 34px; border-radius: 999px; box-shadow: 0 4px 0 rgba(0,0,0,.25);
    letter-spacing: 1px; }
</style></head><body><div class="cap">${text}</div></body></html>`

const browser = await chromium.launch()
const page = await browser.newPage({ viewport: { width: 960, height: 90 } })
for (const { name, color, text } of CAPTIONS) {
  await page.setContent(html(color, text))
  await page.waitForTimeout(150)
  await page.screenshot({ path: join(dir, `${name}.png`), omitBackground: true })
}
await browser.close()
console.log('captions done')
