import { chromium } from 'playwright'
import { fileURLToPath } from 'node:url'
import { dirname, join } from 'node:path'
import { readdirSync, renameSync, rmSync, writeFileSync } from 'node:fs'

const dir = dirname(fileURLToPath(import.meta.url))
const recDir = join(dir, 'rec-hearing')

const browser = await chromium.launch()
const context = await browser.newContext({
  viewport: { width: 1280, height: 720 },
  recordVideo: { dir: recDir, size: { width: 1280, height: 720 } },
})
const page = await context.newPage()

const t0 = Date.now()
const marks = []
const mark = (label) => {
  marks.push({ t: Math.round((Date.now() - t0) / 100) / 10, label })
  console.log(`${((Date.now() - t0) / 1000).toFixed(1)}s  ${label}`)
}
const pause = (ms) => page.waitForTimeout(ms)

const typeAndSend = async (text, cps = 72) => {
  const input = page.locator('input.chat-input')
  await input.click()
  await input.pressSequentially(text, { delay: cps })
  await pause(700)
  await page.getByRole('button', { name: '送信' }).click()
}
const waitBot = (text) =>
  page.locator('.bubble-bot', { hasText: text }).last().waitFor({ timeout: 15000 })

await page.goto('http://localhost:5173/')
mark('ホーム表示')
await pause(2800)

const restart = page.getByRole('button', { name: '設定をやり直す（ヒアリング）' })
if (await restart.count()) {
  await restart.click()
} else {
  await page.getByRole('button', { name: 'ヒアリングを始める' }).click()
}
mark('ヒアリング開始')

await waitBot('実現したい目標はありますか')
await pause(3200)
mark('目標入力(アバウトな文)')
await typeAndSend('今から統計検定の勉強をする。ダラダラしてたら注意して', 95)

await waitBot('障壁となっている悪習慣')
mark('悪習慣質問+レコメンド表示')
await pause(6000)

mark('悪習慣を自由入力')
await typeAndSend('スマホいじり')

await waitBot('どのような通知')
mark('通知方法の選択肢表示')
await pause(4200)
await page.getByRole('button', { name: '言葉で通知する' }).click()
mark('言葉で通知を選択')

await waitBot('どのような言葉')
await pause(2600)
mark('通知フレーズ入力')
await typeAndSend('スマホを置いて、勉強に戻ってください', 85)

await waitBot('他に何か悪習慣')
mark('追加質問+残りレコメンド表示')
await pause(5200)

await page.getByRole('button', { name: 'つい居眠りをしてしまう' }).click()
mark('レコメンドから2つ目を選択')

await waitBot('どのような通知')
await pause(2600)
await page.getByRole('button', { name: 'BGMを流す' }).click()
mark('BGMを選択')

await waitBot('どのBGM')
await pause(2600)
await page.getByRole('button', { name: 'アップテンポ' }).click()

await waitBot('他に何か悪習慣')
await pause(3000)
await page.getByRole('button', { name: 'もう大丈夫' }).click()
mark('もう大丈夫を送信')

await waitBot('以下の内容で設定しました')
mark('設定サマリー表示(デプロイ完了)')
await pause(6500)

await page.getByRole('button', { name: '設定完了！ホームに戻る' }).click()
await page.getByRole('button', { name: 'セッションを開始する' }).waitFor()
mark('ホームに設定カード表示')
await pause(5500)
mark('終了')

await context.close()
await browser.close()

const webm = readdirSync(recDir).find((f) => f.endsWith('.webm'))
renameSync(join(recDir, webm), join(dir, 'hearing-capture.webm'))
rmSync(recDir, { recursive: true, force: true })
writeFileSync(join(dir, 'hearing-capture-marks.json'), JSON.stringify(marks, null, 2))
console.log('saved hearing-capture.webm')
