<template>
  <div class="history-generation-page">
    <div class="history-container">
      <div class="history-header">
        <h2>历史生成</h2>
      </div>
      <div class="history-content">
        <div class="history-top">
          <button @click="prevYear" class="nav-btn left" :disabled="activeIndex === 0">
            <span class="nav-arrow">◀</span>
          </button>
          <div class="timeline-container" ref="timelineContainer">
            <div class="timeline-line"></div>
            <div class="timeline-wrapper" :style="{ transform: `translateX(${translateX}px)` }">
              <div
                v-for="(year, index) in yearData"
                :key="year.year"
                class="year-card"
                :class="{ active: activeIndex === index }"
                :style="{ transform: `scale(${getScale(index)})`, zIndex: getZIndex(index) }"
                @click="goToYear(index)"
              >
                <div class="year-number">{{ year.year }}</div>
                <div class="year-count">{{ year.count }} 个课件</div>
              </div>
            </div>
          </div>
          <button @click="nextYear" class="nav-btn right" :disabled="activeIndex === yearData.length - 1">
            <span class="nav-arrow">▶</span>
          </button>
        </div>
        <div class="history-bottom">
          <div class="left-column">
            <div class="column-header">
              <h3 class="column-title">{{ selectedYear }} 年课件</h3>
              <button 
                @click="toggleDeleteMode" 
                class="delete-mode-btn"
                :class="{ active: isDeleteMode }"
              >
                {{ isDeleteMode ? '退出删除' : '删除' }}
              </button>
            </div>
            <div class="content-grid-wrapper">
              <div class="content-grid">
                <div
                  v-for="(item, index) in filteredCoursewares"
                  :key="index"
                  class="content-card"
                  :class="{ selected: selectedContent?.id === item.id }"
                  @click="isDeleteMode ? null : selectContent(item)"
                >
                  <button 
                    v-if="isDeleteMode" 
                    @click.stop="deleteCourseware(item)" 
                    class="card-delete-btn"
                  >
                    <span class="delete-icon">×</span>
                  </button>
                  <div class="card-image">
                    <img src="/images/ppt.png" alt="课件预览" class="preview-img">
                  </div>
                  <div class="card-info">
                    <h5 class="card-title">{{ item.title }}</h5>
                    <div class="card-meta">
                      <span class="card-date">{{ item.date }}</span>
                      <span class="card-type" :class="item.type">{{ item.typeLabel }}</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
          <div class="right-column">
            <transition name="fade" mode="out-in">
              <div v-if="selectedContent" :key="selectedContent.title" class="detail-panel">
                <h3 class="detail-title">{{ selectedContent.title }}</h3>
                <div class="detail-info">
                  <p class="detail-date">生成时间：{{ selectedContent.date }}</p>
                  <p class="detail-desc">{{ selectedContent.description }}</p>
                </div>
                <div class="related-content">
                  <h4 class="related-title">配套资源</h4>
                  <div class="related-list">
                    <div 
                      v-if="selectedContent.pptFilename" 
                      class="related-item"
                      @click="handleResourceClick('courseware', selectedContent.pptFilename, selectedContent.generation)"
                    >
                      <span class="related-type plan">PPT课件</span>
                      <span class="related-name">{{ selectedContent.pptFilename }}</span>
                    </div>
                    <div 
                      v-if="selectedContent.plan" 
                      class="related-item"
                      @click="handleResourceClick('plan', selectedContent.plan, selectedContent.generation)"
                    >
                      <span class="related-type plan">教案</span>
                      <span class="related-name">{{ selectedContent.plan }}</span>
                    </div>
                  </div>
                </div>
              </div>
              <div v-else key="empty" class="empty-detail">
                <p class="empty-text">点击左侧课件查看</p>
              </div>
            </transition>
            <img v-if="!selectedContent" src="/images/插画1.png" alt="插画" class="illustration-1">
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import store from '../store'

const router = useRouter()
const timelineContainer = ref(null)
const activeIndex = ref(0)
const translateX = ref(0)
const selectedContent = ref(null)
const isDeleteMode = ref(false)

