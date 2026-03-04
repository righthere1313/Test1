<template>
  <div class="preview-page">
    <div class="preview-layout" :class="{ 'sidebar-collapsed': sidebarCollapsed }">
      <div class="left-panel">
        <div class="panel-card">
          <div class="panel-header">
            <h3>对话历史</h3>
          </div>
          <div class="chat-history">
            <div v-for="(msg, index) in chatHistory" :key="index" :class="['chat-item', msg.role]">
              <div class="chat-avatar">
                <span v-if="msg.role === 'ai'" class="chat-avatar-emoji">🤖</span>
                <span v-else class="chat-avatar-emoji">👤</span>
              </div>
              <div class="chat-text">{{ msg.content }}</div>
            </div>
          </div>
        </div>
      </div>
      <div class="main-panel">
        <div class="main-header-card">
          <div class="main-header">
            <div class="header-left">
              <button @click="toggleSidebar" class="sidebar-toggle-btn">
                <span v-if="sidebarCollapsed" class="sidebar-emoji">▶</span>
                <span v-else class="sidebar-emoji">◀</span>
              </button>
              <div class="tabs">
                <button 
                  v-for="tab in tabs" 
                  :key="tab.id"
                  @click="currentTab = tab.id"
                  :class="['tab', { active: currentTab === tab.id }]"
                >
                  <span class="tab-emoji">{{ tab.icon }}</span>
                  {{ tab.name }}
                </button>
              </div>
            </div>
            <div class="header-right">
              <div class="download-group">
                <button @click="downloadFile('pptx')" class="download-btn">
                  <span class="download-emoji">📥</span>
                  下载 PPT
                </button>
                <button @click="downloadFile('docx')" class="download-btn secondary">
                  <span class="download-emoji">📥</span>
                  下载教案
                </button>
              </div>
            </div>
          </div>
        </div>
        <div class="preview-content">
          <div v-if="currentTab === 'ppt'" class="ppt-preview">
            <div class="ppt-container">
              <div class="ppt-thumbnails-card">
                <div class="ppt-thumbnails">
                  <div 
                    v-for="(slide, index) in pptSlides" 
                    :key="index"
                    @click="currentSlide = index"
                    :class="['thumbnail', { active: currentSlide === index }]"
                  >
                    <div class="thumbnail-content">{{ slide.title }}</div>
                    <span class="slide-number">{{ index + 1 }}</span>
                  </div>
                </div>
              </div>
              <div class="ppt-main-card">
                <div class="ppt-main">
                  <div class="slide-wrapper">
                    <div class="slide-display" :class="pptSlides[currentSlide]?.theme">
                      <div v-if="isEditing" class="edit-overlay">
                        <textarea 
                          v-model="editingTitle" 
                          class="edit-title"
                          placeholder="输入标题..."
                        ></textarea>
                        <textarea 
                          v-model="editingContent" 
                          class="edit-content"
                          placeholder="输入内容..."
                        ></textarea>
                      </div>
                      <template v-else>
                        <h1>{{ pptSlides[currentSlide]?.title }}</h1>
                        <p v-if="pptSlides[currentSlide]?.content">{{ pptSlides[currentSlide]?.content }}</p>
                      </template>
                    </div>
                  </div>
                  <div class="control-bar">
                    <div class="mode-switch">
                      <button 
                        @click="isEditing = false" 
                        :class="['mode-btn', { active: !isEditing }]"
                      >
                        只读
                      </button>
                      <button 
                        @click="startEditing" 
                        :class="['mode-btn', { active: isEditing }]"
                      >
                        编辑
                      </button>
                    </div>
                    <div class="slide-nav">
                      <button @click="prevSlide" class="nav-btn" :disabled="currentSlide === 0">
                        <span class="nav-emoji">◀</span>
                        上一页
                      </button>
                      <span class="slide-indicator">{{ currentSlide + 1 }} / {{ pptSlides.length }}</span>
                      <button @click="nextSlide" class="nav-btn" :disabled="currentSlide === pptSlides.length - 1">
                        下一页
                        <span class="nav-emoji">▶</span>
                      </button>
                    </div>
                    <div class="edit-actions" v-if="isEditing">
                      <button @click="cancelEditing" class="action-btn cancel">取消</button>
                      <button @click="saveEditing" class="action-btn save">保存</button>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
          <div v-if="currentTab === 'word'" class="word-preview">
            <div class="word-container">
              <div class="word-outline-card">
                <div class="word-outline">
                  <h4><span class="outline-emoji">📋</span> 教案大纲</h4>
                  <ul>
                    <li 
                      v-for="(item, index) in outlineItems" 
                      :key="index"
                      @click="activeOutline = index"
                      :class="{ active: activeOutline === index }"
                    >
                      {{ item }}
                    </li>
                  </ul>
                </div>
              </div>
              <div class="word-content-card">
                <div class="word-content">
                  <div v-for="(section, index) in wordSections" :key="index" class="doc-section">
                    <h2>{{ section.title }}</h2>
                    <p>{{ section.content }}</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
          <div v-if="currentTab === 'creative'" class="creative-preview">
            <div class="creative-container">
              <div class="creative-header-card">
                <h3>创意内容</h3>
              </div>
              <div class="creative-grid">
                <div class="creative-card">
                  <div class="card-header">
                    <span class="card-type">动画创意</span>
                    <h4>勾股定理证明动画</h4>
                  </div>
                  <div class="card-body">
                    <div class="placeholder">动画预览区域</div>
                  </div>
                  <div class="card-desc">
                    <p>通过面积法直观展示勾股定理的证明过程</p>
                  </div>
                  <div class="card-actions">
                    <button class="card-btn primary">预览动画</button>
                    <button class="card-btn">导出 GIF</button>
                  </div>
                </div>
                <div class="creative-card">
                  <div class="card-header">
                    <span class="card-type">互动小游戏</span>
                    <h4>勾股定理闯关游戏</h4>
                  </div>
                  <div class="card-body">
                    <div class="placeholder">游戏预览区域</div>
                  </div>
                  <div class="card-desc">
                    <p>通过关卡式游戏巩固知识点</p>
                  </div>
                  <div class="card-actions">
                    <button class="card-btn primary">试玩游戏</button>
                    <button class="card-btn">导出 HTML</button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import store from '../store'

