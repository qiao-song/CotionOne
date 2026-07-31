<template>
  <div class="snake-game" ref="containerRef">
    <canvas ref="canvasRef" class="game-canvas"></canvas>
    <!-- Floating quotes -->
    <div
      v-for="(q, i) in floatingQuotes"
      :key="q.id"
      class="floating-quote"
      :style="{ left: q.x + 'px', top: q.y + 'px' }"
    >
      {{ q.text }}
    </div>
    <div class="game-hud">
      <div class="hud-item">🐍 长度: <strong>{{ snakeLength }}</strong></div>
      <div class="hud-item">🏆 分数: <strong>{{ score }}</strong></div>
      <div class="hud-item timer" v-if="started && !gameOver">⏱️ <strong>{{ formatTime(elapsed) }}</strong></div>
      <div class="hud-item darkness" v-if="started && !gameOver">🌑 <strong>{{ Math.floor(bgDarkness * 100) }}%</strong></div>
    </div>
    <!-- Flashbang overlay — subtle ambient layer, canvas handles all text/effects -->
    <div v-if="flashbang" class="flashbang-overlay" :class="{ active: flashbangActive }"></div>
    <div v-if="gameOver" class="game-over-overlay">
      <div class="game-over-card">
        <h2>{{ score >= 50 ? '🐉 化龙成功！' : '💀 游戏结束' }}</h2>
        <div class="final-score">
          <div class="score-row"><span>最终长度</span><span>{{ snakeLength }}</span></div>
          <div class="score-row"><span>获得点数</span><span class="pts">{{ score }}</span></div>
        </div>
        <button class="btn-restart" @click="startGame">再来一局</button>
      </div>
    </div>
    <div v-if="!started && !gameOver" class="game-over-overlay">
      <div class="game-over-card">
        <h2>🐍 蛇兜化龙记</h2>
        <p class="game-desc-text">方向键 ↑↓←→ 控制仙人兜移动<br/>吃查克拉块成长，小心写轮眼！<br/>螺旋丸可大幅增加分数<br/>写轮眼将触发伊邪那美重置进度</p>
        <button class="btn-restart" @click="startGame">开始游戏</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'

const emit = defineEmits(['earn', 'close'])

const canvasRef = ref(null)
const containerRef = ref(null)

const started = ref(false)
const gameOver = ref(false)
const snakeLength = ref(1)
const score = ref(0)
const elapsed = ref(0)
const bgDarkness = ref(0)
const floatingQuotes = ref([])
const flashbang = ref(false)
const flashbangActive = ref(false)

let canvas, ctx, gameLoopId
let snake = []
let food = { x: 0, y: 0 }
let direction = { x: 1, y: 0 }
let nextDirection = { x: 1, y: 0 }
let gridSize = 20
let speed = 120
let lastMove = 0
let startTime = 0
let audio = null

// Special items
let rasengan = null
let rasenganSpawnTimer = 0
let rasenganSpawnTime = 0  // timestamp when rasengan was spawned
let rasenganFlashPhase = 0
let sharingans = []
let sharinganSpawnTimer = 0
let quoteIdCounter = 0
let isFlashbang = false
let flashbangStartTime = 0

// Kabuto quotes
const kabutoQuotes = ['我将化身成龙！', '大蛇丸大人的梦我来实现！', '蛤~蛤蛤蛤蛤']

function initAudio() {
  try {
    audio = new Audio('https://files.freemusicarchive.org/storage-freemusicarchive-org/music/no_curator/Kevin_MacLeod/Impact/Kevin_MacLeod_-_Impact_Andante.mp3')
    audio.loop = true
    audio.volume = 0.3
  } catch { /* audio not critical */ }
}

function initCanvas() {
  canvas = canvasRef.value
  const rect = containerRef.value.getBoundingClientRect()
  const size = Math.min(rect.width - 20, rect.height - 120, 620)
  canvas.width = Math.floor(size / gridSize) * gridSize
  canvas.height = Math.floor(size / gridSize) * gridSize
  ctx = canvas.getContext('2d')
}

function getCols() { return Math.floor(canvas.width / gridSize) }
function getRows() { return Math.floor(canvas.height / gridSize) }

function placeFood() {
  const cols = getCols()
  const rows = getRows()
  let fx, fy
  do {
    fx = Math.floor(Math.random() * cols)
    fy = Math.floor(Math.random() * rows)
  } while (
    snake.some(s => s.x === fx && s.y === fy) ||
    (rasengan && fx >= rasengan.x && fx < rasengan.x + 2 && fy >= rasengan.y && fy < rasengan.y + 2) ||
    sharingans.some(s => fx >= s.x && fx < s.x + 3 && fy >= s.y && fy < s.y + 3)
  )
  food = { x: fx, y: fy }
}

