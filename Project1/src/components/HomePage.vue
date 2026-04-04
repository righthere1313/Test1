<template>
  <div class="home-page" :class="{ 'logged-in': isLoggedIn }">
    <div class="main-content">
      <transition name="fade" mode="out-in">
        <div v-if="showSplash && !isLoggedIn" key="splash" class="splash-wrapper">
          <SplashPage />
        </div>
        <div v-else key="intro" class="content-wrapper" :class="{ 'logged-in': isLoggedIn }">
          <div class="carousel-container" @wheel.passive="false" @wheel="handleWheel">
            <div class="carousel-wrapper" :style="{ transform: `translateY(-${currentPage * 100}%)` }">
              <div class="carousel-page">
                <div class="page-content">
                  <div class="hero-section">
                    <h1 class="title">AI互动式教学智能体</h1>
                    <p class="slogan">让教学更简单，让课堂更精彩</p>
                  </div>
                  
                  <div class="features-section">
                    <div class="card active">
                      <div class="img-box">
                        <img src="/images/card1/1.png" alt="智能对话设计" class="card-img">
                      </div>
                      <div class="text-box">
                        <h2>智能对话设计</h2>
                        <p>与AI智能体自然对话，经过多轮对话交互，根据您的教学需求智能调整个性化内容。无论是教学设计、教案撰写还是课堂活动策划，为您提供专业的建议和方案。</p>
                      </div>
                    </div>
                    <div class="card active">
                      <div class="img-box">
                        <img src="/images/card1/2.png" alt="知识库管理" class="card-img">
                      </div>
                      <div class="text-box">
                        <h2>本地资料库</h2>
                        <p>上传管理各类教学资料，轻松构建您的专属资料库。支持全文和相似度检索，强大的搜索功能帮助快速找到所需资料，提升备课效率，智能管理资料。</p>
                      </div>
                    </div>
                    <div class="card active">
                      <div class="img-box">
                        <img src="/images/card1/3.png" alt="课件预览生成" class="card-img">
                      </div>
                      <div class="text-box">
                        <h2>课件预览生成</h2>
                        <p>一键生成美观实用的教学课件，包含教学目标、重点难点、教学过程等完整结构。支持实时预览和灵活编辑，让课件制作更高效。</p>
                      </div>
                    </div>
                    <div class="card active">
                      <div class="img-box">
                        <img src="/images/card1/4.png" alt="历史管理" class="card-img">
                      </div>
                      <div class="text-box">
                        <h2>个人主页与历史</h2>
                        <p>基础信息设置作为课件前置条件，历史课件及配套资料按时间排序，方便查看管理，记录工作细节。</p>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
              
              <div class="carousel-page">
                <div class="page-content drawer-content">
                  <DrawerCarousel />
                </div>
              </div>
              
              <div class="carousel-page">
                <div class="page-content send-message-page">
                  <SendMessage :auto-expand="currentPage === 2" :hide-start-button="isLoggedIn" @start="goToLogin" />
                </div>
              </div>
            </div>
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
import DrawerCarousel from './DrawerCarousel.vue'
import SendMessage from './SendMessage.vue'

const router = useRouter()
const route = useRoute()
const isLoggedIn = computed(() => store.isLoggedIn)
const showSplash = ref(true)
const currentPage = ref(0)
const totalPages = 3
// let autoPlayInterval = null
let carouselInterval = null
let splashTimeout = null

const goToLogin = () => {
  router.push('/login')
}

// const handleCardHover = (index) => {
//   clearInterval(autoPlayInterval)
//   activeCard.value = index
// }

// const handleCardLeave = () => {
//   startAutoPlay()
// }

// const startAutoPlay = () => {
//   autoPlayInterval = setInterval(() => {
//     activeCard.value = (activeCard.value + 1) % 4
//   }, 3000)
// }

// const startCarousel = () => {
//   if (currentPage.value >= totalPages - 1) return
//   carouselInterval = setInterval(() => {
//     if (currentPage.value < totalPages - 1) {
//       currentPage.value++
//     } else {
//       clearInterval(carouselInterval)
//     }
//   }, 5000)
// }

// const pauseCarousel = () => {
//   clearInterval(carouselInterval)
// }

// const resumeCarousel = () => {
//   if (currentPage.value < totalPages - 1) {
//     startCarousel()
//   }
// }