const currentTab = ref('ppt')
const currentSlide = ref(0)
const activeOutline = ref(0)
const sidebarCollapsed = ref(false)
const isEditing = ref(false)
const editingTitle = ref('')
const editingContent = ref('')

const tabs = [
  { id: 'ppt', name: 'PPT 课件', icon: '📊' },
  { id: 'word', name: 'Word 教案', icon: '📄' },
  { id: 'creative', name: '创意内容', icon: '✨' }
]

const chatHistory = computed(() => store.chatHistory)

const pptSlides = ref([
  { title: '勾股定理', content: '初中数学 · 八年级', theme: 'theme-cover' },
  { title: '目录', content: '定理介绍、证明过程、例题讲解', theme: 'theme-content' },
  { title: '定理介绍', content: 'a² + b² = c²', theme: 'theme-content' },
  { title: '证明过程', content: '面积法证明', theme: 'theme-content' },
  { title: '课堂总结', content: '掌握勾股定理公式', theme: 'theme-summary' }
])

const outlineItems = [
  '一、教学目标',
  '二、教学重难点',
  '三、教学过程',
  '四、课堂练习',
  '五、课后作业'
]

const wordSections = [
  { title: '一、教学目标', content: '理解勾股定理的内容，掌握勾股定理的证明方法' },
  { title: '二、教学重难点', content: '教学重点：勾股定理的内容和应用' },
  { title: '三、教学过程', content: '通过生活实例引入新课' }
]

const toggleSidebar = () => {
  sidebarCollapsed.value = !sidebarCollapsed.value
}

const prevSlide = () => {
  if (currentSlide.value > 0) currentSlide.value--
}

const nextSlide = () => {
  if (currentSlide.value < pptSlides.value.length - 1) currentSlide.value++
}

const startEditing = () => {
  const slide = pptSlides.value[currentSlide.value]
  editingTitle.value = slide?.title || ''
  editingContent.value = slide?.content || ''
  isEditing.value = true
}

const cancelEditing = () => {
  isEditing.value = false
  editingTitle.value = ''
  editingContent.value = ''
}

const saveEditing = () => {
  if (currentSlide.value >= 0 && currentSlide.value < pptSlides.value.length) {
    pptSlides.value[currentSlide.value].title = editingTitle.value
    pptSlides.value[currentSlide.value].content = editingContent.value
  }
  isEditing.value = false
}

const downloadFile = (type) => {
  const filename = type === 'pptx' ? '勾股定理课件.pptx' : '勾股定理教案.docx'
  alert('正在下载: ' + filename)
}
</script>