function spawnRasengan() {
  const cols = getCols()
  const rows = getRows()
  let rx, ry
  do {
    rx = Math.floor(Math.random() * (cols - 1))
    ry = Math.floor(Math.random() * (rows - 1))
  } while (
    snake.some(s => s.x >= rx && s.x < rx + 2 && s.y >= ry && s.y < ry + 2) ||
    (food.x >= rx && food.x < rx + 2 && food.y >= ry && food.y < ry + 2) ||
    sharingans.some(s => !(rx + 2 <= s.x || rx >= s.x + 3 || ry + 2 <= s.y || ry >= s.y + 3))
  )
  rasengan = { x: rx, y: ry }
  rasenganSpawnTimer = 0
  rasenganSpawnTime = performance.now()
}

function spawnSharingan() {
  if (sharingans.length >= 3) return
  const cols = getCols()
  const rows = getRows()
  const head = snake[0]
  let sx, sy
  let attempts = 0
  do {
    sx = Math.floor(Math.random() * (cols - 2))
    sy = Math.floor(Math.random() * (rows - 2))
    attempts++
  } while (
    attempts < 100 &&
    (Math.abs(sx - head.x) < 5 && Math.abs(sy - head.y) < 5)
  )
  if (attempts < 100 || sharingans.length === 0) {
    sharingans.push({ x: sx, y: sy })
  }
  sharinganSpawnTimer = 0
}

function repositionSharingans() {
  const cols = getCols()
  const rows = getRows()
  const head = snake[0]
  for (const s of sharingans) {
    let nsx, nsy, attempts = 0
    do {
      nsx = Math.floor(Math.random() * (cols - 2))
      nsy = Math.floor(Math.random() * (rows - 2))
      attempts++
    } while (attempts < 50 && Math.abs(nsx - head.x) < 5 && Math.abs(nsy - head.y) < 5)
    s.x = nsx
    s.y = nsy
  }
}

function addFloatingQuote(text) {
  const head = snake[0]
  const headScreenX = head.x * gridSize + gridSize / 2
  const headScreenY = head.y * gridSize
  const id = quoteIdCounter++
  floatingQuotes.value.push({ id, text, x: headScreenX, y: headScreenY })
  setTimeout(() => {
    floatingQuotes.value = floatingQuotes.value.filter(q => q.id !== id)
  }, 1500)
}

function startGame() {
  initCanvas()
  const cols = getCols()
  const rows = getRows()
  const midX = Math.floor(cols / 2)
  const midY = Math.floor(rows / 2)
  snake = [
    { x: midX, y: midY },
    { x: midX - 1, y: midY },
    { x: midX - 2, y: midY }
  ]
  direction = { x: 1, y: 0 }
  nextDirection = { x: 1, y: 0 }
  speed = 120
  score.value = 0
  bgDarkness.value = 0
  snakeLength.value = snake.length
  elapsed.value = 0
  gameOver.value = false
  started.value = true
  flashbang.value = false
  flashbangActive.value = false
  isFlashbang = false
  floatingQuotes.value = []

  rasengan = null
  rasenganSpawnTimer = 0
  rasenganSpawnTime = 0
  sharingans = []
  sharinganSpawnTimer = 0

  startTime = performance.now()
  placeFood()

  if (!audio) initAudio()
  if (audio) {
    audio.currentTime = 0
    audio.play().catch(() => {})
  }

  lastMove = performance.now()
  cancelAnimationFrame(gameLoopId)
  gameLoop(performance.now())
}

