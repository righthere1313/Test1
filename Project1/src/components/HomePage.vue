<template>
  <div class="home-page" :class="{ 'logged-in': isLoggedIn }">
    <div class="main-content">
      <transition name="fade" mode="out-in">
        <div v-if="showSplash && !isLoggedIn" key="splash" class="splash-wrapper">
          <SplashPage />
        </div>
        <div v-else key="intro" class="content-wrapper" :class="{ 'logged-in': isLoggedIn }">
          <div class="hero-section">
            <h1 class="title">AI互动式教学智能体</h1>
            <p class="slogan">让教学更简单，让课堂更精彩</p>
          </div>
          
          <div class="features-section">
            <div class="card" 
                 :class="{ 'active': activeCard === 0 }"
                 @mouseenter="handleCardHover(0)"
                 @mouseleave="handleCardLeave">
              <div class="img-box">
                <img src="/images/card1/1.png" alt="智能对话设计" class="card-img">
              </div>
              <div class="text-box">
                <h2>智能对话设计</h2>
                <p>与AI智能体自然对话，生成个性化教学方案。支持多轮对话交互，根据您的教学需求智能调整内容。无论是教学设计、教案撰写还是课堂活动策划，AI都能为您提供专业的建议和方案。</p>
              </div>
            </div>
            <div class="card" 
                 :class="{ 'active': activeCard === 1 }"
                 @mouseenter="handleCardHover(1)"
                 @mouseleave="handleCardLeave">
              <div class="img-box">
                <img src="/images/card1/2.png" alt="知识库管理" class="card-img">
              </div>
              <div class="text-box">
                <h2>本地资料库</h2>
                <p>上传管理教学资料，支持全文和相似度检索。轻松构建您的专属本地资料库，智能分类管理各类教学资源。强大的搜索功能帮助您快速找到所需资料，提升备课效率。</p>
              </div>
            </div>
            <div class="card" 
                 :class="{ 'active': activeCard === 2 }"
                 @mouseenter="handleCardHover(2)"
                 @mouseleave="handleCardLeave">
              <div class="img-box">
                <img src="/images/card1/3.png" alt="课件预览生成" class="card-img">
              </div>
              <div class="text-box">
                <h2>课件预览生成</h2>
                <p>一键生成完整课件，支持在线预览和编辑。AI智能生成美观实用的教学课件，包含教学目标、重点难点、教学过程等完整结构。支持实时预览和灵活编辑，让课件制作更高效。</p>
              </div>
            </div>
            <div class="card" 
                 :class="{ 'active': activeCard === 3 }"
                 @mouseenter="handleCardHover(3)"
                 @mouseleave="handleCardLeave">
              <div class="img-box">
              <img src="/images/card1/3.png" alt="个人主页" class="card-img">
            </div>
              <div class="text-box">
                <h2>个人主页</h2>
                <p>基础信息设置作为PPT前置条件默认条件，直接完成PPT署名和水印等工作，进一步简化教师工作。历史课件功能支持储存历史课件，方便查询和多次使用，记录教学工作。</p>
              </div>
            </div>
          </div>
          
          <div v-if="!isLoggedIn" class="cta-section">
            <button @click="goToLogin" class="cta-btn">
              开始体验
            </button>
          </div>
        </div>
      </transition>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import store from '../store'
import SplashPage from './SplashPage.vue'

const router = useRouter()
const route = useRoute()
const isLoggedIn = computed(() => store.isLoggedIn)
const showSplash = ref(true)
const activeCard = ref(0)
let autoPlayInterval = null
let splashTimeout = null

const goToLogin = () => {
  router.push('/login')
}

const handleCardHover = (index) => {
  clearInterval(autoPlayInterval)
  activeCard.value = index
}

const handleCardLeave = () => {
  startAutoPlay()
}

const startAutoPlay = () => {
  autoPlayInterval = setInterval(() => {
    activeCard.value = (activeCard.value + 1) % 4
  }, 3000)
}

const resetAndStartSplash = () => {
  if (splashTimeout) {
    clearTimeout(splashTimeout)
  }
  if (autoPlayInterval) {
    clearInterval(autoPlayInterval)
  }
  
  if (isLoggedIn.value && route.path === '/') {
    router.replace('/introduction')
    return
  }

  if (!isLoggedIn.value && route.path === '/') {
    showSplash.value = true
    splashTimeout = setTimeout(() => {
      showSplash.value = false
      startAutoPlay()
    }, 3000)
  } else {
    showSplash.value = false
    startAutoPlay()
  }
}

