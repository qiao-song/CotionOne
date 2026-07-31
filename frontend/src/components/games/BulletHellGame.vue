<template>
  <div class="bullet-hell-game" ref="containerRef">
    <canvas
      ref="canvasRef"
      class="game-canvas"
      @mousemove="handleMouseMove"
      @touchmove="handleTouchMove"
    ></canvas>
    <div class="game-hud">
      <div class="hud-item">⏱️ 时间: <strong>{{ formatTime(survivalTime) }}</strong></div>
      <div class="hud-item">🔥 倍率: <strong>x{{ multiplier.toFixed(1) }}</strong></div>
      <div class="hud-item">🏆 点数: <strong>{{ score }}</strong></div>
      <div class="hud-item">💖 生命: <strong>{{ lives }}</strong></div>
    </div>
    <div v-if="gameOver" class="game-over-overlay">
      <div class="game-over-card">
        <h2>💫 幻想乡之旅结束</h2>
        <div class="final-score">
          <div class="score-row"><span>存活时间</span><span>{{ formatTime(survivalTime) }}</span></div>
          <div class="score-row"><span>最终倍率</span><span>x{{ multiplier.toFixed(1) }}</span></div>
          <div class="score-row"><span>获得点数</span><span class="pts">{{ score }}</span></div>
        </div>
        <button class="btn-restart" @click="startGame">再来一局</button>
      </div>
    </div>
    <div v-if="!started && !gameOver" class="game-over-overlay">
      <div class="game-over-card">
        <h2>✨ 东方幻想乡</h2>
        <p class="game-desc-text">鼠标控制灵梦移动<br/>躲避红魔馆的弹幕攻击<br/>存活越久倍率越高，点数越多！<br/>每10秒弹幕密度增加<br/>共有 3 次生命机会</p>
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
const survivalTime = ref(0)
const multiplier = ref(1.0)
const score = ref(0)
const lives = ref(3)

let canvas, ctx, gameLoopId
let player = { x: 0, y: 0, r: 7, speed: 4 }
let bullets = []
let particles = []
let stars = []
let startTime = 0
let lastBulletSpawn = 0
let bulletInterval = 400
let mouseX = 0
let mouseY = 0
let audio = null
let densityLevel = 0
let lastDensityIncrease = 0
let bgMansion = {}

function initAudio() {
  try {
    audio = new Audio('https://files.freemusicarchive.org/storage-freemusicarchive-org/music/no_curator/Kevin_MacLeod/Impact/Kevin_MacLeod_-_Impact_Moderato.mp3')
    audio.loop = true
    audio.volume = 0.25
  } catch { /* audio not critical */ }
}

function initCanvas() {
  canvas = canvasRef.value
  const rect = containerRef.value.getBoundingClientRect()
  canvas.width = Math.min(rect.width - 20, 540)
  canvas.height = Math.min(rect.height - 100, 640)
  ctx = canvas.getContext('2d')

  // Position mansion elements
  bgMansion = {
    x: canvas.width * 0.5,
    y: canvas.height * 0.28,
    w: canvas.width * 0.55,
    h: canvas.height * 0.18,
  }
}

function initStars() {
  stars = []
  for (let i = 0; i < 50; i++) {
    stars.push({
      x: Math.random() * canvas.width,
      y: Math.random() * canvas.height,
      r: Math.random() * 1.2 + 0.4,
      speed: Math.random() * 0.3 + 0.1,
      twinkle: Math.random() * Math.PI * 2
    })
  }
}

function getDensityMultiplier(elapsed) {
  // Every 10 seconds, density increases
  return 1.0 + Math.floor(elapsed / 10) * 0.6
}