function gameLoop(timestamp) {
  if (!started.value || gameOver.value) return

  if (isFlashbang) {
    drawFlashbang(timestamp)
    gameLoopId = requestAnimationFrame(gameLoop)
    return
  }

  const dt = timestamp - startTime
  elapsed.value = Math.floor(dt / 1000)

  // Spawn timers
  rasenganSpawnTimer += 16
  sharinganSpawnTimer += 16

  if (!rasengan && rasenganSpawnTimer >= 10000) {
    spawnRasengan()
  }

  if (sharinganSpawnTimer >= 20000) {
    spawnSharingan()
  }

  // Reposition sharingans every 8 seconds
  if (Math.floor(dt / 8000) > Math.floor((dt - 16) / 8000) && sharingans.length > 0) {
    repositionSharingans()
  }

  // Rasengan auto-disappear after 5 seconds
  if (rasengan && timestamp - rasenganSpawnTime > 5000) {
    rasengan = null
    rasenganSpawnTimer = 0
  }

  if (timestamp - lastMove > speed) {
    direction = { ...nextDirection }
    const head = snake[0]
    const newHead = { x: head.x + direction.x, y: head.y + direction.y }

    const cols = getCols()
    const rows = getRows()

    // Wall collision
    if (newHead.x < 0 || newHead.x >= cols || newHead.y < 0 || newHead.y >= rows) {
      endGame()
      return
    }

    // Self collision
    if (snake.some(s => s.x === newHead.x && s.y === newHead.y)) {
      endGame()
      return
    }

    // Check sharingan collision (3x3 area)
    for (let si = sharingans.length - 1; si >= 0; si--) {
      const s = sharingans[si]
      if (newHead.x >= s.x && newHead.x < s.x + 3 && newHead.y >= s.y && newHead.y < s.y + 3) {
        triggerFlashbang()
        // Continue the game loop for flashbang animation
        gameLoopId = requestAnimationFrame(gameLoop)
        return
      }
    }

    snake.unshift(newHead)

    // Check rasengan (2x2 area)
    if (rasengan && newHead.x >= rasengan.x && newHead.x < rasengan.x + 2 && newHead.y >= rasengan.y && newHead.y < rasengan.y + 2) {
      const bonus = Math.floor(score.value * 0.5)
      score.value += bonus
      addFloatingQuote('你的查克拉我就收下了')
      rasengan = null
      rasenganSpawnTimer = 0
    }

    // Eat food
    if (newHead.x === food.x && newHead.y === food.y) {
      const points = snake.length
      score.value += points
      snakeLength.value = snake.length
      addFloatingQuote(kabutoQuotes[Math.floor(Math.random() * kabutoQuotes.length)])
      bgDarkness.value = Math.min(0.85, bgDarkness.value + 0.04)
      placeFood()
      speed = Math.max(50, speed - 2)
    } else {
      snake.pop()
    }

    snakeLength.value = snake.length
    lastMove = timestamp
  }

  draw(timestamp)
  gameLoopId = requestAnimationFrame(gameLoop)
}

function triggerFlashbang() {
  flashbangStartTime = performance.now()
  isFlashbang = true
  flashbang.value = true
  flashbangActive.value = false
  if (audio) audio.pause()
  // Phase timing is handled inside drawFlashbang()
}