const subjects = ['数学', '语文', '英语', '物理', '化学', '生物', '历史', '地理', '政治']
const courseTitles = [
  '人工智能基础入门',
  '机器学习算法原理',
  '深度学习框架应用',
  '数据结构与算法',
  '软件工程实践',
  '计算机网络基础',
  '数据库系统设计',
  '前端开发技术',
  '后端系统架构',
  '云计算与大数据',
  '人工智能伦理',
  '软件工程方法论',
  '机器学习模型优化',
  '深度学习图像处理',
  '自然语言处理技术',
  '计算机视觉应用',
  '人工智能安全',
  '软件工程质量保证',
  'DevOps实践指南',
  '软件测试技术'
]
const descriptions = [
  '介绍人工智能的基本概念、发展历程和应用领域，帮助学生建立AI认知框架',
  '深入讲解机器学习的核心算法原理，包括监督学习、无监督学习和强化学习',
  '实践深度学习框架的应用，包括神经网络搭建、模型训练和部署',
  '系统学习数据结构与算法，提升编程能力和问题解决能力',
  '探索软件工程的实践方法，包括需求分析、设计、编码和测试',
  '了解计算机网络的基本原理和协议，掌握网络通信技术',
  '学习数据库系统的设计原理和优化方法，提高数据管理能力',
  '掌握前端开发技术，包括HTML、CSS、JavaScript和现代前端框架',
  '设计后端系统架构，包括API设计、数据库交互和服务部署',
  '探索云计算与大数据技术，理解分布式系统原理',
  '探讨人工智能伦理问题，包括隐私保护、算法偏见和社会责任',
  '学习软件工程方法论，包括敏捷开发、DevOps和持续集成',
  '掌握机器学习模型优化技术，提高模型性能和泛化能力',
  '实践深度学习在图像处理中的应用，包括图像分类和目标检测',
  '探索自然语言处理技术，包括文本分类、情感分析和机器翻译',
  '学习计算机视觉应用，包括图像识别、人脸识别和视频分析',
  '了解人工智能安全问题，包括对抗攻击和防御策略',
  '掌握软件工程质量保证方法，包括代码审查、测试和质量评估',
  '实践DevOps流程，包括自动化部署、监控和持续交付',
  '学习软件测试技术，包括单元测试、集成测试和系统测试'
]

const generateMockData = () => {
  const yearCounts = {
    '2021': 12,
    '2022': 19,
    '2023': 25,
    '2024': 38,
    '2025': 50,
    '2026': 12
  }
  
  const mockHistory = []
  let idCounter = 1
  const used2026Titles = new Set()
  
  Object.entries(yearCounts).forEach(([year, count]) => {
    for (let i = 0; i < count; i++) {
      let month, day, date, titleIndex, subjectIndex, hasPpt, hasDocx
      
      if (year === '2026' && i === count - 1) {
        // 2026年最后一个数据固定为人工智能概要
        month = 12
        day = 31
        date = new Date(year, month - 1, day)
        subjectIndex = 0 // 数学
        hasPpt = true
        hasDocx = true
        
        // 固定数据
        mockHistory.push({
          id: `gen_${idCounter++}`,
          timestamp: date.getTime(),
          sessionId: 'mock_session',
          pptFilename: '人工智能概要.pptx',
          docxFilename: '人工智能概要.docx',
          pptPreviewId: 'pv_ai_summary',
          pptPreviewPages: Array.from({ length: 12 }, (_, j) => j + 1),
          requirements: {
            subject: subjects[subjectIndex],
            content: '全面介绍人工智能的发展历程、核心技术和应用场景，帮助学生建立对AI技术的完整认知框架。内容包括AI的定义与分类、机器学习基础、深度学习原理、自然语言处理、计算机视觉等核心领域，以及AI在教育、医疗、金融等行业的应用案例。',
            title: '人工智能概要'
          },
          selectedTemplate: { id: 1, name: '科技风格模板' }
        })
        used2026Titles.add('人工智能概要')
      } else {
        month = Math.floor(Math.random() * 12) + 1
        day = Math.floor(Math.random() * 28) + 1
        date = new Date(year, month - 1, day)
        
        if (year === '2026') {
          // 2026年确保标题不重复
          do {
            titleIndex = Math.floor(Math.random() * courseTitles.length)
          } while (used2026Titles.has(courseTitles[titleIndex]))
          used2026Titles.add(courseTitles[titleIndex])
          subjectIndex = Math.floor(Math.random() * 3) // 只选前三个科目
        } else {
          titleIndex = Math.floor(Math.random() * courseTitles.length)
          subjectIndex = Math.floor(Math.random() * subjects.length)
        }
        
        hasPpt = Math.random() > 0.3
        hasDocx = Math.random() > 0.3
        
        mockHistory.push({
          id: `gen_${idCounter++}`,
          timestamp: date.getTime(),
          sessionId: 'mock_session',
          pptFilename: hasPpt ? `mock_${year}_${i + 1}.pptx` : null,
          docxFilename: hasDocx ? `mock_${year}_${i + 1}.docx` : null,
          pptPreviewId: hasPpt ? `pv_mock_${year}_${i + 1}` : null,
          pptPreviewPages: hasPpt ? Array.from({ length: Math.floor(Math.random() * 15) + 5 }, (_, j) => j + 1) : [],
          requirements: {
            subject: subjects[subjectIndex],
            content: descriptions[titleIndex],
            title: courseTitles[titleIndex]
          },
          selectedTemplate: { id: Math.floor(Math.random() * 9) + 1, name: `模板 ${Math.floor(Math.random() * 9) + 1}` }
        })
      }
    }
  })
  
  mockHistory.sort((a, b) => b.timestamp - a.timestamp)
  return mockHistory
}

