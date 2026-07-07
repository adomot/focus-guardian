import { chromium } from 'playwright'
import { fileURLToPath } from 'node:url'
import { dirname, join } from 'node:path'
import { readdirSync, renameSync, writeFileSync } from 'node:fs'

const dir = dirname(fileURLToPath(import.meta.url))
const outDir = join(dir, 'demo-rec')
const camPath = join(dir, 'cam.y4m')

const WIDTH = 960
const HEIGHT = 720

const browser = await chromium.launch({
  args: [
    '--use-fake-device-for-media-stream',
    `--use-file-for-fake-video-capture=${camPath}`,
    '--use-fake-ui-for-media-stream',
  ],
})
const context = await browser.newContext({
  viewport: { width: WIDTH, height: HEIGHT },
  recordVideo: { dir: outDir, size: { width: WIDTH, height: HEIGHT } },
  permissions: ['camera'],
})

// フェイク判定エージェント用: JPEG 先頭 100 バイト内に HABIT マーカーを差し込む
await context.addInitScript(() => {
  const orig = HTMLCanvasElement.prototype.toBlob
  HTMLCanvasElement.prototype.toBlob = function (cb, type, quality) {
    orig.call(
      this,
      (blob) => {
        const marker = window.__frameMarker
        if (!marker || !blob) {
          cb(blob)
          return
        }
        const bytes = new TextEncoder().encode(`HABIT:${marker}:`)
        Promise.all([blob.slice(0, 20).arrayBuffer(), blob.slice(20).arrayBuffer()]).then(
          ([head, rest]) => cb(new Blob([head, bytes, rest], { type: blob.type })),
        )
      },
      type,
      quality,
    )
  }
})

const page = await context.newPage()
const t0 = Date.now()
const marks = []
const mark = (label) => {
  marks.push({ t: Math.round((Date.now() - t0) / 100) / 10, label })
  console.log(`mark ${label} @ ${(Date.now() - t0) / 1000}s`)
}

const typeAndSend = async (text) => {
  const input = page.locator('input.chat-input')
  await input.click()
  await input.pressSequentially(text, { delay: 45 })
  await page.waitForTimeout(350)
  await page.getByRole('button', { name: '送信' }).click()
}

const waitBot = async (text) => {
  await page.locator('.bubble-bot', { hasText: text }).last().waitFor({ timeout: 15000 })
  await page.waitForTimeout(800)
}

await page.goto('http://localhost:5173/?interval=3')
mark('home')
await page.waitForTimeout(2600)

// ヒアリング開始 (既存設定の有無どちらでも動くように)
const restart = page.getByRole('button', { name: '設定をやり直す（ヒアリング）' })
const fresh = page.getByRole('button', { name: 'ヒアリングを始める' })
if (await restart.count()) {
  await restart.click()
} else {
  await fresh.click()
}
mark('hearing')

await waitBot('実現したい目標はありますか')
await typeAndSend('毎日2時間、個人開発に集中する')

await waitBot('障壁となっている悪習慣')
await typeAndSend('ついスマホをいじってしまう')

await waitBot('どのような通知をしましょうか')
await page.getByRole('button', { name: '言葉で通知する' }).click()

await waitBot('どのような言葉で通知しましょう')
await typeAndSend('スマホを置け！今すぐ作業に戻る！')

await waitBot('他に何か悪習慣はありますか')
await typeAndSend('居眠り')

await waitBot('どのような通知をしましょうか')
await page.getByRole('button', { name: 'BGMを流す' }).click()

await waitBot('どのBGMが良いでしょうか')
await page.getByRole('button', { name: 'アップテンポ' }).click()

await waitBot('他に何か悪習慣はありますか')
await page.getByRole('button', { name: 'もう大丈夫' }).click()

await waitBot('以下の内容で設定しました')
mark('hearing_done')
await page.waitForTimeout(2200)
await page.getByRole('button', { name: '設定完了！ホームに戻る' }).click()
mark('home_config')

// 設定カードを見せてからセッション開始
await page.getByRole('button', { name: 'セッションを開始する' }).waitFor()
await page.waitForTimeout(3000)
await page.getByRole('button', { name: 'セッションを開始する' }).click()
const tCam = Date.now() // 偽カメラ映像はこの直後から再生される
mark('session')

const untilCam = async (sec) => {
  const remain = tCam + sec * 1000 - Date.now()
  if (remain > 0) {
    await page.waitForTimeout(remain)
  }
}
const setMarker = (value) =>
  page.evaluate((v) => {
    window.__frameMarker = v
  }, value)

// 集中中の判定を見せる (カメラ映像: 0-8s 作業中)
await page.locator('.state-focused').waitFor({ timeout: 15000 })
mark('focused')

// カメラ映像 8-14s: スマホいじり → habit_1 (音声通知)
await untilCam(8.5)
await setMarker('habit_1')
await page.locator('.state-habit').waitFor({ timeout: 15000 })
mark('detect_phone')
await untilCam(13.6)
await setMarker(null)
await page.locator('.state-focused').waitFor({ timeout: 15000 })
mark('refocus1')

// カメラ映像 17-23s: 居眠り → habit_2 (BGM 通知)
await untilCam(17.5)
await setMarker('habit_2')
await page.locator('.state-habit').waitFor({ timeout: 15000 })
mark('detect_sleep')
await page.locator('.bgm-bar').waitFor({ timeout: 15000 })
mark('bgm_on')
await untilCam(22.6)
await setMarker(null)
await page.locator('.state-focused').waitFor({ timeout: 15000 })
mark('refocus2')
await page.waitForTimeout(1200)

const stopBgm = page.locator('.bgm-bar button')
if (await stopBgm.count()) {
  await stopBgm.click()
  mark('bgm_stop')
}
await page.waitForTimeout(1500)

await page.getByRole('button', { name: 'セッションを終了する' }).click()
await page.locator('h1', { hasText: 'セッションサマリー' }).waitFor({ timeout: 15000 })
mark('summary')
await page.waitForTimeout(4500)
mark('end')

await context.close()
await browser.close()

const webm = readdirSync(outDir).find((f) => f.endsWith('.webm'))
renameSync(join(outDir, webm), join(dir, 'demo-raw.webm'))
writeFileSync(join(dir, 'marks.json'), JSON.stringify(marks, null, 2))
console.log('saved demo-raw.webm')