function drawFlashbang(timestamp) {
  if (!ctx) return
  const w = canvas.width
  const h = canvas.height

  const elapsed = timestamp - flashbangStartTime

  // Phase 0: 0–2000ms — game frozen, draw frozen state with subtle darkening
  drawGameState(timestamp)

  if (elapsed < 2000) {
    // Just a subtle vignette during the 2-second freeze
    const freezeProgress = Math.min(1, elapsed / 2000)
    const vignette = ctx.createRadialGradient(w / 2, h / 2, w * 0.5, w / 2, h / 2, w * 0.85)
    vignette.addColorStop(0, 'rgba(0,0,0,0)')
    vignette.addColorStop(1, `rgba(0,0,0,${0.3 * freezeProgress})`)
    ctx.fillStyle = vignette
    ctx.fillRect(0, 0, w, h)

    // Pulsing sharingan pattern at center (hint of what's coming)
    const patternAlpha = 0.1 + 0.1 * Math.sin(timestamp * 0.01)
    ctx.fillStyle = `rgba(239, 68, 68, ${patternAlpha})`
    ctx.beginPath()
    ctx.arc(w / 2, h / 2, 10 + 5 * Math.sin(timestamp * 0.015), 0, Math.PI * 2)
    ctx.fill()

    // Activate the CSS overlay at end of freeze
    if (elapsed >= 1900 && !flashbangActive.value) {
      flashbangActive.value = true
    }
    return
  }

  // Phase 1+: Activate CSS overlay
  if (!flashbangActive.value) {
    flashbangActive.value = true
  }

  // Phase 1: 2000–2800ms — gradient white screen build-up
  const whiteElapsed = elapsed - 2000
  const whiteProgress = Math.min(1, whiteElapsed / 800)
  const gradient = ctx.createLinearGradient(0, 0, 0, h)
  gradient.addColorStop(0, `rgba(255, 255, 255, ${whiteProgress * 0.95})`)
  gradient.addColorStop(0.5, `rgba(255, 255, 255, ${whiteProgress})`)
  gradient.addColorStop(1, `rgba(255, 255, 255, ${whiteProgress * 0.9})`)
  ctx.fillStyle = gradient
  ctx.fillRect(0, 0, w, h)

  // Phase 2: 2100–3400ms — "你是无法破解这个术的" with water ripple (staggered after white)
  if (whiteElapsed >= 100 && whiteElapsed < 1400) {
    const textElapsed = whiteElapsed - 100
    const textProgress = Math.min(1, textElapsed / 400)  // fade in over 400ms

    // Ripple effect: scale up and fade out
    const rippleAlpha = Math.max(0, 1 - (textElapsed - 400) / 900) * textProgress
    const rippleScale = 1 + (textElapsed - 300) * 0.003  // gradual scale up
    const blurAmount = Math.max(0, (textElapsed - 300) * 0.015)  // increasing blur like water

    ctx.save()
    ctx.filter = `blur(${blurAmount}px)`
    ctx.fillStyle = `rgba(20, 20, 30, ${rippleAlpha})`
    ctx.font = `bold ${Math.floor(22 * rippleScale)}px sans-serif`
    ctx.textAlign = 'center'
    ctx.fillText('你是无法破解这个术的', w / 2, h / 2 - 30)
    ctx.restore()

    // Ripple rings around the text (ellipse for water wave effect)
    const ringCount = 3
    for (let r = 0; r < ringCount; r++) {
      const ringDelay = r * 150
      const ringElapsed = Math.max(0, textElapsed - ringDelay)
      if (ringElapsed < 1000) {
        const ringProgress = ringElapsed / 1000
        const ringAlpha = (1 - ringProgress) * 0.35 * textProgress
        const ringRadius = 50 + ringProgress * 100
        ctx.strokeStyle = `rgba(139, 92, 246, ${ringAlpha})`
        ctx.lineWidth = 2 - ringProgress * 1.5
        ctx.beginPath()
        ctx.ellipse(w / 2, h / 2 - 30, ringRadius, ringRadius * 0.35, 0, 0, Math.PI * 2)
        ctx.stroke()
      }
    }
    ctx.textAlign = 'start'
  }

  // Phase 3: 2500–4200ms — "伊邪那美" + "时间回溯" (staggered after first text)
  if (whiteElapsed >= 500 && whiteElapsed < 2200) {
    const phase3Elapsed = whiteElapsed - 500
    const p3Progress = Math.min(1, phase3Elapsed / 400)
    const p3Pulse = 0.9 + 0.1 * Math.sin(timestamp * 0.005)

    // Main title: "伊邪那美"
    ctx.fillStyle = `rgba(20, 20, 30, ${p3Progress * p3Pulse})`
    ctx.font = 'bold 38px sans-serif'
    ctx.fillText('伊邪那美', w / 2, h / 2 + 20)

    // Subtitle: "时间回溯" — staggered by 250ms
    const subProgress = Math.min(1, Math.max(0, (phase3Elapsed - 250)) / 400)
    ctx.fillStyle = `rgba(124, 58, 237, ${subProgress * p3Pulse})`
    ctx.font = 'bold 20px sans-serif'
    ctx.fillText('时间回溯', w / 2, h / 2 + 55)

    ctx.textAlign = 'start'

    // Reset at end of phase 3
    if (whiteElapsed >= 2100) {
      resetAfterIzanami()
    }
  }
}

function resetAfterIzanami() {
  const cols = getCols()
  const rows = getRows()
  const midX = Math.floor(cols / 2)
  const midY = Math.floor(rows / 2)

  snake = [
    { x: midX, y: midY },
    { x: midX - 1, y: midY },
    { x: midX - 2, y: midY }
  ]
  direction = { x: 1, y: 0 }
  nextDirection = { x: 1, y: 0 }
  speed = 120
  score.value = 0
  bgDarkness.value = 0
  snakeLength.value = snake.length

  rasengan = null
  rasenganSpawnTimer = 0
  rasenganSpawnTime = 0
  sharingans = []
  sharinganSpawnTimer = 0

  isFlashbang = false
  flashbang.value = false
  flashbangActive.value = false

  if (audio) {
    audio.currentTime = 0
    audio.play().catch(() => {})
  }

  placeFood()
  lastMove = performance.now()
  // Don't call requestAnimationFrame here — the existing gameLoop will continue
  // after drawFlashbang returns, since isFlashbang is now false
}

