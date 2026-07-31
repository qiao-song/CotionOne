<template>
  <div class="games-page">
    <!-- Points display in top-right -->
    <div class="points-bar">
      <div class="points-display">
        <span class="points-icon">🎮</span>
        <span class="points-label">当前点数</span>
        <span class="points-value">{{ totalPoints }}</span>
      </div>
      <button
        class="btn-exchange"
        :disabled="totalPoints <= 0 || exchanging"
        @click="handleExchange"
      >
        {{ exchanging ? '兑换中...' : `兑换为余额 (¥${(totalPoints * 0.01).toFixed(2)})` }}
      </button>
    </div>

    <h1 class="page-title">🎮 游戏中心</h1>
    <p class="page-subtitle">玩游戏赚点数，兑换成账户余额！</p>

    <!-- Game list -->
    <div class="game-list">
      <!-- Game 1: Snake -->
      <div class="game-card" @click="currentGame = 'snake'">
        <div class="game-card-banner snake-banner">
          <div class="game-emoji">🐍</div>
          <div class="game-badge">经典街机</div>
        </div>
        <div class="game-card-body">
          <h3>蛇兜化龙记</h3>
          <p class="game-desc">经典贪吃蛇玩法，操控小蛇吃豆成长，最终化为神龙！越长大分数越高。</p>
          <div class="game-tags">
            <span class="g-tag">🎵 火影主题曲</span>
            <span class="g-tag">⌨️ 方向键控制</span>
            <span class="g-tag">⭐ 经典玩法</span>
          </div>
          <button class="btn-primary game-btn" @click.stop="currentGame = 'snake'">开始游戏</button>
        </div>
      </div>

      <!-- Game 2: Breakout -->
      <div class="game-card" @click="currentGame = 'breakout'">
        <div class="game-card-banner breakout-banner">
          <div class="game-emoji">🍃</div>
          <div class="game-badge">休闲益智</div>
        </div>
        <div class="game-card-body">
          <h3>守护木叶村</h3>
          <p class="game-desc">移动挡板接住查克拉球，击碎来袭的方块！击碎方块可获得额外小球和点数奖励。</p>
          <div class="game-tags">
            <span class="g-tag">🎵 蔚蓝档案主题曲</span>
            <span class="g-tag">🖱️ 鼠标控制</span>
            <span class="g-tag">💥 多重弹球</span>
          </div>
          <button class="btn-primary game-btn" @click.stop="currentGame = 'breakout'">开始游戏</button>
        </div>
      </div>

      <!-- Game 3: Bullet Hell -->
      <div class="game-card" @click="currentGame = 'bullethell'">
        <div class="game-card-banner bullet-banner">
          <div class="game-emoji">✨</div>
          <div class="game-badge">弹幕射击</div>
        </div>
        <div class="game-card-body">
          <h3>东方幻想乡</h3>
          <p class="game-desc">鼠标控制灵梦在红魔馆躲避弹幕，坚持越久点数倍率越高！弹幕每10秒升级一次。</p>
          <div class="game-tags">
            <span class="g-tag">🎵 游戏开发部主题曲</span>
            <span class="g-tag">🖱️ 鼠标控制</span>
            <span class="g-tag">🔥 倍率递增</span>
          </div>
          <button class="btn-primary game-btn" @click.stop="currentGame = 'bullethell'">开始游戏</button>
        </div>
      </div>
    </div>

    <!-- Game overlay -->
    <Teleport to="body">
      <div v-if="currentGame" class="game-overlay">
        <div class="game-container">
          <div class="game-header">
            <button class="btn-back" @click="closeGame">✕ 返回</button>
            <span class="game-points">🏆 {{ gamePoints }}</span>
          </div>
          <SnakeGame
            v-if="currentGame === 'snake'"
            @earn="onGameEarn"
            @close="closeGame"
          />
          <BreakoutGame
            v-if="currentGame === 'breakout'"
            @earn="onGameEarn"
            @close="closeGame"
          />
          <BulletHellGame
            v-if="currentGame === 'bullethell'"
            @earn="onGameEarn"
            @close="closeGame"
          />
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useToast } from '../composables/useToast'
import { useAuthStore } from '../stores/auth'
import { earnPoints } from '../api/user'
import SnakeGame from '../components/games/SnakeGame.vue'
import BreakoutGame from '../components/games/BreakoutGame.vue'
import BulletHellGame from '../components/games/BulletHellGame.vue'

const toast = useToast()
const authStore = useAuthStore()

const currentGame = ref(null)
const totalPoints = ref(0)
const gamePoints = ref(0)
const exchanging = ref(false)

// Load saved points
onMounted(() => {
  const saved = localStorage.getItem('tbao_game_points')
  if (saved) totalPoints.value = parseInt(saved) || 0
})

function savePoints() {
  localStorage.setItem('tbao_game_points', totalPoints.value.toString())
}

function onGameEarn(points) {
  gamePoints.value += points
  totalPoints.value += points
  savePoints()
}