const yearData = computed(() => {
  const years = {}
  store.generationHistory.forEach(gen => {
    const year = new Date(gen.timestamp).getFullYear().toString()
    years[year] = (years[year] || 0) + 1
  })
  
  const sortedYears = Object.keys(years).sort((a, b) => b - a)
  return sortedYears.map(year => ({
    year,
    count: years[year]
  }))
})

const allContent = computed(() => {
  return store.generationHistory.map(gen => {
    const date = new Date(gen.timestamp)
    const formattedDate = date.toISOString().split('T')[0]
    const year = date.getFullYear().toString()
    
    return {
      id: gen.id,
      title: gen.requirements?.title || gen.requirements?.subject || '未命名课件',
      date: formattedDate,
      type: 'courseware',
      typeLabel: '课件',
      year: year,
      description: gen.requirements?.content || '',
      plan: gen.docxFilename,
      pptFilename: gen.pptFilename,
      generation: gen
    }
  })
})

const selectedYear = computed(() => yearData.value[activeIndex.value]?.year)

const filteredCoursewares = computed(() => {
  if (!selectedYear.value) return []
  return allContent.value.filter(item => item.year === selectedYear.value)
})

const prevYear = () => {
  if (activeIndex.value > 0) {
    activeIndex.value--
    adjustTimelinePosition()
    selectedContent.value = null
  }
}

const nextYear = () => {
  if (activeIndex.value < yearData.value.length - 1) {
    activeIndex.value++
    adjustTimelinePosition()
    selectedContent.value = null
  }
}

const goToYear = (index) => {
  if (activeIndex.value !== index) {
    activeIndex.value = index
    adjustTimelinePosition()
    selectedContent.value = null
  }
}

const selectContent = (item) => {
  selectedContent.value = item
}

const toggleDeleteMode = () => {
  isDeleteMode.value = !isDeleteMode.value
}

const deleteCourseware = (item) => {
  const index = store.generationHistory.findIndex(g => g.id === item.id)
  if (index !== -1) {
    store.generationHistory.splice(index, 1)
    if (selectedContent.value?.id === item.id) {
      selectedContent.value = null
    }
    saveToLocalStorage()
  }
}

const saveToLocalStorage = () => {
  localStorage.setItem('generationHistory', JSON.stringify(store.generationHistory))
}

const handleResourceClick = (type, name, generation) => {
  if (type === 'plan' || type === 'courseware') {
    store.setCurrentGeneration(generation)
    router.push('/preview')
  }
}


const getScale = (index) => {
  const distance = Math.abs(index - activeIndex.value)
  const maxScale = 1.2
  const minScale = 0.85
  const scaleStep = 0.05
  
  if (distance === 0) return maxScale
  const scale = maxScale - distance * scaleStep
  return Math.max(scale, minScale)
}

const getZIndex = (index) => {
  const distance = Math.abs(index - activeIndex.value)
  return 100 - distance
}