function drawGameState(timestamp) {
  if (!ctx) return
  const w = canvas.width
  const h = canvas.height
  const d = bgDarkness.value

  // Background - Ryuchi Cave with darkness progression
  // Start light, get darker as player eats more
  const bg = ctx.createLinearGradient(0, 0, 0, h)
  const r0 = Math.floor(80 - d * 70)
  const g0 = Math.floor(70 - d * 60)
  const b0 = Math.floor(100 - d * 85)
  const r1 = Math.floor(50 - d * 38)
  const g1 = Math.floor(40 - d * 30)
  const b1 = Math.floor(80 - d * 62)
  const r2 = Math.floor(30 - d * 20)
  const g2 = Math.floor(22 - d * 13)
  const b2 = Math.floor(55 - d * 36)
  const r3 = Math.floor(18 + d * 7)
  const g3 = Math.floor(12 + d * 8)
  const b3 = Math.floor(30 - d * 9)

  bg.addColorStop(0, `rgb(${r0},${g0},${b0})`)
  bg.addColorStop(0.3, `rgb(${r1},${g1},${b1})`)
  bg.addColorStop(0.7, `rgb(${r2},${g2},${b2})`)
  bg.addColorStop(1, `rgb(${r3},${g3},${b3})`)
  ctx.fillStyle = bg
  ctx.fillRect(0, 0, w, h)

  // Cave wall texture (stalactites) - opacity increases with darkness
  const caveAlpha = 0.15 + d * 0.5
  ctx.fillStyle = `rgba(26, 16, 40, ${caveAlpha})`
  for (let i = 0; i < 12; i++) {
    const cx = (i * 113 + 30) % w
    const ch = 20 + (i * 37) % 60
    ctx.beginPath()
    ctx.moveTo(cx - 15, 0)
    ctx.lineTo(cx, ch)
    ctx.lineTo(cx + 15, 0)
    ctx.fill()
  }

  // Cave floor
  const floorAlpha = 0.1 + d * 0.45
  ctx.fillStyle = `rgba(21, 14, 34, ${floorAlpha})`
  ctx.fillRect(0, h - 15, w, 15)
  for (let i = 0; i < 14; i++) {
    const cx = (i * 97 + 50) % w
    const ch = 8 + (i * 23) % 18
    ctx.beginPath()
    ctx.moveTo(cx - 12, h - 15)
    ctx.lineTo(cx, h - 15 - ch)
    ctx.lineTo(cx + 12, h - 15)
    ctx.fill()
  }

  // Glowing cave crystals - brighter as it gets darker
  const crystalAlpha = 0.1 + d * 0.3
  for (let i = 0; i < 8; i++) {
    const gx = (i * 173 + 80) % w
    const gy = (i * 127 + 40) % (h - 60)
    ctx.fillStyle = `rgba(139, 92, 246, ${crystalAlpha})`
    ctx.beginPath()
    ctx.arc(gx, gy, 4 + (i % 3) * 2, 0, Math.PI * 2)
    ctx.fill()
    ctx.fillStyle = `rgba(139, 92, 246, ${crystalAlpha * 2})`
    ctx.beginPath()
    ctx.arc(gx, gy, 1.5 + (i % 2), 0, Math.PI * 2)
    ctx.fill()
  }

  // Grid lines (faint)
  ctx.strokeStyle = 'rgba(255,255,255,0.02)'
  ctx.lineWidth = 0.5
  for (let x = 0; x < w; x += gridSize) {
    ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, h); ctx.stroke()
  }
  for (let y = 0; y < h; y += gridSize) {
    ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(w, y); ctx.stroke()
  }

  // Food - Chakra Block
  const fx = food.x * gridSize
  const fy = food.y * gridSize
  const fcx = fx + gridSize / 2
  const fcy = fy + gridSize / 2
  ctx.shadowColor = '#60A5FA'
  ctx.shadowBlur = 14
  ctx.fillStyle = '#3B82F6'
  ctx.beginPath()
  ctx.roundRect(fx + 3, fy + 3, gridSize - 6, gridSize - 6, 3)
  ctx.fill()
  ctx.shadowBlur = 0
  ctx.fillStyle = '#93C5FD'
  ctx.beginPath()
  ctx.roundRect(fx + 6, fy + 6, gridSize - 12, gridSize - 12, 2)
  ctx.fill()
  ctx.fillStyle = '#fff'
  ctx.beginPath()
  ctx.arc(fcx, fcy, 2.5, 0, Math.PI * 2)
  ctx.fill()

  // Rasengan (2x2 grid, blinking)
  if (rasengan) {
    const now = timestamp || performance.now()
    // Blinking: cycle every 400ms
    const blinkAlpha = 0.4 + 0.6 * Math.abs(Math.sin(now * 0.008))
    const spawnAge = (now - rasenganSpawnTime) / 1000
    // Urgent blink in last 1.5 seconds
    const urgentBlink = spawnAge > 3.5 ? (0.2 + 0.8 * Math.abs(Math.sin(now * 0.02))) : 1
    const alpha = blinkAlpha * urgentBlink

    for (let dx = 0; dx < 2; dx++) {
      for (let dy = 0; dy < 2; dy++) {
        const rx = (rasengan.x + dx) * gridSize
        const ry = (rasengan.y + dy) * gridSize
        const rcx = rx + gridSize / 2
        const rcy = ry + gridSize / 2

        ctx.globalAlpha = alpha
        ctx.shadowColor = '#3B82F6'
        ctx.shadowBlur = 20
        const pulse = 0.7 + 0.3 * Math.sin(now * 0.005)
        ctx.fillStyle = '#2563EB'
        ctx.beginPath()
        ctx.arc(rcx, rcy, gridSize / 2 - 2, 0, Math.PI * 2)
        ctx.fill()

        // Spiral lines
        ctx.strokeStyle = '#BFDBFE'
        ctx.lineWidth = 1.5
        for (let a = 0; a < 4; a++) {
          ctx.beginPath()
          const angle = a * Math.PI / 2 + now * 0.003
          ctx.arc(rcx, rcy, 3, angle, angle + Math.PI * 0.4)
          ctx.stroke()
        }

        // Center
        ctx.fillStyle = '#EFF6FF'
        ctx.beginPath()
        ctx.arc(rcx, rcy, 3 * pulse, 0, Math.PI * 2)
        ctx.fill()
        ctx.shadowBlur = 0
      }
    }
    ctx.globalAlpha = 1
  }

  // Sharingan (3x3 unified Mangekyo)
  for (const s of sharingans) {
    const now = timestamp || performance.now()
    const scx = (s.x + 1.5) * gridSize
    const scy = (s.y + 1.5) * gridSize
    const outerR = gridSize * 1.35

    // Outer glow
    ctx.shadowColor = '#EF4444'
    ctx.shadowBlur = 25
    ctx.fillStyle = '#1A0000'
    ctx.beginPath()
    ctx.arc(scx, scy, outerR, 0, Math.PI * 2)
    ctx.fill()
    ctx.shadowBlur = 0

    // Red iris background
    const irisGrad = ctx.createRadialGradient(scx - 2, scy - 2, outerR * 0.1, scx, scy, outerR)
    irisGrad.addColorStop(0, '#EF4444')
    irisGrad.addColorStop(0.5, '#DC2626')
    irisGrad.addColorStop(1, '#7F1D1D')
    ctx.fillStyle = irisGrad
    ctx.beginPath()
    ctx.arc(scx, scy, outerR - 2, 0, Math.PI * 2)
    ctx.fill()

    // Outer black ring
    ctx.strokeStyle = '#0A0000'
    ctx.lineWidth = 3
    ctx.beginPath()
    ctx.arc(scx, scy, outerR - 3, 0, Math.PI * 2)
    ctx.stroke()

    // Middle ring
    ctx.strokeStyle = '#1A0000'
    ctx.lineWidth = 1.5
    ctx.beginPath()
    ctx.arc(scx, scy, outerR * 0.55, 0, Math.PI * 2)
    ctx.stroke()

    // Inner ring
    ctx.strokeStyle = '#1A0000'
    ctx.lineWidth = 1
    ctx.beginPath()
    ctx.arc(scx, scy, outerR * 0.3, 0, Math.PI * 2)
    ctx.stroke()

    // 3 Tomoe (Mangekyo blades) rotating
    const bladeAngle = now * 0.002
    ctx.fillStyle = '#0A0000'
    for (let t = 0; t < 3; t++) {
      const angle = bladeAngle + t * Math.PI * 2 / 3
      const tx = scx + Math.cos(angle) * outerR * 0.42
      const ty = scy + Math.sin(angle) * outerR * 0.42
      ctx.beginPath()
      ctx.arc(tx, ty, outerR * 0.13, 0, Math.PI * 2)
      ctx.fill()
      // Small connecting line toward center
      ctx.strokeStyle = '#0A0000'
      ctx.lineWidth = 1.5
      ctx.beginPath()
      ctx.moveTo(tx, ty)
      ctx.lineTo(scx + Math.cos(angle) * outerR * 0.15, scy + Math.sin(angle) * outerR * 0.15)
      ctx.stroke()
    }

    // Center pupil
    const pupilGrad = ctx.createRadialGradient(scx, scy, 0, scx, scy, outerR * 0.1)
    pupilGrad.addColorStop(0, '#0A0000')
    pupilGrad.addColorStop(1, '#DC2626')
    ctx.fillStyle = pupilGrad
    ctx.beginPath()
    ctx.arc(scx, scy, outerR * 0.1, 0, Math.PI * 2)
    ctx.fill()
  }

  // Snake body
  snake.forEach((seg, i) => {
    const sx = seg.x * gridSize
    const sy = seg.y * gridSize

    if (i === 0) {
      drawKabutoHead(sx, sy, gridSize)
    } else {
      const t = i / Math.max(1, snake.length - 1)
      const r = Math.floor(180 + 75 * (1 - t))
      const g = Math.floor(160 + 80 * (1 - t))
      const b = Math.floor(200 + 55 * t)
      ctx.fillStyle = `rgb(${r},${g},${b})`

      const padding = 2
      ctx.beginPath()
      ctx.roundRect(sx + padding, sy + padding, gridSize - padding * 2, gridSize - padding * 2, 4)
      ctx.fill()

      ctx.fillStyle = `rgba(139, 92, 246, ${0.15 + 0.1 * (1 - t)})`
      ctx.beginPath()
      ctx.roundRect(sx + 5, sy + 5, gridSize - 10, gridSize - 10, 3)
      ctx.fill()
    }
  })
}

