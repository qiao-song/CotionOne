<template>
  <div class="breakout-game" ref="containerRef">
    <canvas ref="canvasRef" class="game-canvas" @mousemove="handleMouseMove" @touchmove="handleTouchMove"></canvas>
    <div class="game-hud">
      <div class="hud-item">🧱 剩余: <strong>{{ blocksRemaining }}</strong></div>
      <div class="hud-item">🎾 小球: <strong>{{ ballCount }}</strong></div>
      <div class="hud-item">🏆 点数: <strong>{{ score }}</strong></div>
      <div class="hud-item">🔥 连击: <strong>x{{ combo }}</strong></div>
    </div>
    <div v-if="gameOver" class="game-over-overlay">
      <div class="game-over-card">
        <h2>{{ blocksRemaining === 0 ? '🎉 守护成功！' : '💥 木叶村失守' }}</h2>
        <div class="final-score">
          <div class="score-row"><span>击碎方块</span><span>{{ initialBlocks - blocksRemaining }}</span></div>
          <div class="score-row"><span>获得点数</span><span class="pts">{{ score }}</span></div>
        </div>
        <button class="btn-restart" @click="startGame">再来一局</button>
      </div>
    </div>
    <div v-if="!started && !gameOver" class="game-over-overlay">
      <div class="game-over-card">
        <h2>🍃 守护木叶村</h2>
        <p class="game-desc-text">鼠标左右移动控制下方挡板<br/>用查克拉球击碎所有来袭方块<br/>击碎方块可获得额外小球和点数！<br/>小球越多速度越快，挑战极限！</p>
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
const blocksRemaining = ref(0)
const ballCount = ref(1)
const score = ref(0)
const combo = ref(1)
const initialBlocks = ref(0)

let canvas, ctx, gameLoopId
let paddle = { x: 0, y: 0, w: 120, h: 14 }
let balls = []
let blocks = []
let mouseX = 0
let audio = null
let lastComboTime = 0

// Konoha background elements
let bgClouds = []
let bgMountains = []
let bgTrees = []

function initAudio() {
  try {
    audio = new Audio('https://files.freemusicarchive.org/storage-freemusicarchive-org/music/no_curator/Kevin_MacLeod/Impact/Kevin_MacLeod_-_Impact_Allegretto.mp3')
    audio.loop = true
    audio.volume = 0.2
  } catch { /* audio not critical */ }
}

function initCanvas() {
  canvas = canvasRef.value
  const rect = containerRef.value.getBoundingClientRect()
  canvas.width = Math.min(rect.width - 20, 760)
  canvas.height = Math.min(rect.height - 100, 580)
  ctx = canvas.getContext('2d')
}

function initBackground() {
  const w = canvas.width
  const h = canvas.height
  // Clouds
  bgClouds = []
  for (let i = 0; i < 5; i++) {
    bgClouds.push({
      x: Math.random() * w,
      y: 10 + Math.random() * 60,
      w: 40 + Math.random() * 80,
      speed: 0.1 + Math.random() * 0.2
    })
  }
  // Hokage Mountain silhouette
  bgMountains = [
    { cx: w * 0.15, h: 90 + Math.random() * 30, w: 70 },
    { cx: w * 0.35, h: 110 + Math.random() * 20, w: 80 },
    { cx: w * 0.55, h: 95 + Math.random() * 25, w: 75 },
    { cx: w * 0.72, h: 105 + Math.random() * 20, w: 70 },
    { cx: w * 0.88, h: 85 + Math.random() * 30, w: 65 },
  ]
  // Trees
  bgTrees = []
  for (let i = 0; i < 20; i++) {
    bgTrees.push({
      x: Math.random() * w,
      h: 15 + Math.random() * 30,
      w: 6 + Math.random() * 12
    })
  }
}