const adjustTimelinePosition = () => {
  if (!timelineContainer.value) return
  
  const cardWidth = 120
  const gap = 24
  const containerWidth = timelineContainer.value.offsetWidth
  const cardCenter = (cardWidth + gap) * activeIndex.value + cardWidth / 2
  const newTranslateX = containerWidth / 2 - cardCenter
  
  translateX.value = newTranslateX
}

onMounted(() => {
  const forceRefresh = true
  if (forceRefresh || store.generationHistory.length === 0) {
    const mockData = generateMockData()
    store.generationHistory.splice(0, store.generationHistory.length, ...mockData)
    localStorage.setItem('generationHistory', JSON.stringify(mockData))
  }
  adjustTimelinePosition()
  window.addEventListener('resize', adjustTimelinePosition)
})
</script>

<style scoped>
.history-generation-page {
  width: 100%;
  height: calc(100vh - 110px);
  display: flex;
  align-items: flex-start;
  justify-content: center;
  position: relative;
  z-index: 1;
}

.history-container {
  width: 100%;
  height: 100%;
  background: white;
  border-radius: 4px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.12);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.history-header {
  background: #ffffff;
  padding: 16px 32px 0 32px;
  border-bottom: 1px solid #e9ecef;
}

.history-header h2 {
  color: #000000;
  font-size: 22px;
  font-weight: 700;
  margin: 0;
}

.history-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.history-top {
  height: 20%;
  min-height: 120px;
  background: #ffffff;
  display: flex;
  align-items: center;
  padding: 0 16px;
  overflow: hidden;
  position: relative;
}

.nav-btn {
  width: 40px;
  height: 40px;
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
  z-index: 10;
}

.nav-btn:hover:not(:disabled) {
  background: #bdd6cd;
  transform: scale(1.1);
}

.nav-btn:disabled {
  opacity: 0.3;
  cursor: not-allowed;
}

.nav-arrow {
  font-size: 16px;
  color: #495057;
}

.nav-btn:hover:not(:disabled) .nav-arrow {
  color: #0f5132;
}

.timeline-container {
  flex: 1;
  overflow: hidden;
  position: relative;
  margin: 0 16px;
}

.timeline-line {
  position: absolute;
  top: 50%;
  left: 0;
  right: 0;
  height: 3px;
  background: #d1e6e0;
  transform: translateY(-50%);
  z-index: 1;
}

.timeline-wrapper {
  display: flex;
  gap: 18px;
  transition: transform 0.5s cubic-bezier(0.4, 0, 0.2, 1);
  padding: 20px 0;
  position: relative;
  z-index: 2;
}

.year-card{
    flex-shrink: 0;
    width: 100px;
    height: 100px;
    background: #d1e6e0;
    border: 4px solid #bbd6cd;
    border-radius: 50px;
    padding: 12px;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 4px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
    cursor: pointer;
    transition: all 0.5s ease;
}
 


.year-card.active {
  background: #64a596;
  color: white;
  box-shadow: 0 6px 20px rgba(138, 180, 170, 0.4);
}

.year-card.active .year-number,
.year-card.active .year-count {
  color: white;
}

.year-number {
  font-size: 20px;
  font-weight: 700;
  color: #212529;
}

.year-count {
  font-size: 12px;
  color: #6c757d;
}

.history-bottom {
  flex: 1;
  display: flex;
  overflow: hidden;
  padding: 0 48px;
  background: #ffffff;
}

.left-column {
  flex: 0 0 60%;
  display: flex;
  flex-direction: column;
  border-right: 1px solid #e9ecef;
  overflow: hidden;
}

.column-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 24px 0 24px;
  flex-shrink: 0;
}

.column-header .column-title {
  padding: 0;
  margin: 0;
}

.delete-mode-btn {
  margin-top:20px;
  padding: 4px 16px;
  background: white;
  border: 2px solid #e28b94;
  border-radius: 20px;
  color: #e28b94;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
}

.delete-mode-btn:hover,
.delete-mode-btn.active {
  background: #e28b94;
  color: white;
}

.left-column .column-title {
  padding: 0 24px;
  flex-shrink: 0;
}

.content-grid-wrapper {
  flex: 1;
  overflow-y: auto;
  padding: 10px 24px 20px 24px;
}