function drawKabutoHead(x, y, size) {
  const cx = x + size / 2
  const cy = y + size / 2
  const r = size / 2 - 1

  ctx.shadowColor = '#8B5CF6'
  ctx.shadowBlur = 6

  ctx.fillStyle = '#E8E0F0'
  ctx.beginPath()
  ctx.arc(cx, cy, r, 0, Math.PI * 2)
  ctx.fill()
  ctx.shadowBlur = 0

  ctx.fillStyle = '#7C3AED'
  ctx.beginPath()
  ctx.arc(cx - 3, cy - 2, 3.5, 0, Math.PI * 2)
  ctx.fill()
  ctx.fillStyle = '#8B5CF6'
  ctx.beginPath()
  ctx.arc(cx + 3, cy - 3, 2.5, 0, Math.PI * 2)
  ctx.fill()

  ctx.strokeStyle = '#C4B5FD'
  ctx.lineWidth = 2
  ctx.beginPath()
  ctx.moveTo(cx - 3, cy - r + 2)
  ctx.quadraticCurveTo(cx - 6, cy - r - 4, cx - 2, cy - r - 6)
  ctx.stroke()
  ctx.beginPath()
  ctx.moveTo(cx + 3, cy - r + 2)
  ctx.quadraticCurveTo(cx + 6, cy - r - 4, cx + 2, cy - r - 6)
  ctx.stroke()

  let eye1x, eye1y, eye2x, eye2y
  if (direction.x === 1) {
    eye1x = cx + 3; eye1y = cy - 3
    eye2x = cx + 3; eye2y = cy + 3
  } else if (direction.x === -1) {
    eye1x = cx - 3; eye1y = cy - 3
    eye2x = cx - 3; eye2y = cy + 3
  } else if (direction.y === -1) {
    eye1x = cx - 3; eye1y = cy - 3
    eye2x = cx + 3; eye2y = cy - 3
  } else {
    eye1x = cx - 3; eye1y = cy + 3
    eye2x = cx + 3; eye2y = cy + 3
  }

  ctx.fillStyle = '#FDE68A'
  ctx.beginPath()
  ctx.arc(eye1x, eye1y, 3.5, 0, Math.PI * 2)
  ctx.fill()
  ctx.beginPath()
  ctx.arc(eye2x, eye2y, 3.5, 0, Math.PI * 2)
  ctx.fill()

  ctx.fillStyle = '#1C1917'
  ctx.fillRect(eye1x - 0.8, eye1y - 3, 1.6, 6)
  ctx.fillRect(eye2x - 0.8, eye2y - 3, 1.6, 6)

  ctx.fillStyle = 'rgba(124, 58, 237, 0.4)'
  ctx.beginPath()
  ctx.arc(eye1x, eye1y + 2, 4, 0, Math.PI * 2)
  ctx.fill()
  ctx.beginPath()
  ctx.arc(eye2x, eye2y + 2, 4, 0, Math.PI * 2)
  ctx.fill()

  ctx.strokeStyle = '#A78BFA'
  ctx.lineWidth = 1
  ctx.beginPath()
  if (direction.x === 1) {
    ctx.arc(cx + 2, cy + 1, 3, 0, Math.PI)
  } else if (direction.x === -1) {
    ctx.arc(cx - 2, cy + 1, 3, 0, Math.PI)
  } else if (direction.y === -1) {
    ctx.arc(cx, cy - 2, 3, Math.PI, 0)
  } else {
    ctx.arc(cx, cy + 2, 3, 0, Math.PI)
  }
  ctx.stroke()

  ctx.fillStyle = 'rgba(196, 181, 253, 0.5)'
  ctx.beginPath()
  if (direction.x === 1) {
    ctx.moveTo(cx - 2, cy - r)
    ctx.quadraticCurveTo(cx - 8, cy, cx - 2, cy + r)
  } else if (direction.x === -1) {
    ctx.moveTo(cx + 2, cy - r)
    ctx.quadraticCurveTo(cx + 8, cy, cx + 2, cy + r)
  } else if (direction.y === -1) {
    ctx.moveTo(cx - r, cy + 2)
    ctx.quadraticCurveTo(cx, cy + 8, cx + r, cy + 2)
  } else {
    ctx.moveTo(cx - r, cy - 2)
    ctx.quadraticCurveTo(cx, cy - 8, cx + r, cy - 2)
  }
  ctx.closePath()
  ctx.fill()
}

