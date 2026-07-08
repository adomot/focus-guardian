import { chromium } from 'playwright'
import { fileURLToPath } from 'node:url'
import { dirname, join } from 'node:path'
import { readdirSync, renameSync, rmSync, writeFileSync } from 'node:fs'

const dir = dirname(fileURLToPath(import.meta.url))
const recDir = join(dir, 'rec-hearing-mobile')

// スマホ実寸 (iPhone 14 相当)。zoom 拡大はスクロール挙動が崩れるためネイティブ解像度で録る
const browser = await chromium.launch()
const context = await browser.newContext({
  viewport: { width: 390, height: 844 },
  recordVideo: { dir: recDir, size: { width: 390, height: 844 } },
})
const page = await context.newPage()

const t0 = Date.now()
const marks = []
const mark = (label) => {
  marks.push({ t: Math.round((Date.now() - t0) / 100) / 10, label })
  console.log(`${((Date.now() - t0) / 1000).toFixed(1)}s  ${label}`)
}
const pause = (ms) => page.waitForTimeout(ms)

const typeAndSend = async (text, cps = 100) => {
  const input = page.locator('input.chat-input')
  await input.click()
  await input.pressSequentially(text, { delay: cps })
  await pause(800)
  await page.getByRole('button', { name: '送信' }).click()
}
const waitBot = (text) =>
  page.locator('.bubble-bot', { hasText: text }).last().waitFor({ timeout: 15000 })

await page.goto('http://localhost:5173/')
mark('ホーム表示')
await pause(2000)

const restart = page.getByRole('button', { name: '設定をやり直す（ヒアリング）' })
if (await restart.count()) {
  await restart.click()
} else {
  await page.getByRole('button', { name: 'ヒアリングを始める' }).click()
}
mark('ヒアリング開始')

await waitBot('実現したい目標はありますか')
await pause(2000)
mark('目標入力')
await typeAndSend('統計検定の合格', 110)

await waitBot('障壁となっている悪習慣')
mark('悪習慣質問+レコメンド表示')
await pause(4000)

mark('悪習慣を自由入力')
await typeAndSend('スマホいじり', 120)

await waitBot('どのような通知')
mark('通知方法の選択肢表示')
await pause(4000)
await page.getByRole('button', { name: '言葉で通知する' }).click()
mark('言葉で通知を選択')

await waitBot('どのような言葉')
await pause(2200)
mark('通知フレーズ入力')
await typeAndSend('いてこますぞ', 150)
await pause(1200)

await waitBot('他に何か悪習慣')
mark('追加質問+レコメンド表示(複数設定可の説明)')
await pause(4000)

await page.getByRole('button', { name: 'もう大丈夫' }).click()
mark('もう大丈夫を送信')

await waitBot('以下の内容で設定しました')
mark('設定サマリー表示')
await pause(4200)

await page.getByRole('button', { name: '設定完了！ホームに戻る' }).click()
await page.getByRole('button', { name: 'セッションを開始する' }).waitFor()
mark('ホームに設定カード表示(デプロイ完了)')
await pause(4500)
mark('終了')

await context.close()
await browser.close()

const webm = readdirSync(recDir).find((f) => f.endsWith('.webm'))
renameSync(join(recDir, webm), join(dir, 'hearing-mobile.webm'))
rmSync(recDir, { recursive: true, force: true })
writeFileSync(join(dir, 'hearing-mobile-marks.json'), JSON.stringify(marks, null, 2))
console.log('saved hearing-mobile.webm')