function createBlocks() {
  const rows = 5
  const cols = 10
  const padding = 4
  const topMargin = 60
  const bw = (canvas.width - padding * (cols + 1)) / cols
  const bh = 22
  blocks = []

  const colors = ['#EF4444', '#F97316', '#F59E0B', '#22C55E', '#3B82F6']

  for (let r = 0; r < rows; r++) {
    for (let c = 0; c < cols; c++) {
      blocks.push({
        x: padding + c * (bw + padding),
        y: topMargin + r * (bh + padding),
        w: bw,
        h: bh,
        color: colors[r],
        alive: true,
        extraBall: Math.random() < 0.15
      })
    }
  }
  initialBlocks.value = blocks.length
  blocksRemaining.value = blocks.length
}

function getBallSpeed(ballCount) {
  // Base speed is slower, increases with ball count
  return 3.5 + ballCount * 0.3
}

function startGame() {
  initCanvas()
  initBackground()
  paddle = {
    x: canvas.width / 2 - 60,
    y: canvas.height - 40,
    w: 120,
    h: 14
  }
  const baseSpeed = getBallSpeed(1)
  balls = [{
    x: canvas.width / 2,
    y: canvas.height - 60,
    dx: (Math.random() - 0.5) * baseSpeed * 1.2,
    dy: -baseSpeed,
    r: 7
  }]
  score.value = 0
  combo.value = 1
  ballCount.value = 1
  lastComboTime = 0
  createBlocks()

  if (!audio) initAudio()
  if (audio) {
    audio.currentTime = 0
    audio.play().catch(() => {})
  }

  gameOver.value = false
  started.value = true
  cancelAnimationFrame(gameLoopId)
  gameLoop()
}

function gameLoop() {
  if (!started.value || gameOver.value) return
  update()
  draw()
  gameLoopId = requestAnimationFrame(gameLoop)
}

function update() {
  // Paddle follows mouse
  paddle.x = Math.max(0, Math.min(canvas.width - paddle.w, mouseX - paddle.w / 2))

  // Update combo timer
  const now = performance.now()
  if (now - lastComboTime > 2000) {
    combo.value = 1
  }

  // Update balls
  const newBalls = []
  for (const ball of balls) {
    ball.x += ball.dx
    ball.y += ball.dy

    // Wall collisions
    if (ball.x - ball.r <= 0 || ball.x + ball.r >= canvas.width) {
      ball.dx = -ball.dx
      ball.x = Math.max(ball.r, Math.min(canvas.width - ball.r, ball.x))
    }
    if (ball.y - ball.r <= 0) {
      ball.dy = -ball.dy
      ball.y = ball.r
    }

    // Bottom (ball lost)
    if (ball.y + ball.r >= canvas.height) {
      continue
    }

    // Paddle collision
    if (ball.y + ball.r >= paddle.y &&
        ball.y - ball.r <= paddle.y + paddle.h &&
        ball.x >= paddle.x &&
        ball.x <= paddle.x + paddle.w) {
      const hitPos = (ball.x - paddle.x) / paddle.w
      const angle = (hitPos - 0.5) * Math.PI * 0.65
      const currentSpeed = getBallSpeed(balls.length)
      ball.dx = Math.sin(angle) * currentSpeed
      ball.dy = -Math.abs(Math.cos(angle) * currentSpeed)
      ball.y = paddle.y - ball.r
    }

    // Block collision
    let hitBlock = false
    for (const block of blocks) {
      if (!block.alive) continue
      if (ball.x + ball.r > block.x && ball.x - ball.r < block.x + block.w &&
          ball.y + ball.r > block.y && ball.y - ball.r < block.y + block.h) {
        block.alive = false
        blocksRemaining.value--
        hitBlock = true

        // Combo
        const nowT = performance.now()
        if (nowT - lastComboTime < 1500) {
          combo.value++
        } else {
          combo.value = 1
        }
        lastComboTime = nowT
        score.value += 10 * combo.value

        // Extra ball
        if (block.extraBall) {
          const extraSpeed = getBallSpeed(balls.length + newBalls.length + 1)
          newBalls.push({
            x: ball.x,
            y: ball.y,
            dx: (Math.random() - 0.5) * extraSpeed * 1.5,
            dy: -extraSpeed * 0.8 - Math.random() * 2,
            r: 7
          })
        }

        // Bounce resolution
        let overlapX = 0, overlapY = 0
        const left = ball.x + ball.r - block.x
        const right = block.x + block.w - (ball.x - ball.r)
        const top = ball.y + ball.r - block.y
        const bottom = block.y + block.h - (ball.y - ball.r)
        const minX = Math.min(left, right)
        const minY = Math.min(top, bottom)

        if (minX < minY) {
          ball.dx = -ball.dx
          ball.x += left < right ? -minX : minX
        } else {
          ball.dy = -ball.dy
          ball.y += top < bottom ? -minY : minY
        }
        break
      }
    }

    // Adjust speed based on total ball count
    const targetSpeed = getBallSpeed(balls.length + newBalls.length)
    const currentSpeed = Math.sqrt(ball.dx ** 2 + ball.dy ** 2)
    if (currentSpeed > 0 && Math.abs(currentSpeed - targetSpeed) > 0.5) {
      const factor = targetSpeed / currentSpeed
      ball.dx *= factor
      ball.dy *= factor
    }

    newBalls.push(ball)
  }

  balls = newBalls
  ballCount.value = balls.length

  // Win or lose
  if (blocksRemaining.value === 0) {
    score.value += 50
    endGame()
  }
  if (balls.length === 0) {
    endGame()
  }
}

