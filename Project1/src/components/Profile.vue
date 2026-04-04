<template>
  <div class="profile-page">
    <div class="profile-container">
      <div class="profile-header">
        <h2>个人主页</h2>
      </div>
      <div class="profile-content">
        <div class="profile-left">
          <div class="profile-card">
            <div class="avatar-section">
              <div class="avatar">
                <img v-if="store.user.avatar" :src="store.user.avatar" alt="头像" class="avatar-img">
              </div>
            </div>
            <div class="username-section">
              <h3 class="username">{{ store.user.username }}</h3>
            </div>
            <div class="info-section">
              <div class="info-item">
                <span class="info-label">教师姓名：</span>
                <span class="info-value">{{ store.user.teacherName || '未设置' }}</span>
              </div>
              <div class="info-item">
                <span class="info-label">教学学科：</span>
                <span class="info-value">{{ store.user.subject || '未设置' }}</span>
              </div>
              <div class="info-item">
                <span class="info-label">学校名称：</span>
                <span class="info-value">{{ store.user.schoolName || '未设置' }}</span>
              </div>
            </div>
            <div class="action-buttons">
              <button @click="goToEdit" class="btn-edit">编辑信息</button>
              <button @click="handleLogout" class="btn-logout">退出登录</button>
            </div>
          </div>
        </div>
        <div class="profile-divider"></div>
        <div class="profile-right">
          <transition name="fade" mode="out-in">
            <div v-if="!showEditor" :key="'stats'" class="stats-container">
              <div class="stats-top">
                <div class="carousel-card">
                  <h4>最新生成课件</h4>
                  <div class="carousel-container">
                    <button @click="prevSlide" class="carousel-btn left">
                      <span class="carousel-arrow">◀</span>
                    </button>
                    <div class="carousel-wrapper">
                      <div class="carousel-track" :style="{ transform: `translateX(-${currentSlide * 100}%)` }">
                        <div 
                          v-for="(course, index) in carouselCourses" 
                          :key="index"
                          class="carousel-slide"
                        >
                          <div class="carousel-left">
                            <h5 class="carousel-title">{{ course.title }}</h5>
                            <p class="carousel-desc">{{ course.desc }}</p>
                            <span class="carousel-date">{{ course.date }}</span>
                          </div>
                          <div class="carousel-right">
                            <div class="ppt-cover" :style="{ backgroundImage: course.cover ? `url(${course.cover})` : 'none' }">
                              <span v-if="!course.cover" class="cover-placeholder">PPT封面</span>
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                    <button @click="nextSlide" class="carousel-btn right">
                      <span class="carousel-arrow">▶</span>
                    </button>
                  </div>
                  <div class="carousel-dots">
                    <span 
                      v-for="(_, index) in carouselCourses" 
                      :key="index"
                      class="dot"
                      :class="{ active: currentSlide === index }"
                      @click="goToSlide(index)"
                    ></span>
                  </div>
                </div>
                <div class="chart-card">
                  <div class="card-header">
                    <h4>课件生成统计</h4>
                  </div>
                  <div class="chart-wrapper" :style="{ width: '330px', height: '190px' }">
                    <canvas ref="yearlyChart"></canvas>
                  </div>
                </div>
              </div>
              <div class="stats-bottom">
                <div class="line-chart-card">
                  <div class="card-header">
                    <h4>使用频率时间轴</h4>
                  </div>
                  <div class="chart-wrapper" :style="{ width: '800px', height: '375px' }">
                    <canvas ref="frequencyChart"></canvas>
                  </div>
                </div>
                <div class="side-card">
                  <div class="sticky-note-header">
                    <div class="sticky-pin"></div>
                  </div>
                  <div class="stat-items">
                    <div class="stat-item note-1">
                      <span class="stat-number">{{ totalCoursewares }}</span>
                      <span class="stat-label">总课件数</span>
                    </div>
                    <div class="stat-item note-2">
                      <span class="stat-number">{{ thisMonthCount }}</span>
                      <span class="stat-label">本月生成</span>
                    </div>
                    <div class="stat-item note-3">
                      <span class="stat-number">{{ avgPerWeek }}</span>
                      <span class="stat-label">周均生成</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            <ProfileEditor 
              v-else 
              :key="'editor'"
              @save="handleSave"
              @cancel="handleCancelEdit"
            />
          </transition>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { Chart, registerables } from 'chart.js'