.right-column {
  flex: 1;
  margin: 32px;
  border: 2px dashed #64a596;
  border-radius: 16px;
  overflow: hidden;
  background: #ffffff;
  position: relative;
}

.illustration-1 {
  position: absolute;
  right: 16px;
  bottom: -12px;
  width: 180px;
  height: 180px;
  object-fit: contain;
  pointer-events: none;
  z-index: 0;
}

.column-title {
  font-size: 18px;
  font-weight: 600;
  color: #212529;
  margin: 0 0 20px 0;
}

.content-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
}

.content-card {
  background: #dde8e4;
  border-radius: 12px;
  overflow: hidden;
  transition: all 0.3s ease;
  cursor: pointer;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  border: 2px solid transparent;
  position: relative;
}

.content-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
  border:2px solid #64a596
}

.content-card.selected {
  border-color: #8ab4aa;
  box-shadow: 0 4px 16px rgba(138, 180, 170, 0.3);
}

.card-delete-btn {
  position: absolute;
  top: 8px;
  right: 8px;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: #ffd3d3;
  color: #e28b94;
  border: none;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
  z-index: 10;
  padding: 0;
}

.card-delete-btn:hover {
  background: #e28b94;
  color:white;
}

.delete-icon {
  font-size: 20px;
  font-weight: bold;
  line-height: 1;
  margin-top: -2px;
}

.card-image {
  width: 100%;
  aspect-ratio: 16 / 9;
  background: #ffffff;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}

.preview-img {
  width: 50%;
  height: 50%;
  object-fit: contain;
}

.card-info {
  padding: 14px;
}

.card-title {
  font-size: 14px;
  font-weight: 400;
  color: #212529;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  line-height: 1.4;
  margin-bottom: 8px;
}

.card-meta {
  display: flex;
  align-items: center;
  gap: 8px;
}

.card-date {
  font-size: 12px;
  color: #6c757d;
  margin: 0;
}

.card-type {
  display: inline-block;
  padding: 3px 10px;
  border-radius: 10px;
  text-align: center;
  font-size: 12px;
  font-weight: 500;
  min-width: 30px;
}

.card-type.courseware {
  background: #bdd6cd;
  color: #0f5132;
}

.card-type.plan {
  background: #cff4fc;
  color: #055160;
}

.detail-panel {
  background: white;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  overflow-y: auto;
  max-height: 100%;
  position: relative;
  z-index: 1;
}

.detail-title {
  font-size: 20px;
  font-weight: 600;
  color: #212529;
  margin: 0 0 16px 0;
}

.detail-info {
  margin-bottom: 10sspx;
}

.detail-date {
  font-size: 13px;
  color: #6c757d;
  margin: 0 0 12px 0;
}

.detail-desc {
  font-size: 14px;
  color: #495057;
  line-height: 1.6;
  margin: 0;
}

.related-content {
  border-top: 1px solid #e9ecef;
  padding-top: 20px;
}

.related-title {
  font-size: 15px;
  font-weight: 600;
  color: #212529;
  margin: 0 0 12px 0;
}

.related-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.related-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px;
  background: #f8f9fa;
  border-radius: 8px;
  border: 2px solid transparent;
  cursor: pointer;
  transition: all 0.2s ease;
}

.related-item:hover {
  border-color: #64a596;
  background: #e9f5f2;
  transform: translateY(-2px);
  box-shadow: 0 2px 8px rgba(100, 165, 150, 0.15);
}

.related-type {
  padding: 4px 10px;
  border-radius: 8px;
  font-size: 11px;
  font-weight: 500;
}

.related-type.plan {
  background: #cff4fc;
  color: #055160;
}

.related-type.animation {
  background: #fff3cd;
  color: #664d03;
}

.related-name {
  font-size: 13px;
  color: #495057;
}



.empty-detail {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #6c757d;
}

.empty-icon {
  font-size: 48px;
  margin-bottom: 16px;
}

.empty-text {
  font-size: 14px;
  margin: 0;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

@media (max-width: 1400px) {
  .content-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 900px) {
  .content-grid {
    grid-template-columns: 1fr;
  }
  
  .left-column {
    flex-basis: 50%;
  }
}
</style>