let wheelTimeout = null
const handleWheel = (event) => {
  event.preventDefault()
  if (wheelTimeout) return
  
  if (event.deltaY > 0) {
    if (currentPage.value < totalPages - 1) {
      currentPage.value++
      // if (currentPage.value >= totalPages - 1) {
      //   clearInterval(carouselInterval)
      // }
    }
  } else if (event.deltaY < 0) {
    if (currentPage.value > 0) {
      currentPage.value--
      // if (currentPage.value < totalPages - 1) {
      //   clearInterval(carouselInterval)
      //   startCarousel()
      // }
    }
  }
  
  wheelTimeout = setTimeout(() => {
    wheelTimeout = null
  }, 800)
}

const resetAndStartSplash = () => {
  if (splashTimeout) {
    clearTimeout(splashTimeout)
  }
  // if (autoPlayInterval) {
  //   clearInterval(autoPlayInterval)
  // }
  // if (carouselInterval) {
  //   clearInterval(carouselInterval)
  // }
  
  currentPage.value = 0
  
  // 已登录状态下直接显示卡片介绍页面，不显示splashpage
  if (isLoggedIn.value) {
    showSplash.value = false
    // startAutoPlay()
    // 如果在首页，重定向到介绍页
    if (route.path === '/') {
      router.replace('/introduction')
    }
    return
  }

  // 未登录状态下，只在首页显示splashpage
  if (!isLoggedIn.value && route.path === '/') {
    showSplash.value = true
    splashTimeout = setTimeout(() => {
      showSplash.value = false
      // startAutoPlay()
      // startCarousel()
    }, 2000)
  } else {
    showSplash.value = false
    // startAutoPlay()
    // startCarousel()
  }
}

onMounted(() => {
  resetAndStartSplash()
})

watch([isLoggedIn, () => route.path], () => {
  resetAndStartSplash()
})

onUnmounted(() => {
  // clearInterval(autoPlayInterval)
  // clearInterval(carouselInterval)
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
  padding: 0px;
  width: 100%;
  height: 100%;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
}

.content-wrapper:not(.logged-in) {
  height: calc(100vh - 110px);
  max-width: none;
  background: transparent;
  box-shadow: none;
}

.content-wrapper.logged-in {
  padding-top: 0;
  height: calc(100vh - 110px);
  max-width: none;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
  min-height: 0;
}

.carousel-container {
  width: 100%;
  height: 100%;
  overflow: hidden;
  position: relative;
}

.carousel-wrapper {
  display: flex;
  flex-direction: column;
  transition: transform 0.8s ease-in-out;
  height: 100%;
}

.carousel-page {
  flex-shrink: 0;
  height: 100%;
  width: 100%;
}

.page-content {
  width: 100%;
  height: 100%;
  padding: 20px;
  /* background: rgba(255, 255, 255, 0.85); */
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  overflow-y: auto;
  box-sizing: border-box;
}

.page-content.drawer-content {
  padding: 0;
  background: transparent;
}

.page-content.send-message-page {
  padding: 20px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  gap: 30px;
  overflow: hidden;
}

.page-content.send-message-page .cta-section {
  flex-shrink: 0;
  text-align: center;
}

.hero-section {
  text-align: center;
}

.title {
  font-size: 42px;
  font-weight: 700;
  color: #1a1a1a;
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
  margin-bottom: 10px;
  min-height: 480px;
  height: 480px;
  overflow: hidden;
}

.card {
  position: relative;
  max-width: 280px;
  height: 360px;
  background: rgba(255, 255, 255, 0.7);
  margin: 50px 15px 30px;
  padding: 20px 15px;
  border-radius: 10px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.12);
  transform: translateY(-10px) rotateX(2deg);
  transform-style: preserve-3d;
  perspective: 1000px;
  flex-shrink: 0;
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
  opacity: 1;
  transition: opacity 0.4s ease;
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
  transform: scale(1.05) rotate(-2deg);
}

.card-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  border-radius: 16px;
}

.card .text-box {
  position: relative;
  margin-top: -10px;
  padding: 0px 15px;
  text-align: center;
  color: #111;
  visibility: visible;
  opacity: 1;
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
  border-radius: 24px;
  font-size: 18px;
  font-weight: 600;
  cursor: pointer;
  transition: opacity 0.2s ease;
}

.empty-page-content {
  text-align: center;
}

.empty-page-content h2 {
  font-size: 36px;
  color: #46736d;
  margin-bottom: 20px;
}

.empty-page-content p {
  font-size: 18px;
  color: #6c757d;
}
</style>