<style scoped>
.preview-page {
  height: 100%;
  display: flex;
  overflow: hidden;
  width: 100%;
}

.preview-layout {
  display: grid;
  grid-template-columns: 320px 1fr;
  height: 100%;
  width: 100%;
  gap: 16px;
  padding: 0;
  transition: grid-template-columns 0.3s ease;
}

.preview-layout.sidebar-collapsed {
  grid-template-columns: 0 1fr;
  gap: 0;
  width: 100%;
}

.left-panel {
  display: flex;
  flex-direction: column;
  overflow: hidden;
  transition: all 0.3s ease;
  min-width: 0;
}

.panel-card {
  flex: 1;
  background: white;
  border-radius: 16px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.panel-header {
  padding: 16px 20px;
  border-bottom: 1px solid #f8f9fa;
}

.panel-header h3 {
  font-size: 15px;
  color: #212529;
}

.chat-history {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
}

.chat-item {
  display: flex;
  gap: 10px;
  margin-bottom: 16px;
}

.chat-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
}

.chat-text {
  padding: 10px 14px;
  border-radius: 16px;
  font-size: 13px;
  line-height: 1.5;
}

.chat-item.ai .chat-text {
  background: #f8f9fa;
  color: #212529;
}

.chat-item.user .chat-text {
  background: #d1e7dd;
  color: #0f5132;
}

.main-panel {
  display: flex;
  flex-direction: column;
  overflow: hidden;
  gap: 16px;
  min-width: 0;
}

.main-header-card {
  background: white;
  border-radius: 16px;
  padding: 12px 20px;
}

.main-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.sidebar-toggle-btn {
  width: 36px;
  height: 36px;
  border: 1px solid #dee2e6;
  background: white;
  border-radius: 10px;
  font-size: 14px;
  cursor: pointer;
}

.sidebar-toggle-btn:hover {
  background: #f8f9fa;
}

.tabs {
  display: flex;
  gap: 4px;
  background: #f8f9fa;
  padding: 4px;
  border-radius: 14px;
}

.tab {
  padding: 8px 16px;
  border: none;
  background: transparent;
  color: #6c757d;
  border-radius: 10px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
}

.tab:hover {
  color: #212529;
}

.tab.active {
  background: #1a1a1a;
  color: white;
}

.download-group {
  display: flex;
  gap: 10px;
}

.download-btn {
  padding: 8px 16px;
  background: #1a1a1a;
  color: white;
  border: none;
  border-radius: 10px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
}

.download-btn.secondary {
  background: white;
  color: #212529;
  border: 1px solid #dee2e6;
}

.preview-content {
  flex: 1;
  overflow: hidden;
}

.ppt-preview, .word-preview, .creative-preview {
  height: 100%;
  overflow: hidden;
}

.ppt-container {
  display: grid;
  grid-template-columns: 160px 1fr;
  height: 100%;
  gap: 16px;
}

.ppt-thumbnails-card {
  background: white;
  border-radius: 16px;
  overflow: hidden;
}

.ppt-thumbnails {
  height: 100%;
  padding: 16px;
  overflow-y: auto;
}

.thumbnail {
  margin-bottom: 12px;
  cursor: pointer;
  border-radius: 12px;
  overflow: hidden;
  border: 2px solid transparent;
  position: relative;
  background: #f8f9fa;
  padding: 10px;
}

.thumbnail.active {
  border-color: #1a1a1a;
  background: white;
}

.thumbnail-content {
  font-size: 12px;
  text-align: center;
}

.slide-number {
  position: absolute;
  bottom: 4px;
  right: 4px;
  background: #1a1a1a;
  color: white;
  font-size: 12px;
  padding: 2px 6px;
  border-radius: 6px;
}