function spawnBullets() {
  const now = performance.now()
  if (now - lastBulletSpawn < bulletInterval) return
  lastBulletSpawn = now

  const elapsed = (now - startTime) / 1000
  const density = getDensityMultiplier(elapsed)
  bulletInterval = Math.max(50, 400 - elapsed * 8)

  // Track density level changes for display
  const newLevel = Math.floor(elapsed / 10)
  if (newLevel > densityLevel) {
    densityLevel = newLevel
  }

  const pattern = Math.floor(Math.random() * 4)

  if (pattern === 0) {
    // Random bullets
    const count = 1 + Math.floor(elapsed / 6 * density)
    for (let i = 0; i < count; i++) {
      bullets.push({
        x: Math.random() * canvas.width,
        y: -10,
        dx: (Math.random() - 0.5) * 2.5,
        dy: 1.5 + Math.random() * 3,
        r: 4,
        color: '#EF4444'
      })
    }
  } else if (pattern === 1) {
    // Spread fan
    const cx = Math.random() * canvas.width
    const count = 5 + Math.floor(elapsed / 4 * density)
    for (let i = 0; i < count; i++) {
      const angle = (i / count) * Math.PI - Math.PI / 2
      bullets.push({
        x: cx,
        y: -10,
        dx: Math.cos(angle) * 2,
        dy: Math.abs(Math.sin(angle)) * 2.5 + 1,
        r: 3,
        color: '#F59E0B'
      })
    }
  } else if (pattern === 2) {
    // Aimed at player
    if (elapsed > 5) {
      const angle = Math.atan2(player.y - 20, player.x - canvas.width / 2)
      const count = 3 + Math.floor(density)
      for (let i = -Math.floor(count / 2); i <= Math.floor(count / 2); i++) {
        bullets.push({
          x: canvas.width / 2 + i * 35,
          y: -10,
          dx: Math.cos(angle + i * 0.12) * 2.8,
          dy: Math.sin(angle + i * 0.12) * 2.5 + 1.5,
          r: 5,
          color: '#EC4899'
        })
      }
    }
  } else {
    // Circle burst from mansion area
    const cx = canvas.width / 2 + (Math.random() - 0.5) * 250
    const cy = canvas.height / 3
    const count = 8 + Math.floor(elapsed / 3 * density)
    for (let i = 0; i < count; i++) {
      const angle = (i / count) * Math.PI * 2
      bullets.push({
        x: cx,
        y: cy,
        dx: Math.cos(angle) * 2,
        dy: Math.sin(angle) * 2,
        r: 4,
        color: '#8B5CF6'
      })
    }
  }
}

function startGame() {
  initCanvas()
  initStars()
  player = {
    x: canvas.width / 2,
    y: canvas.height - 100,
    r: 7,
    speed: 4
  }
  bullets = []
  particles = []
  mouseX = player.x
  mouseY = player.y
  startTime = performance.now()
  lastBulletSpawn = startTime
  bulletInterval = 400
  survivalTime.value = 0
  multiplier.value = 1.0
  score.value = 0
  lives.value = 3
  densityLevel = 0

  if (!audio) initAudio()
  if (audio) {
    audio.currentTime = 0
    audio.play().catch(() => {})
  }

  gameOver.value = false
  started.value = true
  cancelAnimationFrame(gameLoopId)
  gameLoop(performance.now())
}

function gameLoop(timestamp) {
  if (!started.value || gameOver.value) return
  update(timestamp)
  draw()
  gameLoopId = requestAnimationFrame(gameLoop)
}

function update(timestamp) {
  const elapsed = (timestamp - startTime) / 1000
  survivalTime.value = Math.floor(elapsed)
  multiplier.value = 1.0 + elapsed * 0.15
  score.value = Math.floor(elapsed * multiplier.value)

  // Player follows mouse smoothly
  const targetX = Math.max(player.r, Math.min(canvas.width - player.r, mouseX))
  const targetY = Math.max(player.r, Math.min(canvas.height - player.r, mouseY))
  player.x += (targetX - player.x) * 0.3
  player.y += (targetY - player.y) * 0.3

  // Spawn bullets
  spawnBullets()

  // Update bullets
  for (const b of bullets) {
    b.x += b.dx
    b.y += b.dy
  }

  // Remove off-screen bullets
  bullets = bullets.filter(b =>
    b.y < canvas.height + 50 && b.y > -50 &&
    b.x > -50 && b.x < canvas.width + 50
  )

  // Collision detection
  for (let i = bullets.length - 1; i >= 0; i--) {
    const b = bullets[i]
    const dist = Math.sqrt((b.x - player.x) ** 2 + (b.y - player.y) ** 2)
    if (dist < b.r + player.r - 1) {
      bullets.splice(i, 1)
      lives.value--

      // Spawn particles
      for (let p = 0; p < 12; p++) {
        const angle = (p / 12) * Math.PI * 2
        particles.push({
          x: player.x,
          y: player.y,
          dx: Math.cos(angle) * 2,
          dy: Math.sin(angle) * 2,
          life: 20,
          maxLife: 20,
          color: '#FBBF24'
        })
      }

      // Reposition player
      player.x = canvas.width / 2
      player.y = canvas.height - 100
      mouseX = player.x
      mouseY = player.y

      if (lives.value <= 0) {
        endGame()
        return
      }
    }
  }

  // Update particles
  for (const p of particles) {
    p.x += p.dx
    p.y += p.dy
    p.life--
  }
  particles = particles.filter(p => p.life > 0)

  // Update stars
  for (const s of stars) {
    s.y += s.speed
    if (s.y > canvas.height) {
      s.y = 0
      s.x = Math.random() * canvas.width
    }
  }
}