onMounted(() => {
  resetAndStartSplash()
})

watch([isLoggedIn, () => route.path], () => {
  resetAndStartSplash()
})

onUnmounted(() => {
  clearInterval(autoPlayInterval)
  if (splashTimeout) {
    clearTimeout(splashTimeout)
  }
})
</script>

<style scoped>
.home-page {
  min-height: 100vh;
  height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  overflow: hidden;
}

.splash-wrapper {
  width: 100%;
  height: 100%;
  display: flex;
  justify-content: center;
  align-items: center;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.5s ease-in-out;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

.home-page.logged-in {
  height: 100%;
  min-height: 0;
}

.main-content {
  position: relative;
  z-index: 1;
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.content-wrapper {
  border-radius: 4px;
  padding: 0px 20px 20px 20px;
  width: 100%;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
}

.content-wrapper:not(.logged-in) {
  height: calc(100vh - 60px);
  max-width: none;
  background: transparent;
  box-shadow: none;
}

.content-wrapper.logged-in {
  padding-top: 0;
  height: calc(100vh - 120px);
  max-width: none;
  background: rgba(255, 255, 255, 0.95);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
  min-height: 0;
}

.hero-section {
  text-align: center;
  /* margin-bottom: 15px; */
  /* margin-top: 30px; */
}

.title {
  font-size: 42px;
  font-weight: 700;
  color: #1a1a1a;
  /* margin-bottom: 12px; */
}

.slogan {
  font-size: 20px;
  color: #46736d;
  font-weight: 500;
}

.features-section {
  display: flex;
  justify-content: center;
  align-items: flex-start;
  /* gap: 30px; */
  margin-bottom: 10px;
  min-height: 420px;
  height: 420px;
  overflow: hidden;
}

.card {
  position: relative;
  max-width: 300px;
  height: 215px;
  background: rgba(255, 255, 255, 0.7);
  margin: 50px 15px 30px;
  padding: 20px 15px;
  border-radius: 10px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
  cursor: pointer;
  transform-style: preserve-3d;
  perspective: 1000px;
  flex-shrink: 0;
}

.home-page.logged-in .card {
  background: #cce4db;
}

.card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  border-radius: 20px;
  background: linear-gradient(45deg, transparent, rgba(13, 84, 122, 0.03), transparent);
  opacity: 0;
  transition: opacity 0.4s ease;
}

.card:hover,
.card.active {
  height: 360px;
  transform: translateY(-10px) rotateX(2deg);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.12);
}

.card:hover::before,
.card.active::before {
  opacity: 1;
}

.card .img-box {
  position: relative;
  width: 220px;
  height: 160px;
  border-radius: 16px;
  overflow: hidden;
  top: -50px;
  left: 25px;
  box-shadow: none;
  z-index: 2;
  background: transparent;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
}

.card:hover .img-box,
.card.active .img-box {
  transform: scale(1.05) rotate(-2deg);
  box-shadow: none;
}

.card-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  border-radius: 16px;
}

.card .text-box {
  position: relative;
  margin-top: -110px;
  padding: 0px 15px;
  text-align: center;
  color: #111;
  visibility: hidden;
  opacity: 0;
  transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
}

.card:hover .text-box,
.card.active .text-box {
  visibility: visible;
  opacity: 1;
  margin-top: -10px;
  transition-delay: 0.15s;
}

.card .text-box h2 {
  font-size: 22px;
  font-weight: 700;
  color: #000;
  margin-bottom: 12px;
  letter-spacing: 0.5px;
}

.card .text-box p {
  text-align: left;
  line-height: 1.7;
  margin-top: 12px;
  font-size: 14px;
  color: #4a5568;
  font-weight: 400;
}

.cta-section {
  text-align: center;
}

.cta-btn {
  padding: 12px 48px;
  background: #312f2f;
  color: white;
  /* border: 1px solid #a3cfbb; */
  border-radius: 24px;
  font-size: 18px;
  font-weight: 600;
  cursor: pointer;
  transition: opacity 0.2s ease;
}

.cta-btn:hover {
  opacity: 0.9;
}
</style>