function draw() {
  if (!ctx) return
  const w = canvas.width
  const h = canvas.height

  // Konoha Sky Gradient
  const sky = ctx.createLinearGradient(0, 0, 0, h)
  sky.addColorStop(0, '#1A2332')
  sky.addColorStop(0.25, '#3B5998')
  sky.addColorStop(0.55, '#87CEEB')
  sky.addColorStop(0.8, '#90D5EC')
  sky.addColorStop(1, '#7EC8E3')
  ctx.fillStyle = sky
  ctx.fillRect(0, 0, w, h)

  // Stars (top portion)
  ctx.fillStyle = '#fff'
  for (let i = 0; i < 35; i++) {
    const sx = (i * 137 + 50) % w
    const sy = (i * 73 + 10) % 40
    const alpha = 0.3 + (i % 5) * 0.15
    ctx.globalAlpha = alpha
    ctx.beginPath()
    ctx.arc(sx, sy, (i % 3) * 0.5 + 0.5, 0, Math.PI * 2)
    ctx.fill()
  }
  ctx.globalAlpha = 1

  // Clouds
  ctx.fillStyle = 'rgba(255,255,255,0.35)'
  for (const cloud of bgClouds) {
    ctx.beginPath()
    ctx.ellipse(cloud.x, cloud.y, cloud.w / 2, cloud.w / 6, 0, 0, Math.PI * 2)
    ctx.fill()
    ctx.beginPath()
    ctx.ellipse(cloud.x - cloud.w * 0.25, cloud.y + 4, cloud.w / 3, cloud.w / 7, 0, 0, Math.PI * 2)
    ctx.fill()
    ctx.beginPath()
    ctx.ellipse(cloud.x + cloud.w * 0.25, cloud.y + 3, cloud.w / 3.5, cloud.w / 7, 0, 0, Math.PI * 2)
    ctx.fill()
  }

  // Hokage Mountain (distant gray-green)
  ctx.fillStyle = '#2D4A3E'
  ctx.beginPath()
  ctx.moveTo(0, h * 0.55)
  for (const m of bgMountains) {
    ctx.lineTo(m.cx - m.w * 0.5, h * 0.55)
    ctx.quadraticCurveTo(m.cx - m.w * 0.3, h * 0.55 - m.h * 0.7, m.cx - m.w * 0.15, h * 0.55 - m.h)
    ctx.quadraticCurveTo(m.cx, h * 0.55 - m.h * 0.85, m.cx + m.w * 0.15, h * 0.55 - m.h)
    ctx.quadraticCurveTo(m.cx + m.w * 0.3, h * 0.55 - m.h * 0.7, m.cx + m.w * 0.5, h * 0.55)
  }
  ctx.lineTo(w, h * 0.55)
  ctx.closePath()
  ctx.fill()

  // Hokage faces (simplified - carved look)
  ctx.fillStyle = '#3B5E4A'
  for (const m of bgMountains) {
    // Face outline
    ctx.beginPath()
    ctx.arc(m.cx, h * 0.55 - m.h * 0.45, m.w * 0.22, 0, Math.PI * 2)
    ctx.fill()
    // Eyes
    ctx.fillStyle = '#2D4A3E'
    ctx.beginPath()
    ctx.arc(m.cx - m.w * 0.07, h * 0.55 - m.h * 0.5, 2.5, 0, Math.PI * 2)
    ctx.fill()
    ctx.beginPath()
    ctx.arc(m.cx + m.w * 0.07, h * 0.55 - m.h * 0.5, 2.5, 0, Math.PI * 2)
    ctx.fill()
    ctx.fillStyle = '#3B5E4A'
  }

  // Village ground/buildings
  ctx.fillStyle = '#3D5A3C'
  ctx.fillRect(0, h * 0.65, w, h * 0.35)

  // Trees in village
  ctx.fillStyle = '#2D6B30'
  for (const tree of bgTrees) {
    const ty = h * 0.63 + Math.random() * 15
    // Trunk
    ctx.fillStyle = '#5D4037'
    ctx.fillRect(tree.x - 1.5, ty, 3, tree.h * 0.4)
    // Canopy
    ctx.fillStyle = '#2D6B30'
    ctx.beginPath()
    ctx.arc(tree.x, ty - 2, tree.w / 2, 0, Math.PI * 2)
    ctx.fill()
    ctx.fillStyle = '#388E3C'
    ctx.beginPath()
    ctx.arc(tree.x + 2, ty - 4, tree.w / 3, 0, Math.PI * 2)
    ctx.fill()
  }
  ctx.fillStyle = '#2D6B30'

  // Building silhouettes (Konoha buildings within game area)
  ctx.fillStyle = 'rgba(40, 60, 40, 0.5)'
  for (let i = 0; i < 8; i++) {
    const bx = i * 100 + 20
    ctx.fillRect(bx, h * 0.62, 40, 25 + (i % 3) * 15)
    // Roof
    ctx.fillStyle = 'rgba(139, 90, 43, 0.4)'
    ctx.beginPath()
    ctx.moveTo(bx - 5, h * 0.62)
    ctx.lineTo(bx + 20, h * 0.62 - 12)
    ctx.lineTo(bx + 45, h * 0.62)
    ctx.fill()
    ctx.fillStyle = 'rgba(40, 60, 40, 0.5)'
  }

  // Blocks (the "attacking" blocks)
  for (const block of blocks) {
    if (!block.alive) continue
    const grad = ctx.createLinearGradient(block.x, block.y, block.x, block.y + block.h)
    grad.addColorStop(0, block.color)
    grad.addColorStop(1, '#1A1A2E')
    ctx.fillStyle = grad
    ctx.shadowColor = block.color
    ctx.shadowBlur = 6
    ctx.beginPath()
    ctx.roundRect(block.x, block.y, block.w, block.h, 3)
    ctx.fill()
    ctx.shadowBlur = 0

    // Extra ball indicator
    if (block.extraBall) {
      ctx.fillStyle = 'rgba(255,255,255,0.5)'
      ctx.beginPath()
      ctx.arc(block.x + block.w / 2, block.y + block.h / 2, 4, 0, Math.PI * 2)
      ctx.fill()
    }
  }

  // Paddle (Konoha shield)
  const pg = ctx.createLinearGradient(paddle.x, paddle.y, paddle.x, paddle.y + paddle.h)
  pg.addColorStop(0, '#22C55E')
  pg.addColorStop(0.5, '#16A34A')
  pg.addColorStop(1, '#15803D')
  ctx.fillStyle = pg
  ctx.shadowColor = '#22C55E'
  ctx.shadowBlur = 14
  ctx.beginPath()
  ctx.roundRect(paddle.x, paddle.y, paddle.w, paddle.h, 7)
  ctx.fill()
  ctx.shadowBlur = 0

  // Leaf symbol on paddle
  ctx.fillStyle = '#fff'
  ctx.font = '10px sans-serif'
  ctx.textAlign = 'center'
  ctx.fillText('🍃', paddle.x + paddle.w / 2, paddle.y + 11)
  ctx.textAlign = 'start'

  // Balls (Rasengan-like chakra balls)
  for (const ball of balls) {
    // Outer glow
    ctx.shadowColor = '#FBBF24'
    ctx.shadowBlur = 15
    const gradient = ctx.createRadialGradient(ball.x - 2, ball.y - 2, 1, ball.x, ball.y, ball.r)
    gradient.addColorStop(0, '#fff')
    gradient.addColorStop(0.3, '#FDE68A')
    gradient.addColorStop(0.7, '#F59E0B')
    gradient.addColorStop(1, '#D97706')
    ctx.fillStyle = gradient
    ctx.beginPath()
    ctx.arc(ball.x, ball.y, ball.r, 0, Math.PI * 2)
    ctx.fill()
    ctx.shadowBlur = 0

    // Spiral effect
    ctx.strokeStyle = 'rgba(255,255,255,0.6)'
    ctx.lineWidth = 1
    ctx.beginPath()
    ctx.arc(ball.x, ball.y, ball.r * 0.5, performance.now() * 0.004, performance.now() * 0.004 + Math.PI)
    ctx.stroke()
  }
}