function closeGame() {
  // Transfer game session points to total
  totalPoints.value += gamePoints.value
  gamePoints.value = 0
  savePoints()
  currentGame.value = null
}

async function handleExchange() {
  if (totalPoints.value <= 0) return
  exchanging.value = true
  try {
    const res = await earnPoints({ points: totalPoints.value, game: '游戏中心' })
    toast.success(res.msg || `成功兑换 ${totalPoints.value} 点数`)
    // Refresh auth store to update balance
    await authStore.fetchUser()
    totalPoints.value = 0
    savePoints()
  } catch (e) {
    toast.error(e.msg || '兑换失败')
  } finally {
    exchanging.value = false
  }
}
</script>

<style scoped>
.games-page {
  padding-bottom: 40px;
  position: relative;
}

.page-subtitle {
  color: var(--text-secondary);
  font-size: 14px;
  margin-top: -16px;
  margin-bottom: 28px;
}

.points-bar {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 16px;
  margin-bottom: 16px;
  position: sticky;
  top: 72px;
  z-index: 10;
}

.points-display {
  display: flex;
  align-items: center;
  gap: 8px;
  background: linear-gradient(135deg, #1F2937, #374151);
  color: #FBBF24;
  padding: 8px 20px;
  border-radius: 24px;
  font-weight: 600;
  box-shadow: 0 4px 14px rgba(0,0,0,0.15);
}

.points-icon {
  font-size: 20px;
}

.points-label {
  font-size: 12px;
  color: #9CA3AF;
}

.points-value {
  font-size: 20px;
  font-weight: 800;
}

.btn-exchange {
  min-width: auto;
  padding: 8px 20px;
  height: 40px;
  border-radius: 20px;
  border: none;
  background: linear-gradient(135deg, #F59E0B, #D97706);
  color: #fff;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  white-space: nowrap;
  box-shadow: 0 2px 10px rgba(245, 158, 11, 0.3);
  transition: all 0.2s ease;
}

.btn-exchange:hover:not(:disabled) {
  background: linear-gradient(135deg, #FBBF24, #F59E0B);
  transform: translateY(-1px);
  box-shadow: 0 4px 16px rgba(245, 158, 11, 0.4);
}

.btn-exchange:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Game cards */
.game-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 24px;
}

.game-card {
  background: var(--card-bg);
  border-radius: var(--radius);
  overflow: hidden;
  box-shadow: 0 4px 16px rgba(0,0,0,0.06);
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  border: 1px solid transparent;
}

.game-card:hover {
  transform: translateY(-6px);
  box-shadow: 0 20px 40px rgba(0,0,0,0.12);
  border-color: rgba(249, 115, 22, 0.2);
}

.game-card-banner {
  height: 140px;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  overflow: hidden;
}

.snake-banner {
  background: linear-gradient(135deg, #064E3B, #059669, #34D399);
}

.breakout-banner {
  background: linear-gradient(135deg, #1E3A5F, #3B82F6, #60A5FA);
}

.bullet-banner {
  background: linear-gradient(135deg, #4C1D95, #7C3AED, #A78BFA);
}

.game-emoji {
  font-size: 56px;
  filter: drop-shadow(0 4px 8px rgba(0,0,0,0.3));
  animation: float 3s ease-in-out infinite;
}

@keyframes float {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-8px); }
}

.game-badge {
  position: absolute;
  top: 12px;
  right: 12px;
  background: rgba(255,255,255,0.2);
  backdrop-filter: blur(8px);
  color: #fff;
  font-size: 11px;
  font-weight: 600;
  padding: 4px 12px;
  border-radius: 12px;
}

.game-card-body {
  padding: 20px;
}

.game-card-body h3 {
  font-size: 20px;
  font-weight: 700;
  color: var(--text);
  margin-bottom: 8px;
}

.game-desc {
  font-size: 14px;
  color: var(--text-secondary);
  line-height: 1.6;
  margin-bottom: 12px;
}

.game-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-bottom: 16px;
}

.g-tag {
  font-size: 11px;
  padding: 3px 10px;
  border-radius: 12px;
  background: var(--bg);
  color: var(--text-secondary);
  border: 1px solid var(--border);
}

.game-btn {
  width: 100%;
}

/* Game overlay */
.game-overlay {
  position: fixed;
  inset: 0;
  z-index: 2000;
  background: #0F172A;
  display: flex;
  align-items: center;
  justify-content: center;
}

.game-container {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.game-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 20px;
  background: rgba(255,255,255,0.05);
  border-bottom: 1px solid rgba(255,255,255,0.1);
  z-index: 10;
}

.btn-back {
  min-width: auto;
  padding: 6px 16px;
  height: 36px;
  border: 1px solid rgba(255,255,255,0.2);
  border-radius: var(--radius-sm);
  background: rgba(255,255,255,0.1);
  color: #fff;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-back:hover {
  background: rgba(255,255,255,0.2);
}

.game-points {
  font-size: 18px;
  font-weight: 700;
  color: #FBBF24;
}
</style>