import store from '../store'
import ProfileEditor from './ProfileEditor.vue'

Chart.register(...registerables)

const router = useRouter()
const showEditor = ref(false)
const yearlyChart = ref(null)
const frequencyChart = ref(null)
let yearlyChartInstance = null
let frequencyChartInstance = null

const currentSlide = ref(0)
let autoSlideInterval = null

const carouselCourses = ref([
  {
    title: '勾股定理教学课件',
    desc: '通过生动的几何图形和实例，深入浅出地讲解勾股定理的应用',
    date: '2026-03-15',
    cover: null
  },
  {
    title: '二次根式复习课',
    desc: '系统复习二次根式的概念、性质和运算，通过大量例题帮助学生巩固知识点',
    date: '2026-03-10',
    cover: null
  },
  {
    title: '函数图像分析',
    desc: '学习如何分析和绘制各种函数的图像，包括一次函数、二次函数、反比例函数等',
    date: '2026-02-28',
    cover: null
  },
  {
    title: '三角函数入门',
    desc: '介绍三角函数的基本概念，包括正弦、余弦、正切函数及其在直角三角形中的应用',
    date: '2026-02-20',
    cover: null
  }
])

const yearlyData = {
  labels: ['2021', '2022', '2023', '2024', '2025', '2026'],
  data: [12, 19, 25, 38, 50, 12]
}

const frequencyData = {
  labels: ['1月', '2月', '3月', '4月', '5月', '6月', '7月', '8月', '9月', '10月', '11月', '12月'],
  data: [3, 5, 8, 12, 9, 15, 7, 10, 14, 11, 8, 5]
}

const totalCoursewares = ref(156)
const thisMonthCount = ref(12)
const avgPerWeek = ref(3)

const goToEdit = () => {
  showEditor.value = true
}

const handleSave = () => {
  showEditor.value = false
}

const handleCancelEdit = () => {
  showEditor.value = false
}

const handleLogout = () => {
  if (confirm('确定要退出登录吗？')) {
    store.logout()
    router.push('/')
  }
}

const prevSlide = () => {
  currentSlide.value = currentSlide.value === 0 ? carouselCourses.value.length - 1 : currentSlide.value - 1
}

const nextSlide = () => {
  currentSlide.value = currentSlide.value === carouselCourses.value.length - 1 ? 0 : currentSlide.value + 1
}

const goToSlide = (index) => {
  currentSlide.value = index
}

const startAutoSlide = () => {
  autoSlideInterval = setInterval(() => {
    nextSlide()
  }, 5000)
}

const stopAutoSlide = () => {
  if (autoSlideInterval) {
    clearInterval(autoSlideInterval)
  }
}

const initYearlyChart = () => {
  if (!yearlyChart.value) return
  
  const ctx = yearlyChart.value.getContext('2d')
  
  if (yearlyChartInstance) {
    yearlyChartInstance.destroy()
  }
  
  yearlyChartInstance = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: yearlyData.labels,
      datasets: [{
        label: '课件生成数',
        data: yearlyData.data,
        backgroundColor: '#8ab4aa',
        borderRadius: 8,
        borderSkipped: false,
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          display: false
        }
      },
      scales: {
        y: {
          beginAtZero: true,
          grid: {
            color: '#e9ecef'
          },
          ticks: {
            color: '#495057',
            font: { size: 11 }
          }
        },
        x: {
          grid: {
            display: false
          },
          ticks: {
            color: '#495057',
            font: { size: 11 }
          }
        }
      }
    }
  })
}

const initFrequencyChart = () => {
  if (!frequencyChart.value) return
  
  const ctx = frequencyChart.value.getContext('2d')
  
  if (frequencyChartInstance) {
    frequencyChartInstance.destroy()
  }
  
  frequencyChartInstance = new Chart(ctx, {
    type: 'line',
    data: {
      labels: frequencyData.labels,
      datasets: [{
        label: '使用频率',
        data: frequencyData.data,
        borderColor: '#8ab4aa',
        backgroundColor: 'rgba(138, 180, 170, 0.1)',
        borderWidth: 3,
        fill: true,
        tension: 0.4,
        pointBackgroundColor: '#8ab4aa',
        pointBorderColor: '#fff',
        pointBorderWidth: 2,
        pointRadius: 5,
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          display: false
        }
      },
      scales: {
        y: {
          beginAtZero: true,
          grid: {
            color: '#e9ecef'
          },
          ticks: {
            color: '#495057'
          }
        },
        x: {
          grid: {
            display: false
          },
          ticks: {
            color: '#495057'
          }
        }
      }
    }
  })
}