function endGame() {
  gameOver.value = true
  started.value = false
  cancelAnimationFrame(gameLoopId)
  if (audio) audio.pause()
  emit('earn', score.value)
}

function handleMouseMove(e) {
  const rect = canvas.getBoundingClientRect()
  mouseX = e.clientX - rect.left
}

function handleTouchMove(e) {
  e.preventDefault()
  const rect = canvas.getBoundingClientRect()
  mouseX = e.touches[0].clientX - rect.left
}

onMounted(() => {
  initAudio()
})

onUnmounted(() => {
  cancelAnimationFrame(gameLoopId)
  if (audio) {
    audio.pause()
    audio = null
  }
})
</script>

<style scoped>
.breakout-game {
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
  box-shadow: 0 0 30px rgba(34, 197, 94, 0.15);
  cursor: none;
}

.game-hud {
  display: flex;
  gap: 24px;
  margin-top: 12px;
  flex-wrap: wrap;
  justify-content: center;
}

.hud-item {
  font-size: 14px;
  color: #94A3B8;
}

.hud-item strong {
  color: #60A5FA;
  font-size: 16px;
}

.game-over-overlay {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(11, 17, 33, 0.92);
  backdrop-filter: blur(8px);
  z-index: 20;
}

.game-over-card {
  text-align: center;
  padding: 40px;
  background: rgba(255,255,255,0.05);
  border: 1px solid rgba(255,255,255,0.1);
  border-radius: 20px;
  max-width: 360px;
  width: 90%;
}

.game-over-card h2 {
  font-size: 26px;
  color: #22C55E;
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
  background: rgba(255,255,255,0.05);
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
  background: linear-gradient(135deg, #16A34A, #22C55E);
  color: #fff;
  font-size: 16px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-restart:hover {
  background: linear-gradient(135deg, #22C55E, #4ADE80);
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(34, 197, 94, 0.4);
}
</style>