function draw() {
  if (!ctx) return
  const w = canvas.width
  const h = canvas.height

  // Background - Scarlet Devil Mansion night sky (红魔馆)
  const bg = ctx.createLinearGradient(0, 0, 0, h)
  bg.addColorStop(0, '#0A0208')
  bg.addColorStop(0.3, '#1A0518')
  bg.addColorStop(0.6, '#2D0A1E')
  bg.addColorStop(1, '#1A0A10')
  ctx.fillStyle = bg
  ctx.fillRect(0, 0, w, h)

  // Blood-red moon
  const moonX = w * 0.78
  const moonY = h * 0.12
  ctx.shadowColor = '#DC2626'
  ctx.shadowBlur = 40
  ctx.fillStyle = '#991B1B'
  ctx.beginPath()
  ctx.arc(moonX, moonY, 30, 0, Math.PI * 2)
  ctx.fill()
  ctx.shadowBlur = 0

  // Moon inner glow
  const moonGrad = ctx.createRadialGradient(moonX - 5, moonY - 5, 8, moonX, moonY, 30)
  moonGrad.addColorStop(0, '#DC2626')
  moonGrad.addColorStop(1, '#7F1D1D')
  ctx.fillStyle = moonGrad
  ctx.beginPath()
  ctx.arc(moonX, moonY, 30, 0, Math.PI * 2)
  ctx.fill()

  // Stars
  for (const s of stars) {
    const twinkle = 0.3 + 0.4 * Math.sin(performance.now() * 0.002 + s.twinkle)
    ctx.fillStyle = `rgba(255, 220, 220, ${twinkle})`
    ctx.beginPath()
    ctx.arc(s.x, s.y, s.r, 0, Math.PI * 2)
    ctx.fill()
  }

  // Distant mist/fog
  ctx.fillStyle = 'rgba(139, 30, 50, 0.08)'
  ctx.fillRect(0, h * 0.5, w, h * 0.3)

  // Scarlet Devil Mansion silhouette
  const mx = bgMansion.x
  const my = bgMansion.y
  const mw = bgMansion.w
  const mh = bgMansion.h

  // Mansion main building
  ctx.fillStyle = '#1A0A10'
  ctx.fillRect(mx - mw * 0.45, my, mw * 0.9, mh)

  // Central tower
  ctx.fillStyle = '#1F0A12'
  ctx.fillRect(mx - mw * 0.12, my - mh * 0.5, mw * 0.24, mh * 1.5)

  // Tower spire
  ctx.fillStyle = '#1A0A10'
  ctx.beginPath()
  ctx.moveTo(mx - mw * 0.15, my - mh * 0.5)
  ctx.lineTo(mx, my - mh * 1.2)
  ctx.lineTo(mx + mw * 0.15, my - mh * 0.5)
  ctx.fill()

  // Side towers
  ctx.fillStyle = '#1F0A12'
  ctx.fillRect(mx - mw * 0.5, my - mh * 0.2, mw * 0.18, mh * 1.2)
  ctx.fillRect(mx + mw * 0.32, my - mh * 0.2, mw * 0.18, mh * 1.2)

  // Side tower spires
  ctx.fillStyle = '#1A0A10'
  ctx.beginPath()
  ctx.moveTo(mx - mw * 0.5, my - mh * 0.2)
  ctx.lineTo(mx - mw * 0.41, my - mh * 0.7)
  ctx.lineTo(mx - mw * 0.32, my - mh * 0.2)
  ctx.fill()
  ctx.beginPath()
  ctx.moveTo(mx + mw * 0.32, my - mh * 0.2)
  ctx.lineTo(mx + mw * 0.41, my - mh * 0.7)
  ctx.lineTo(mx + mw * 0.5, my - mh * 0.2)
  ctx.fill()

  // Windows (glowing red)
  ctx.fillStyle = '#DC2626'
  ctx.shadowColor = '#EF4444'
  ctx.shadowBlur = 4
  const winSize = mw * 0.04
  for (let r = 0; r < 3; r++) {
    for (let c = 0; c < 6; c++) {
      if (Math.random() > 0.3) {
        ctx.fillRect(
          mx - mw * 0.35 + c * mw * 0.12,
          my + mh * 0.15 + r * mh * 0.3,
          winSize,
          winSize * 1.3
        )
      }
    }
  }
  ctx.shadowBlur = 0

  // Mansion clock tower (center detail)
  ctx.fillStyle = '#DC2626'
  ctx.beginPath()
  ctx.arc(mx, my - mh * 0.1, mw * 0.06, 0, Math.PI * 2)
  ctx.fill()
  ctx.strokeStyle = '#1A0A10'
  ctx.lineWidth = 1.5
  ctx.beginPath()
  ctx.arc(mx, my - mh * 0.1, mw * 0.06, 0, Math.PI * 2)
  ctx.stroke()

  // Ground
  ctx.fillStyle = '#0D0508'
  ctx.fillRect(0, h * 0.75, w, h * 0.25)

  // Bare trees
  ctx.strokeStyle = '#1A080E'
  ctx.lineWidth = 3
  for (let i = 0; i < 5; i++) {
    const tx = i * w * 0.22 + 15
    const ty = h * 0.72
    ctx.beginPath()
    ctx.moveTo(tx, ty + 10)
    ctx.lineTo(tx, ty - 15 - (i % 3) * 10)
    ctx.stroke()
    // Branches
    ctx.lineWidth = 1.5
    ctx.beginPath()
    ctx.moveTo(tx, ty - 5)
    ctx.lineTo(tx - 8 - i * 2, ty - 15 - (i % 2) * 5)
    ctx.stroke()
    ctx.beginPath()
    ctx.moveTo(tx, ty - 10)
    ctx.lineTo(tx + 8 + i * 2, ty - 18)
    ctx.stroke()
    ctx.lineWidth = 3
  }

  // Bullets
  for (const b of bullets) {
    ctx.fillStyle = b.color
    ctx.shadowColor = b.color
    ctx.shadowBlur = 8
    ctx.beginPath()
    ctx.arc(b.x, b.y, b.r, 0, Math.PI * 2)
    ctx.fill()
    // Inner glow
    ctx.fillStyle = '#fff'
    ctx.beginPath()
    ctx.arc(b.x, b.y, b.r * 0.5, 0, Math.PI * 2)
    ctx.fill()
  }
  ctx.shadowBlur = 0

  // Particles
  for (const p of particles) {
    const alpha = p.life / p.maxLife
    ctx.fillStyle = p.color
    ctx.globalAlpha = alpha
    ctx.beginPath()
    ctx.arc(p.x, p.y, 3, 0, Math.PI * 2)
    ctx.fill()
  }
  ctx.globalAlpha = 1

  // Player - Reimu Hakurei (博丽灵梦)
  drawReimu(player.x, player.y, player.r)
}