onMounted(() => {
  nextTick(() => {
    initYearlyChart()
    initFrequencyChart()
    startAutoSlide()
  })
})

onUnmounted(() => {
  stopAutoSlide()
})
</script>

<style scoped>
.profile-page {
  width: 100%;
  height: calc(100vh - 110px);
  display: flex;
  align-items: flex-start;
  justify-content: center;
  position: relative;
  z-index: 1;
}

.profile-container {
  width: 100%;
  height: 100%;
  background: white;
  border-radius: 4px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.12);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.profile-header {
  background: #ffffff;
  padding: 16px 32px;
  border-bottom: 1px solid #e9ecef;
}

.profile-header h2 {
  color: #000000;
  font-size: 22px;
  font-weight: 700;
  margin: 0;
}

.profile-content {
  flex: 1;
  display: flex;
  overflow: hidden;
}

.profile-left {
  width: 280px;
  padding: 24px;
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
}

.profile-card {
  background: #f8f9fa;
  border-radius: 12px;
  padding: 20px;
  display: flex;
  flex-direction: column;
  align-items: center;
  height: 100%;
}

.avatar-section {
  margin-bottom: 16px;
}

.avatar {
  width: 100px;
  height: 100px;
  border-radius: 50%;
  background: #bdd6cd;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  border: 3px solid #8ab4aa;
}

.avatar-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.username-section {
  margin-bottom: 20px;
}

.username {
  font-size: 18px;
  font-weight: 600;
  color: #212529;
  margin: 0;
}

.info-section {
  width: 100%;
  margin-bottom: auto;
}

.info-item {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  padding: 6px 0;
  border-bottom: 1px solid #e9ecef;
}

.info-label {
  color: #6c757d;
}

.info-value {
  color: #212529;
  font-weight: 500;
  text-align: right;
  flex: 1;
  margin-left: 8px;
}

.action-buttons {
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-top: 16px;
}

.btn-edit,
.btn-logout {
  padding: 10px 16px;
  border: none;
  border-radius: 16px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: opacity 0.2s ease;
  width: 100%;
}

.btn-edit {
  background: #8ab4aa;
  color: white;
}


.btn-logout {
  background: #312f2f;
  color: white;
}


.profile-divider {
  width: 2px;
  background: #bdd6cd;
  flex-shrink: 0;
}

.profile-right {
  flex: 1;
  display: flex;
  overflow: hidden;
  position: relative;
}

.stats-container {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  padding: 18px 24px;
  overflow-y: auto;
}

.stats-top {
  position: absolute;
  top: 1px;
  left: 24px;
  right: 24px;
  display: flex;
  gap: 24px;
  min-height: 220px;
}

.carousel-card {
  position: absolute;
  top: 0;
  left: 0;
  right: 424px;
  background: #f8f9fa;
  border-radius: 16px;
  padding: 16px;
  display: flex;
  flex-direction: column;
  height: 220px;
}

.chart-card {
  position: absolute;
  top: 0;
  right: 0;
  width: 370px;
  background: #f8f9fa;
  border-radius: 16px;
  padding: 16px;
  display: flex;
  flex-direction: column;
  height: 220px;
}

.stats-bottom {
  position: absolute;
  top: 258px;
  left: 24px;
  right: 24px;
  bottom: 0;
  display: flex;
  gap: 24px;
}

.carousel-card {
  flex: 1;
  background: #f8f9fa;
  border-radius: 16px;
  padding: 16px;
  display: flex;
  flex-direction: column;
}

.carousel-card h4 {
  font-size: 15px;
  font-weight: 600;
  color: #212529;
  margin: 0 0 12px 0;
}

.carousel-container {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 12px;
  min-height: 0;
}

.carousel-btn {
  width: 32px;
  height: 32px;
  border: none;
  background: white;
  border-radius: 50%;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  transition: all 0.2s ease;
  flex-shrink: 0;
}


.carousel-arrow {
  font-size: 14px;
  color: #495057;
}