.ppt-main-card {
  background: white;
  border-radius: 16px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.ppt-main {
  height: 100%;
  padding: 24px;
  display: flex;
  flex-direction: column;
}

.slide-wrapper {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}

.slide-display {
  width: 100%;
  max-width: 600px;
  aspect-ratio: 16/9;
  border-radius: 20px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  padding: 40px;
  position: relative;
}

.edit-overlay {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.edit-title, .edit-content {
  width: 100%;
  border: 2px dashed #000000;
  border-radius: 12px;
  padding: 12px;
  font-family: inherit;
  resize: none;
  background: rgba(255, 255, 255, 0.9);
}

.edit-title {
  font-size: 24px;
  font-weight: bold;
  min-height: 60px;
}

.edit-content {
  flex: 1;
  font-size: 16px;
}

.theme-cover {
  background: #000000;
  color: white;
}

.theme-content, .theme-summary {
  background: #f8f9fa;
  color: #212529;
}

.slide-display h1 {
  font-size: 36px;
  margin-bottom: 16px;
}

.control-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid #e9ecef;
  flex-wrap: wrap;
  gap: 12px;
}

.mode-switch {
  display: flex;
  gap: 4px;
  background: #f8f9fa;
  padding: 4px;
  border-radius: 12px;
}

.mode-btn {
  padding: 8px 16px;
  border: none;
  background: transparent;
  color: #6c757d;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
}

.mode-btn:hover {
  color: #212529;
}

.mode-btn.active {
  background: #1a1a1a;
  color: white;
}

.slide-nav {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
}

.nav-btn {
  padding: 8px 16px;
  border: 1px solid #dee2e6;
  background: white;
  border-radius: 10px;
  font-size: 14px;
  cursor: pointer;
}

.nav-btn:disabled {
  opacity: 0.3;
  cursor: not-allowed;
}

.nav-btn:not(:disabled):hover {
  background: #f8f9fa;
}

.slide-indicator {
  font-size: 14px;
  color: #6c757d;
}

.edit-actions {
  display: flex;
  gap: 8px;
}

.action-btn {
  padding: 8px 16px;
  border: none;
  border-radius: 10px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
}

.action-btn.cancel {
  background: #f8f9fa;
  color: #495057;
}

.action-btn.save {
  background: #1a1a1a;
  color: white;
}

.word-container {
  display: grid;
  grid-template-columns: 240px 1fr;
  height: 100%;
  gap: 16px;
}

.word-outline-card {
  background: white;
  border-radius: 16px;
  overflow: hidden;
}

.word-outline {
  height: 100%;
  padding: 20px;
  overflow-y: auto;
}

.word-outline h4 {
  font-size: 14px;
  color: #212529;
  margin-bottom: 16px;
}

.word-outline ul {
  list-style: none;
  padding: 0;
}

.word-outline li {
  padding: 10px 14px;
  margin-bottom: 4px;
  border-radius: 10px;
  color: #495057;
  font-size: 14px;
  cursor: pointer;
}

.word-outline li:hover {
  background: #f8f9fa;
}

.word-outline li.active {
  background: #d1e7dd;
  color: #0f5132;
  font-weight: 500;
}

.word-content-card {
  background: white;
  border-radius: 16px;
  overflow: hidden;
}

.word-content {
  height: 100%;
  padding: 24px 40px;
  overflow-y: auto;
}

.doc-section {
  margin-bottom: 32px;
}

.doc-section h2 {
  font-size: 22px;
  color: #212529;
  margin-bottom: 16px;
  padding-bottom: 8px;
  border-bottom: 2px solid #e9ecef;
}

.doc-section p {
  color: #495057;
  line-height: 1.8;
}

.creative-container {
  height: 100%;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.creative-header-card {
  background: white;
  border-radius: 16px;
  padding: 20px 24px;
}

.creative-container h3 {
  font-size: 20px;
  color: #212529;
  margin: 0;
}

.creative-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 16px;
}

.creative-card {
  background: white;
  border-radius: 16px;
  overflow: hidden;
}

.card-header {
  padding: 20px;
  border-bottom: 1px solid #f8f9fa;
}

.card-type {
  display: inline-block;
  padding: 4px 12px;
  background: #d1e7dd;
  color: #0f5132;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 500;
  margin-bottom: 8px;
}

.card-header h4 {
  font-size: 16px;
  color: #212529;
  margin: 0;
}

.card-body {
  padding: 20px;
}

.placeholder {
  background: #f8f9fa;
  border-radius: 12px;
  padding: 40px 20px;
  text-align: center;
  color: #6c757d;
}

.card-desc {
  padding: 0 20px;
  color: #495057;
  font-size: 14px;
  line-height: 1.6;
}

.card-actions {
  padding: 16px 20px 20px;
  display: flex;
  gap: 10px;
}

.card-btn {
  flex: 1;
  padding: 10px;
  border: 1px solid #dee2e6;
  background: white;
  border-radius: 10px;
  font-size: 14px;
  color: #495057;
  cursor: pointer;
}

.card-btn.primary {
  background: #1a1a1a;
  color: white;
  border: none;
}
</style>