function drawReimu(px, py, baseR) {
  if (!ctx) return
  const r = baseR * 2 // Scale up for detail

  // Hitbox indicator (subtle)
  ctx.strokeStyle = 'rgba(255, 255, 255, 0.3)'
  ctx.lineWidth = 1
  ctx.beginPath()
  ctx.arc(px, py, baseR, 0, Math.PI * 2)
  ctx.stroke()

  // Body (red skirt / hakama)
  ctx.fillStyle = '#DC2626'
  ctx.beginPath()
  ctx.moveTo(px - r * 0.6, py + r * 0.2)
  ctx.lineTo(px - r * 0.35, py - r * 0.1)
  ctx.lineTo(px + r * 0.35, py - r * 0.1)
  ctx.lineTo(px + r * 0.6, py + r * 0.2)
  ctx.closePath()
  ctx.fill()

  // Upper body (white kosode)
  ctx.fillStyle = '#FEF3F3'
  ctx.beginPath()
  ctx.ellipse(px, py - r * 0.25, r * 0.35, r * 0.4, 0, 0, Math.PI * 2)
  ctx.fill()

  // Red collar/hakui detail
  ctx.fillStyle = '#DC2626'
  ctx.beginPath()
  ctx.moveTo(px - r * 0.3, py - r * 0.5)
  ctx.lineTo(px, py - r * 0.1)
  ctx.lineTo(px + r * 0.3, py - r * 0.5)
  ctx.closePath()
  ctx.fill()

  // Head
  ctx.fillStyle = '#FEE2D4'
  ctx.beginPath()
  ctx.arc(px, py - r * 0.65, r * 0.32, 0, Math.PI * 2)
  ctx.fill()

  // Hair (dark brown/purple)
  ctx.fillStyle = '#3B1F2B'
  ctx.beginPath()
  ctx.arc(px, py - r * 0.7, r * 0.34, Math.PI, Math.PI * 2)
  ctx.fill()
  // Side hair
  ctx.fillRect(px - r * 0.32, py - r * 0.75, r * 0.64, r * 0.25)

  // Hair ribbon (red bow)
  ctx.fillStyle = '#DC2626'
  ctx.beginPath()
  ctx.moveTo(px + r * 0.15, py - r * 1.0)
  ctx.lineTo(px + r * 0.35, py - r * 0.85)
  ctx.lineTo(px + r * 0.15, py - r * 0.8)
  ctx.fill()
  ctx.beginPath()
  ctx.moveTo(px - r * 0.15, py - r * 1.0)
  ctx.lineTo(px - r * 0.35, py - r * 0.85)
  ctx.lineTo(px - r * 0.15, py - r * 0.8)
  ctx.fill()

  // Eyes
  ctx.fillStyle = '#1C1917'
  ctx.beginPath()
  ctx.arc(px - r * 0.1, py - r * 0.7, 1.5, 0, Math.PI * 2)
  ctx.fill()
  ctx.beginPath()
  ctx.arc(px + r * 0.1, py - r * 0.7, 1.5, 0, Math.PI * 2)
  ctx.fill()

  // Sleeves (white, flowing)
  ctx.fillStyle = '#FEF3F3'
  ctx.beginPath()
  ctx.ellipse(px - r * 0.45, py - r * 0.3, r * 0.15, r * 0.35, -0.3, 0, Math.PI * 2)
  ctx.fill()
  ctx.beginPath()
  ctx.ellipse(px + r * 0.45, py - r * 0.3, r * 0.15, r * 0.35, 0.3, 0, Math.PI * 2)
  ctx.fill()

  // Glow aura
  ctx.strokeStyle = 'rgba(220, 38, 38, 0.15)'
  ctx.lineWidth = 2
  ctx.beginPath()
  ctx.arc(px, py, baseR * 2.5, 0, Math.PI * 2)
  ctx.stroke()
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

function handleMouseMove(e) {
  const rect = canvas.getBoundingClientRect()
  mouseX = e.clientX - rect.left
  mouseY = e.clientY - rect.top
}

function handleTouchMove(e) {
  e.preventDefault()
  const rect = canvas.getBoundingClientRect()
  mouseX = e.touches[0].clientX - rect.left
  mouseY = e.touches[0].clientY - rect.top
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
.bullet-hell-game {
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
  box-shadow: 0 0 30px rgba(220, 38, 38, 0.2);
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
  font-size: 13px;
  color: #94A3B8;
}

.hud-item strong {
  color: #FCA5A5;
  font-size: 16px;
}

.game-over-overlay {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(10, 2, 8, 0.94);
  backdrop-filter: blur(8px);
  z-index: 20;
}

.game-over-card {
  text-align: center;
  padding: 40px;
  background: rgba(220, 38, 38, 0.06);
  border: 1px solid rgba(220, 38, 38, 0.15);
  border-radius: 20px;
  max-width: 360px;
  width: 90%;
}

.game-over-card h2 {
  font-size: 26px;
  color: #FCA5A5;
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
  background: rgba(220, 38, 38, 0.06);
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
  background: linear-gradient(135deg, #DC2626, #EF4444);
  color: #fff;
  font-size: 16px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-restart:hover {
  background: linear-gradient(135deg, #EF4444, #F87171);
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(220, 38, 38, 0.5);
}
</style>