.carousel-wrapper {
  flex: 1;
  overflow: hidden;
  width: 200px;
  border-radius: 12px;
  min-height: 0;
}

.carousel-track {
  display: flex;
  transition: transform 0.5s cubic-bezier(0.4, 0, 0.2, 1);
  height: 100%;
}

.carousel-slide {
  min-width: 100%;
  height: 100%;
  padding: 0 20px;
  box-sizing: border-box;
  display: flex;
  align-items: center;
}

.carousel-left {
  flex: 1;
  background: #bbd6cd;
  border: 2px dashed #64a596;
  border-radius: 12px 0 0 12px;
  min-height: 120px;
  max-height: 120px;
  padding: 16px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  box-sizing: border-box;
}

.carousel-right {
  flex: 0 0 140px;
  min-height: 110px;
  max-height: 110px;
  border-radius: 0 12px 12px 0;
  overflow: hidden;
  border: 2px dashed #64a596;
  border-left: none;
  box-sizing: border-box;
}

.ppt-cover {
  width: 100%;
  height: 100%;
  background: #e9ecef;
  display: flex;
  align-items: center;
  justify-content: center;
  background-size: cover;
  background-position: center;
}

.cover-placeholder {
  font-size: 12px;
  color: #6c757d;
}

.carousel-title {
  font-size: 15px;
  font-weight: 600;
  color: #212529;
  margin: 0 0 8px 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.carousel-desc {
  font-size: 12px;
  color: #6c757d;
  margin: 0 0 6px 0;
  line-height: 1.4;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.carousel-date {
  font-size: 11px;
  color: #6c757d;
}

.carousel-dots {
  display: flex;
  justify-content: center;
  gap: 8px;
  margin-top: 12px;
}

.dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #dee2e6;
  cursor: pointer;
  transition: all 0.3s ease;
}

.dot.active {
  background: #8ab4aa;
  width: 24px;
  border-radius: 4px;
}

.dot:hover:not(.active) {
  background: #adb5bd;
}

.chart-card {
  flex: 0 0 auto;
  width: 370px;
  background: #f8f9fa;
  border-radius: 16px;
  padding: 16px;
  display: flex;
  flex-direction: column;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}

.card-header h4 {
  font-size: 15px;
  font-weight: 600;
  color: #212529;
  margin: 0;
}

.chart-wrapper {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 0;
}

.chart-wrapper canvas {
  width: 100% !important;
  height: 100% !important;
}

.stats-bottom {
  flex: 1;
  min-height: 0;
  display: flex;
  gap: 24px;
}

.line-chart-card {
  position: absolute;
  top: -10px;
  left: 0;
  right: 228px;
  bottom: 10px;
  background: #f8f9fa;
  border-radius: 16px;
  padding: 16px;
  display: flex;
  flex-direction: column;
}

.line-chart-card h4 {
  font-size: 15px;
  font-weight: 600;
  color: #212529;
  margin: 0 0 12px 0;
}

.side-card {
  position: absolute;
  top: -30px;
  right: -870px;
  width: 180px;
  bottom: 0;
  background: #f5f5f5;
  border-radius: 12px;
  padding: 16px;
  display: flex;
  flex-direction: column;
  position: relative;
}

.sticky-note-header {
  display: flex;
  justify-content: center;
  margin-bottom: 8px;
}

.sticky-pin {
  width: 24px;
  height: 24px;
  background: #64a596;
  border-radius: 50%;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
}

.stat-items {
  display: flex;
  flex-direction: column;
  gap: 12px;
  flex: 1;
  justify-content: center;
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: 10px 10px;
  border-radius: 4px;
  position: relative;
  box-shadow: 2px 2px 8px rgba(0, 0, 0, 0.1);
}

.stat-item.note-1 {
  background: #fff9c4;
  transform: rotate(-1deg);
}

.stat-item.note-2 {
  background: #c8e6c9;
  transform: rotate(1deg);
}

.stat-item.note-3 {
  background: #bbdefb;
  transform: rotate(-0.5deg);
}

.stat-item::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 24px;
  background: rgba(0, 0, 0, 0.05);
  border-radius: 4px 4px 0 0;
}

.stat-number {
  font-size: 24px;
  font-weight: 700;
  color: #212529;
  position: relative;
  z-index: 1;
}

.stat-label {
  font-size: 11px;
  color: #495057;
  position: relative;
  z-index: 1;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