function draw(timestamp) {
  drawGameState(timestamp)
}

function endGame() {
  gameOver.value = true
  started.value = false
  cancelAnimationFrame(gameLoopId)
  if (audio) audio.pause()
  emit('earn', score.value)
}

function formatTime(sec) {
  const m = Math.floor(sec / 60)
  const s = sec % 60
  return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`
}

function handleKey(e) {
  if (!started.value || gameOver.value || isFlashbang) return
  const key = e.key
  e.preventDefault()
  if ((key === 'ArrowUp' || key === 'w' || key === 'W') && direction.y !== 1) {
    nextDirection = { x: 0, y: -1 }
  } else if ((key === 'ArrowDown' || key === 's' || key === 'S') && direction.y !== -1) {
    nextDirection = { x: 0, y: 1 }
  } else if ((key === 'ArrowLeft' || key === 'a' || key === 'A') && direction.x !== 1) {
    nextDirection = { x: -1, y: 0 }
  } else if ((key === 'ArrowRight' || key === 'd' || key === 'D') && direction.x !== -1) {
    nextDirection = { x: 1, y: 0 }
  }
}

onMounted(() => {
  window.addEventListener('keydown', handleKey)
  initAudio()
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleKey)
  cancelAnimationFrame(gameLoopId)
  if (audio) {
    audio.pause()
    audio = null
  }
})
</script>

<style scoped>
.snake-game {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  position: relative;
  overflow: hidden;
}

.game-canvas {
  border-radius: 8px;
  box-shadow: 0 0 40px rgba(139, 92, 246, 0.2);
}

.game-hud {
  display: flex;
  gap: 24px;
  margin-top: 12px;
}

.hud-item {
  font-size: 14px;
  color: #94A3B8;
}

.hud-item strong {
  color: #C4B5FD;
  font-size: 16px;
}

.hud-item.timer strong {
  color: #FBBF24;
}

.hud-item.darkness strong {
  color: #8B5CF6;
}

/* Floating quotes */
.floating-quote {
  position: absolute;
  font-size: 13px;
  font-weight: 700;
  color: #C4B5FD;
  text-shadow: 0 0 8px rgba(139, 92, 246, 0.6);
  pointer-events: none;
  white-space: nowrap;
  animation: floatUp 1.5s ease-out forwards;
  z-index: 15;
}

@keyframes floatUp {
  0% { opacity: 1; transform: translateY(0) scale(0.6); }
  20% { opacity: 1; transform: translateY(-15px) scale(1.1); }
  100% { opacity: 0; transform: translateY(-60px) scale(0.8); }
}

/* Flashbang — ambient layer, canvas handles all text/effects */
.flashbang-overlay {
  position: absolute;
  inset: 0;
  pointer-events: none;
  z-index: 30;
  transition: background 0.8s ease-in;
  background: transparent;
}

.flashbang-overlay.active {
  background: radial-gradient(ellipse at center, rgba(255,255,255,0.15) 0%, rgba(255,255,255,0.05) 40%, rgba(0,0,0,0.3) 100%);
}

.game-over-overlay {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(10, 8, 16, 0.94);
  backdrop-filter: blur(8px);
  z-index: 20;
}

.game-over-card {
  text-align: center;
  padding: 40px;
  background: rgba(139, 92, 246, 0.08);
  border: 1px solid rgba(139, 92, 246, 0.2);
  border-radius: 20px;
  max-width: 360px;
  width: 90%;
}

.game-over-card h2 {
  font-size: 28px;
  color: #A78BFA;
  margin-bottom: 20px;
}

.game-desc-text {
  color: #94A3B8;
  font-size: 14px;
  line-height: 1.8;
  margin-bottom: 24px;
}

.final-score {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 24px;
  padding: 16px;
  background: rgba(139, 92, 246, 0.08);
  border-radius: 12px;
}

.score-row {
  display: flex;
  justify-content: space-between;
  font-size: 15px;
  color: #94A3B8;
}

.score-row .pts {
  color: #FBBF24;
  font-weight: 700;
}

.btn-restart {
  min-width: 160px;
  padding: 12px 32px;
  border: none;
  border-radius: 24px;
  background: linear-gradient(135deg, #7C3AED, #8B5CF6);
  color: #fff;
  font-size: 16px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-restart:hover {
  background: linear-gradient(135deg, #8B5CF6, #A78BFA);
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(139, 92, 246, 0.4);
}
</style>
