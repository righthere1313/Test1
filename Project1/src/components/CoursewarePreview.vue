<template>
  <div class="preview-page">
    <div class="preview-layout" :class="{ 'sidebar-collapsed': sidebarCollapsed }">
      <div class="left-panel">
        <div class="panel-card chat-panel-card">
          <div class="panel-header">
            <h3>智能对话</h3>
          </div>
          <div class="messages-container" ref="messagesContainer">
            <div v-if="chatHistory.length === 0" class="empty-state">
              <img class="empty-icon" src="/images/插画2.png" alt="">
              <p class="empty-text">开始对话吧</p>
            </div>
            <div
              v-for="(msg, index) in chatHistory"
              :key="index"
              :class="['message', msg.role]"
            >
              <div class="message-avatar" :class="msg.role + '-avatar'">
                <div v-if="msg.role === 'ai'" class="robot-icon"></div>
                <div v-else class="avatar-icon"></div>
              </div>
              <div class="message-content">
                <div class="message-text">
                  <span v-if="msg.role === 'user'">{{ msg.content }}</span>
                  <div v-else class="markdown-content" v-html="renderMarkdown(msg.content)"></div>
                </div>
                <div v-if="msg.role === 'ai'" class="message-actions">
                  <button class="action-btn small" @click="copyMessage(msg.content)">
                    复制
                  </button>
                  <button class="action-btn small" @click="regenerate">
                    重新生成
                  </button>
                </div>
              </div>
            </div>
            <div v-if="isAwaitingAI" class="message ai">
              <div class="message-avatar ai-avatar">
                <div class="robot-icon"></div>
              </div>
              <div class="message-content">
                <div class="message-text thinking-bubble">
                  <div class="thinking-dots">
                    <span></span>
                    <span></span>
                    <span></span>
                  </div>
                  正在思考...
                </div>
              </div>
            </div>
          </div>
          <div class="input-area">
            <div
              class="input-wrapper"
              @dragover.prevent="isDragOver = true"
              @dragleave.prevent="isDragOver = false"
              @drop.prevent="handleDrop"
              :class="{ 'drag-over': isDragOver }"
            >
              <div v-if="pendingFiles.length > 0" class="pending-files">
                <div v-for="(file, index) in pendingFiles" :key="index" class="pending-file">
                  <span class="file-name">{{ file.name }}</span>
                  <button @click="removeFile(index)" class="remove-file">×</button>
                </div>
              </div>
              <div class="toolbar">
                  <button class="toolbar-btn" @click="toggleFileInput">
                    <img src="/images/添加附件.png" alt="上传" class="toolbar-img">
                  </button>
                  <button class="toolbar-btn" @click="startVoiceInput" :class="{ recording: isRecording }">
                    <img src="/images/语音.png" alt="语音" class="toolbar-img">
                  </button>
                  <div class="toolbar-divider"></div>
                </div>
              <div class="textarea-wrapper">
                <textarea
                  ref="chatInput"
                  v-model="inputText"
                  class="chat-textarea"
                  placeholder="请输入内容..."
                  @keydown.enter="handleKeyDown"
                  rows="1"
                  @input="autoResize"
                ></textarea>
                <button @click="sendMessage" class="send-btn" :disabled="!inputText.trim() && pendingFiles.length === 0">
                  <span v-if="inputText.trim() || pendingFiles.length > 0">发送</span>
                  <span v-else>请先输入内容</span>
                </button>
              </div>
            </div>
            <input
              type="file"
              ref="fileInput"
              class="file-input"
              @change="handleFileSelect"
              multiple
              accept=".ppt,.pptx,.doc,.docx,.pdf"
            >
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
                  @click="switchTab(tab.id)"
                  :class="['tab', { active: currentTab === tab.id }]"
                >
                  {{ tab.name }}
                </button>
              </div>
            </div>
            <div class="header-right">
              <div class="download-group">
                <button @click="downloadFile('pptx')" class="download-btn">
                  <img src="/images/保存.png" alt="保存" class="download-img">
                  下载 PPT
                </button>
                <button @click="downloadFile('docx')" class="download-btn">
                  <img src="/images/保存.png" alt="保存" class="download-img">
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
                    <img v-if="slide.thumb" :src="slide.thumb" :alt="slide.title" class="thumbnail-image" />
                    <div v-else class="thumbnail-content">{{ slide.title }}</div>
                    <span class="slide-number">{{ index + 1 }}</span>
                  </div>
                </div>
              </div>
              <div class="ppt-main-card">
                <div class="ppt-main">
                  <div class="courseware-title">
                    <span class="title-label">课件名:</span>
                    <span class="title-text">{{ coursewareTitle || '未命名课件' }}</span>
                  </div>
                  <div class="slide-wrapper">
                    <div class="slide-display" :class="pptSlides[currentSlide]?.theme">
                      <img 
                        v-if="pptSlides[currentSlide]?.image" 
                        :src="pptSlides[currentSlide]?.image" 
                        :alt="pptSlides[currentSlide]?.title"
                        class="slide-image"
                      />
                      <template v-else>
                        <h1>{{ pptSlides[currentSlide]?.title }}</h1>
                        <p v-if="pptSlides[currentSlide]?.content">{{ pptSlides[currentSlide]?.content }}</p>
                      </template>
                    </div>
                  </div>
                  <div class="control-bar">
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
                  </div>
                </div>
              </div>
            </div>
          </div>
          <div v-if="currentTab === 'word'" class="word-preview">
            <div class="word-content-card full-width">
              <div class="word-content">
                <div v-if="wordHtmlContent" class="word-preview-container" v-html="wordHtmlContent"></div>
                <div v-else class="doc-sections">
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
              <div class="creative-cards-wrapper">
                <div class="creative-cards">
                  <div class="creative-card" @click="openQuizGame">
                    <div class="card-header">
                      <span class="card-type">互动问答</span>
                      <h4>快问快答</h4>
                    </div>
                    <div class="card-body">
                      <div class="placeholder">点击开始问答游戏</div>
                    </div>
                    <div class="card-desc">
                      <p>人工智能通识小测验，挑战你的AI知识</p>
                    </div>
                    <div class="card-actions">
                      <button class="card-btn primary">开始答题</button>
                    </div>
                  </div>
                  <div class="creative-card" @click="openMemoryGame">
                    <div class="card-header">
                      <span class="card-type">翻牌猜谜</span>
                      <h4>术语卡配对</h4>
                    </div>
                    <div class="card-body">
                      <div class="placeholder">点击开始翻牌游戏</div>
                    </div>
                    <div class="card-desc">
                      <p>翻牌配对AI术语和定义，记忆AI知识点</p>
                    </div>
                    <div class="card-actions">
                      <button class="card-btn primary">开始游戏</button>
                    </div>
                  </div>
                  <div class="creative-card" @click="openDigitalHuman">
                    <div class="card-header">
                      <span class="card-type">数字人演示</span>
                      <h4>数字人展示</h4>
                    </div>
                    <div class="card-body">
                      <div class="placeholder">点击观看数字人演示</div>
                    </div>
                    <div class="card-desc">
                      <p>数字人互动演示，体验AI数字人技术</p>
                    </div>
                    <div class="card-actions">
                      <button class="card-btn primary">开始演示</button>
                    </div>
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
import { ref, computed, nextTick, onMounted, watch } from 'vue'
import store from '../store'
import { chatAPI, filesAPI, generateAPI } from '../services/api'
import apiConfig from '../config/api'
import MarkdownIt from 'markdown-it'
import mammoth from 'mammoth'

const currentTab = ref(store.previewTab)
const currentSlide = ref(0)
const activeOutline = ref(0)
const sidebarCollapsed = ref(false)

const tabs = [
  { id: 'ppt', name: 'PPT 课件' },
  { id: 'word', name: 'Word 教案' },
  { id: 'creative', name: '创意内容' }
]

const switchTab = (tabId) => {
  currentTab.value = tabId
  store.setPreviewTab(tabId)
}

watch(() => store.previewTab, (newTab) => {
  currentTab.value = newTab
  if (newTab === 'ppt') {
    loadPptPreview();
  } else if (newTab === 'word') {
    loadLessonPlanPreview();
  }
})

watch(() => store.generatedFiles.docxFilename, async (newFilename) => {
  if (newFilename) {
    console.log('检测到docxFilename变化:', newFilename);
    await loadLessonPlanPreview()
  }
})

watch(() => store.generatedFiles, (newFiles) => {
  console.log('generatedFiles变化:', newFiles);
  if (newFiles.docxFilename && !wordHtmlContent.value) {
    loadLessonPlanPreview();
  }
}, { deep: true })

const chatHistory = computed(() => store.chatHistory)
const messagesContainer = ref(null)
const inputText = ref("")
const isRecording = ref(false)
const tempVoiceText = ref("")
const isDragOver = ref(false)
const fileInput = ref(null)
const pendingFiles = ref([])
const chatInput = ref(null)
const isAwaitingAI = ref(false)

const md = new MarkdownIt();

const renderMarkdown = (content) => {
  if (!content) return '';
  let processedContent = content.replace(/<br\s*\/?>/gi, '\n');
  return md.render(processedContent);
};

const scrollToBottom = () => {
  nextTick(() => {
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight;
    }
  });
};

const downloadLessonPlan = async () => {
  try {
    if (lessonPlanFilename.value) {
      await generateAPI.downloadDocx(lessonPlanFilename.value);
    }
  } catch (error) {
    console.error('下载教案失败:', error);
  }
};

const updateWordSectionsFromRequirements = () => {
  if (store.teachingRequirements) {
    const requirements = store.teachingRequirements;
    const newSections = [];
    
    // 教学目标
    newSections.push({
      title: '一、教学目标',
      content: requirements.objectives || '理解和掌握本节课的核心内容'
    });
    
    // 重点内容（知识点）
    if (requirements.knowledgePoints && requirements.knowledgePoints.length > 0) {
      newSections.push({
        title: '二、重点内容',
        content: '教学重点：' + requirements.knowledgePoints.join('、')
      });
    }
    
    // 教学难点
    if (requirements.difficulties && requirements.difficulties.length > 0) {
      newSections.push({
        title: '三、教学难点',
        content: '教学难点：' + requirements.difficulties.join('、')
      });
    }
    
    // 教学过程
    newSections.push({
      title: '四、教学过程',
      content: '通过实例引入新课，讲解重点内容，进行课堂练习和总结'
    });
    
    wordSections.value = newSections;
  }
};

onMounted(() => {
  scrollToBottom();
  if (store.generatedFiles.pptFilename) {
    loadPptPreview();
  }
  if (store.generatedFiles.docxFilename) {
    loadLessonPlanPreview();
  }
  updateWordSectionsFromRequirements();
});

const sendMessage = async () => {
  if (!inputText.value.trim() && pendingFiles.value.length === 0) return;
  if (isAwaitingAI.value) return;

  const userMsg = {
    role: "user",
    content: inputText.value,
    files: [...pendingFiles.value],
  };

  store.addMessage(userMsg);
  const queryText = inputText.value;
  inputText.value = "";
  pendingFiles.value = [];
  scrollToBottom();
  isAwaitingAI.value = true;

  try {
    const tempDocIds = [];

    for (const file of userMsg.files) {
      try {
        const result = await filesAPI.uploadStaging(file, store.sessionId);
        tempDocIds.push(result.temp_document_id);
        store.addTemporaryDocument(result.temp_document_id);
      } catch (err) {
        console.error("上传临时文件失败:", err);
      }
    }

    const aiResponse = await chatAPI.qa(queryText, {
      top_k: 5,
      temporary_document_ids: tempDocIds,
      session_id: store.sessionId,
    });

    const aiMsg = {
      role: "ai",
      content: aiResponse.answer,
      citations: aiResponse.citations,
    };
    
    // 检查AI响应中是否有结构化的教学需求摘要
    if (aiResponse.structuredSummary || (aiResponse.answer && (aiResponse.answer.includes('教学目标') || aiResponse.answer.includes('重点内容')))) {
      // 尝试从AI响应中提取结构化的教学需求
      let summary = aiResponse.structuredSummary;
      if (!summary) {
        // 如果没有structuredSummary，尝试从内容中解析
        summary = {
          objectives: '',
          knowledgePoints: [],
          difficulties: []
        };
        
        // 简单的解析逻辑，从AI回答中提取关键词
        const answer = aiResponse.answer;
        if (answer.includes('教学目标')) {
          const objectiveMatch = answer.match(/教学目标[：:]\s*([^\n]+)/);
          if (objectiveMatch) summary.objectives = objectiveMatch[1];
        }
        if (answer.includes('重点内容')) {
          const pointsMatch = answer.match(/重点内容[：:]\s*([^\n]+)/);
          if (pointsMatch) summary.knowledgePoints = pointsMatch[1].split(/[，、]/);
        }
        if (answer.includes('教学难点')) {
          const diffMatch = answer.match(/教学难点[：:]\s*([^\n]+)/);
          if (diffMatch) summary.difficulties = diffMatch[1].split(/[，、]/);
        }
      }
      
      aiMsg.structuredSummary = summary;
      store.setTeachingRequirements(summary);
      
      // 更新wordSections
      updateWordSectionsFromRequirements();
    }
    
    store.addMessage(aiMsg);
    scrollToBottom();
  } catch (error) {
    const errorMsg = {
      role: "ai",
      content: "抱歉，处理您的请求时出现了问题：" + (error.message || "未知错误"),
    };
    store.addMessage(errorMsg);
    scrollToBottom();
  } finally {
    isAwaitingAI.value = false;
  }
};

const handleKeyDown = (e) => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    sendMessage();
  }
};

const toggleFileInput = () => {
  fileInput.value.click();
};

const handleFileSelect = (e) => {
  const files = Array.from(e.target.files);
  files.forEach((file) => {
    pendingFiles.value.push({
      name: file.name,
      type: file.type,
    });
  });
  e.target.value = "";
};

const handleDrop = (e) => {
  isDragOver.value = false;
  const files = Array.from(e.dataTransfer.files);
  files.forEach((file) => {
    pendingFiles.value.push({
      name: file.name,
      type: file.type,
    });
  });
};

const removeFile = (index) => {
  pendingFiles.value.splice(index, 1);
};

const autoResize = () => {
  nextTick(() => {
    if (chatInput.value) {
      chatInput.value.style.height = "auto";
      chatInput.value.style.height = Math.min(chatInput.value.scrollHeight, 150) + "px";
    }
  });
};

const startVoiceInput = () => {
  if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
    alert('您的浏览器不支持语音识别功能，请使用Chrome浏览器');
    return;
  }

  if (!isRecording.value) {
    tempVoiceText.value = '';
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    const recognition = new SpeechRecognition();
    recognition.lang = 'zh-CN';
    recognition.continuous = true;
    recognition.interimResults = true;

    recognition.onstart = () => {
      isRecording.value = true;
    };

    recognition.onresult = (event) => {
      let transcript = '';
      for (let i = event.resultIndex; i < event.results.length; i++) {
        transcript += event.results[i][0].transcript;
      }
      tempVoiceText.value = transcript;
    };

    recognition.onend = () => {
      isRecording.value = false;
      if (tempVoiceText.value) {
        inputText.value = tempVoiceText.value;
      }
    };

    recognition.start();
  } else {
    isRecording.value = false;
  }
};

const copyMessage = (content) => {
  navigator.clipboard.writeText(content).then(() => {
    alert('已复制到剪贴板');
  });
};

const regenerate = () => {
  sendMessage();
};

const pptPreviewId = ref(null);
const lastLoadedPptFilename = ref(null);
const hasPptData = ref(false);
const coursewareTitle = ref('');
const pptSlides = ref([
  { title: '1', content: '', theme: 'theme-cover', image: null },
  { title: '2', content: '', theme: 'theme-content', image: null },
  { title: '3', content: '', theme: 'theme-content', image: null },
  { title: '4', content: '', theme: 'theme-content', image: null },
  { title: '5', content: '', theme: 'theme-summary', image: null }
]);

const loadPptPreview = async () => {
  try {
    console.log('========== 开始加载PPT预览 ==========');
    console.log('store.generatedFiles:', store.generatedFiles);
    console.log('lastLoadedPptFilename:', lastLoadedPptFilename.value);
    console.log('store.generatedFiles.pptPreviewLoaded:', store.generatedFiles.pptPreviewLoaded);
    
    if (store.generatedFiles.pptPreviewLoaded && 
        lastLoadedPptFilename.value === store.generatedFiles.pptFilename && 
        pptSlides.value.length > 0 && 
        pptSlides.value[0].image !== null) {
      console.log('✅ 已加载过相同的PPT预览，直接使用缓存');
      return;
    }
    
    if (store.generatedFiles.pptPreviewId) {
      console.log('使用已存在的PPT预览ID:', store.generatedFiles.pptPreviewId);
      pptPreviewId.value = store.generatedFiles.pptPreviewId;
      
      const pages = store.generatedFiles.pptPreviewPages || [];
      console.log('预览页数:', pages);
      if (pages.length > 0) {
        pptSlides.value = pages.map((pageNum, index) => {
          const imageUrl = apiConfig.GENERATE.PPT_PREVIEW_PAGE(pptPreviewId.value, pageNum);
          const thumbUrl = apiConfig.GENERATE.PPT_PREVIEW_THUMB(pptPreviewId.value, pageNum);
          console.log(`使用已存在的第 ${pageNum} 页图片URL:`, imageUrl);
          console.log(`使用已存在的第 ${pageNum} 页缩略图URL:`, thumbUrl);
          return {
            title: `第 ${pageNum} 页`,
            content: '',
            theme: index === 0 ? 'theme-cover' : 'theme-content',
            image: imageUrl,
            thumb: thumbUrl
          };
        });
        lastLoadedPptFilename.value = store.generatedFiles.pptFilename;
        console.log('✅ PPT幻灯片加载完成:', pptSlides.value.length, '页');
        return;
      }
    }
    
    if (!store.generatedFiles.pptFilename) {
      console.log('还没有生成的PPT文件，显示默认内容');
      return;
    }
    
    console.log('PPT文件名:', store.generatedFiles.pptFilename);
    
    if (!pptPreviewId.value) {
      console.log('创建PPT预览...');
      const previewData = await generateAPI.createPptPreview({
        filename: store.generatedFiles.pptFilename
      });
      console.log('✅ PPT预览创建成功:', previewData);
      pptPreviewId.value = previewData.preview_id || previewData.id;
    }
    
    console.log('开始轮询获取PPT预览状态...');
    let previewInfo = null;
    let pollCount = 0;
    const maxPollCount = 30;
    
    while (pollCount < maxPollCount) {
      pollCount++;
      console.log(`轮询第 ${pollCount} 次...`);
      
      previewInfo = await generateAPI.getPptPreview(pptPreviewId.value);
      console.log('当前预览状态:', previewInfo.status);
      
      if (previewInfo.status === 'done') {
        console.log('✅ PPT预览完成！');
        break;
      } else if (previewInfo.status === 'failed') {
        console.warn('⚠️ PPT预览生成失败:', previewInfo.error);
        break;
      }
      
      console.log(`等待中，当前进度: ${previewInfo.progress?.done_pages || 0}/${previewInfo.progress?.total_pages || 0}`);
      await new Promise(resolve => setTimeout(resolve, 500));
    }
    
    if (!previewInfo) {
      console.warn('⚠️ 无法获取预览信息');
      return;
    }
    
    console.log('最终预览信息:', previewInfo);
    
    if (previewInfo.filename) {
      coursewareTitle.value = previewInfo.filename;
    } else if (store.generatedFiles.pptFilename) {
      coursewareTitle.value = store.generatedFiles.pptFilename;
    }
    
    if (previewInfo.status === 'failed') {
      console.warn('⚠️ PPT预览生成失败:', previewInfo.error);
      const pageCount = previewInfo.total_pages || 11;
      const pages = Array.from({ length: pageCount }, (_, i) => i + 1);
      pptSlides.value = pages.map((pageNum, index) => ({
        title: `第 ${pageNum} 页`,
        content: previewInfo.error ? `预览生成失败: ${previewInfo.error.message}` : '',
        theme: index === 0 ? 'theme-cover' : 'theme-content',
        image: null
      }));
      
      store.setGeneratedFiles(
        store.generatedFiles.pptFilename,
        store.generatedFiles.docxFilename,
        pptPreviewId.value,
        [],
        null
      );
    } else if (previewInfo.status === 'done') {
      let pageCount = 0;
      if (previewInfo.pages) {
        pageCount = typeof previewInfo.pages === 'number' ? previewInfo.pages : previewInfo.pages.length;
      } else if (previewInfo.total_pages) {
        pageCount = previewInfo.total_pages;
      }
      
      console.log('pages_base_url:', previewInfo.pages_base_url);
      console.log('API_ORIGIN:', apiConfig.API_ORIGIN);
      
      if (pageCount > 0) {
        const pages = Array.from({ length: pageCount }, (_, i) => i + 1);
        pptSlides.value = pages.map((pageNum, index) => {
          let imageUrl;
          let thumbUrl;
          if (previewInfo.pages_base_url) {
            let baseUrl = previewInfo.pages_base_url;
            if (!baseUrl.startsWith('http')) {
              if (baseUrl.startsWith('/')) {
                baseUrl = apiConfig.API_ORIGIN + baseUrl;
              } else {
                baseUrl = apiConfig.API_ORIGIN + '/' + baseUrl;
              }
            }
            imageUrl = `${baseUrl}/${pageNum}.png`;
          } else {
            imageUrl = apiConfig.GENERATE.PPT_PREVIEW_PAGE(pptPreviewId.value, pageNum);
          }
          
          if (previewInfo.thumbs_base_url) {
            let thumbBaseUrl = previewInfo.thumbs_base_url;
            if (!thumbBaseUrl.startsWith('http')) {
              if (thumbBaseUrl.startsWith('/')) {
                thumbBaseUrl = apiConfig.API_ORIGIN + thumbBaseUrl;
              } else {
                thumbBaseUrl = apiConfig.API_ORIGIN + '/' + thumbBaseUrl;
              }
            }
            thumbUrl = `${thumbBaseUrl}/${pageNum}.png`;
          } else {
            thumbUrl = apiConfig.GENERATE.PPT_PREVIEW_THUMB(pptPreviewId.value, pageNum);
          }
          
          console.log(`第 ${pageNum} 页图片URL:`, imageUrl);
          console.log(`第 ${pageNum} 页缩略图URL:`, thumbUrl);
          return {
            title: `第 ${pageNum} 页`,
            content: '',
            theme: index === 0 ? 'theme-cover' : 'theme-content',
            image: imageUrl,
            thumb: thumbUrl
          };
        });
        console.log('✅ PPT幻灯片加载完成:', pptSlides.value.length, '页');
        
        lastLoadedPptFilename.value = store.generatedFiles.pptFilename;
        
        store.setGeneratedFiles(
          store.generatedFiles.pptFilename,
          store.generatedFiles.docxFilename,
          pptPreviewId.value,
          pages,
          null
        );
      }
    } else {
      console.warn('⚠️ PPT预览未完成，显示占位内容');
      const pageCount = previewInfo.total_pages || 11;
      const pages = Array.from({ length: pageCount }, (_, i) => i + 1);
      pptSlides.value = pages.map((pageNum, index) => ({
        title: `第 ${pageNum} 页`,
        content: '预览生成中...',
        theme: index === 0 ? 'theme-cover' : 'theme-content',
        image: null
      }));
    }
  } catch (error) {
    console.error('❌ 加载PPT预览失败:', error);
  }
};

const wordHtmlContent = ref('');

const loadLessonPlanPreview = async () => {
  try {
    console.log('========== 开始加载教案预览 ==========');
    console.log('store.generatedFiles:', store.generatedFiles);
    if (store.generatedFiles.docxFilename) {
      console.log('教案文件名:', store.generatedFiles.docxFilename);
      const url = apiConfig.GENERATE.DOWNLOAD('docx', store.generatedFiles.docxFilename);
      console.log('下载URL:', url);
      
      const response = await fetch(url);
      console.log('响应状态:', response.status);
      console.log('响应头:', response.headers);
      
      if (response.ok) {
        console.log('✅ 下载成功，开始转换为HTML');
        const arrayBuffer = await response.arrayBuffer();
        console.log('文件大小:', arrayBuffer.byteLength, 'bytes');
        
        try {
          const result = await mammoth.convertToHtml({ arrayBuffer });
          console.log('✅ HTML转换成功，内容长度:', result.value?.length || 0);
          console.log('HTML内容预览:', result.value?.substring(0, 200));
          wordHtmlContent.value = result.value;
          console.log('wordHtmlContent已设置，当前值:', wordHtmlContent.value?.substring(0, 100));
        } catch (convertError) {
          console.error('❌ mammoth转换失败:', convertError);
        }
      } else {
        console.error('❌ 下载失败，响应状态:', response.status);
        const errorText = await response.text();
        console.error('错误响应内容:', errorText);
      }
    } else {
      console.log('没有教案文件名，跳过加载');
    }
  } catch (error) {
    console.error('❌ 加载教案预览失败:', error);
    console.error('错误堆栈:', error.stack);
  }
};

const wordSections = ref([
  { title: '一、教学目标', content: '理解勾股定理的内容，掌握勾股定理的证明方法' },
  { title: '二、教学重难点', content: '教学重点：勾股定理的内容和应用' },
  { title: '三、教学过程', content: '通过生活实例引入新课' }
])

const outlineItems = computed(() => {
  return wordSections.value.map(section => section.title)
})

const isGeneratingDocx = ref(false)

const generateDocx = async () => {
  if (isGeneratingDocx.value) return
  
  isGeneratingDocx.value = true
  try {
    const requirements = store.teachingRequirements;
    const sourceText = requirements 
      ? `${requirements.subject || ''}\n${requirements.objectives || ''}\n知识点：${(requirements.knowledgePoints || []).join('、')}\n难点：${(requirements.difficulties || []).join('、')}`
      : '教学教案';

    const docxRequest = {
      topic: requirements?.subject || '教学教案',
      source_text: sourceText,
      extra_instructions: requirements?.content || null
    };

    const result = await generateAPI.generateDocxAuto(docxRequest);
    
    if (result.filename) {
      store.setGeneratedFiles(null, result.filename)
      alert('Word文档生成成功！')
      await loadLessonPlanPreview()
    }
  } catch (error) {
    alert('生成Word文档失败：' + (error.message || '未知错误'))
  } finally {
    isGeneratingDocx.value = false
  }
}

const toggleSidebar = () => {
  sidebarCollapsed.value = !sidebarCollapsed.value
}

const prevSlide = () => {
  if (currentSlide.value > 0) currentSlide.value--
}

const nextSlide = () => {
  if (currentSlide.value < pptSlides.value.length - 1) currentSlide.value++
}

const openQuizGame = () => {
  window.open('/creative-content/quiz.html', '_blank');
};

const openMemoryGame = () => {
  window.open('/creative-content/memory.html', '_blank');
};

const openDigitalHuman = () => {
  window.open('/creative-content/digital-human.html', '_blank');
};

const downloadFile = async (type) => {
  try {
    if (type === 'pptx') {
      if (store.generatedFiles.pptFilename) {
        await generateAPI.downloadPpt(store.generatedFiles.pptFilename);
      } else {
        alert('暂无生成的PPT文件');
      }
    } else if (type === 'docx') {
      if (store.generatedFiles.docxFilename) {
        await generateAPI.downloadDocx(store.generatedFiles.docxFilename);
      } else {
        alert('暂无生成的Word文件');
      }
    }
  } catch (error) {
    alert('下载失败: ' + (error.message || '未知错误'));
  }
}
</script>

<style scoped>
.preview-page {
  height: calc(100vh - 110px);
  display: flex;
  width: 100%;
}

.preview-layout {
  display: grid;
  grid-template-columns: 280px 1fr;
  width: 100%;
  gap: 8px;
  padding: 0;
  transition: grid-template-columns 0.3s ease;
  min-height: 0;
  height: 100%;
}

.preview-layout.sidebar-collapsed {
  grid-template-columns: 0px 1fr;
}

.preview-layout.sidebar-collapsed .left-panel {
  width: 0;
  overflow: hidden;
}

.preview-layout.sidebar-collapsed .panel-card,
.preview-layout.sidebar-collapsed .chat-history {
  display: none;
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
  border-radius: 4px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.12);
}

.panel-header {
  padding: 10px 20px;
  border-bottom: 1px solid #bbd6cd;
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
  background: #bdd6cd;
  color: #0f5132;
}

.main-panel {
  display: flex;
  flex-direction: column;
  overflow: hidden;
  gap: 8px;
  min-width: 0;
}

.main-header-card {
  background: white;
  border-radius: 4px;
  padding: 12px 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.12);
  flex-shrink: 0;
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
  border: 1px solid #ffffff;
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
  border-radius: 16px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
}

.tab:hover {
  color: #212529;
}

.tab.active {
  background: #312f2f;
  color: white;
}

.download-group {
  display: flex;
  gap: 10px;
}

.download-btn {
  padding: 8px 16px;
  background: #312f2f;
  color: white;
  border: none;
  border-radius: 16px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 6px;
  transition: background 0.4s ease;
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
  gap: 8px;
}

.ppt-thumbnails-card {
  background: white;
  border-radius: 4px;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.12);
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
  padding: 0;
  aspect-ratio: 16/9;
  display: flex;
  align-items: center;
  justify-content: center;
}

.thumbnail.active {
  border-color: #1a1a1a;
  background: white;
}

.thumbnail-image {
  width: 100%;
  height: 100%;
  object-fit: fill;
}

.thumbnail-content {
  font-size: 12px;
  text-align: center;
  padding: 10px;
}

.slide-number{
    position: absolute;
    bottom: 4px;
    right: 4px;
    background: #bdd6cd;
    color: black;
    font-size: 10px;
    padding: 2px 7px;
    border-radius: 12px;
}

.ppt-main-card.full-width {
  width: 100%;
}

.ppt-main-card {
  background: white;
  border-radius: 4px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.12);
  flex: 1;
}

.ppt-main {
  height: 100%;
  padding: 24px;
  display: flex;
  flex-direction: column;
  box-sizing: border-box;
}

.slide-wrapper {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 0;
}

.courseware-title {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 16px;
  padding: 8px 16px;
  background: #f8f9fa;
  border-radius: 8px;
  font-size: 14px;
  flex-shrink: 0;
}

.courseware-title .title-label {
  color: #666;
  font-weight: 500;
}

.courseware-title .title-text {
  color: #333;
  font-weight: 600;
}

.slide-display {
  width: 100%;
  max-width: 900px;
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
  overflow: hidden;
}

.word-content-card.full-width {
  width: 100%;
}

.theme-cover {
  background: #f8f9fa;
  color: #212529;
}

.theme-content, .theme-summary {
  background: #f8f9fa;
  color: #212529;
}

.slide-image {
  width: 100%;
  height: 100%;
  object-fit: contain;
  display: block;
}

.slide-display h1 {
  font-size: 36px;
  margin-bottom: 16px;
}

.control-bar {
  display: flex;
  align-items: center;
  justify-content: center;
  margin-top: 16px;
  padding-top: 0;
  border-top: none;
  flex-wrap: wrap;
  gap: 12px;
  flex-shrink: 0;
  position: relative;
  z-index: 100;
}

.slide-nav {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  position: relative;
  z-index: 101;
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

.word-container {
  display: grid;
  grid-template-columns: 240px 1fr;
  height: 100%;
  gap: 16px;
}

.word-outline-card {
  background: white;
  border-radius: 4px;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.12);
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
  background: #bdd6cd;
  color: #0f5132;
  font-weight: 500;
}

.word-preview {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.word-content-card {
  background: white;
  border-radius: 4px;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.12);
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.word-content-card.full-width {
  width: 100%;
  flex: 1;
  display: flex;
  flex-direction: column;
}

.word-content {
  height: 100%;
  padding: 32px 72px;
  overflow-y: auto;
  flex: 1;
  box-sizing: border-box;
}

.word-preview-container {
  line-height: 2;
}

.word-preview-container p {
  margin-bottom: 16px;
}

.word-preview-container h1,
.word-preview-container h2,
.word-preview-container h3,
.word-preview-container h4,
.word-preview-container h5,
.word-preview-container h6 {
  margin-top: 24px;
  margin-bottom: 12px;
}

.word-header-actions {
  margin-bottom: 24px;
  display: flex;
  justify-content: flex-end;
}

.generate-docx-btn {
  padding: 10px 24px;
  background: #312f2f;
  color: white;
  border: none;
  border-radius: 12px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.2s ease;
}

.generate-docx-btn:hover:not(:disabled) {
  background: #000000;
}

.generate-docx-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
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
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.creative-cards-wrapper {
  height: calc(100vh - 150px);
  padding: 16px;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
  background: white;
}

.creative-cards {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
  width: 100%;
  max-width: 1200px;
}

.creative-card {
  background: white;
  border: 2px solid #1a1a1a;
  overflow: hidden;
  cursor: pointer;
  transition: all 0.15s;
}

.creative-card:hover {
  transform: translate(-2px, -2px);
  box-shadow: 4px 4px 0 #1a1a1a;
}

.card-header {
  padding: 20px;
  border-bottom: 2px solid #1a1a1a;
  background: #bdd6cd;
}

.card-type {
  display: inline-block;
  padding: 4px 12px;
  background: white;
  color: #1a1a1a;
  border: 2px solid #1a1a1a;
  border-radius: 0;
  font-size: 12px;
  font-weight: 600;
  margin-bottom: 8px;
}

.card-header h4 {
  font-size: 18px;
  color: #1a1a1a;
  margin: 0;
  font-weight: 700;
}

.card-body {
  padding: 20px;
}

.placeholder {
  background: #f0f0f0;
  border: 2px solid #1a1a1a;
  padding: 40px 20px;
  text-align: center;
  color: #1a1a1a;
  font-weight: 600;
}

.card-desc {
  padding: 0 20px;
  color: #1a1a1a;
  font-size: 14px;
  line-height: 1.6;
  font-weight: 500;
}

.card-actions {
  padding: 16px 20px 20px;
  display: flex;
  gap: 10px;
}

.card-btn {
  flex: 1;
  padding: 10px;
  border: 2px solid #1a1a1a;
  background: white;
  border-radius: 0;
  font-size: 14px;
  color: #1a1a1a;
  cursor: pointer;
  font-weight: 600;
}

.card-btn.primary {
  background: #1a1a1a;
  color: white;
  border: 2px solid #1a1a1a;
}

.card-btn:hover {
  opacity: 0.8;
}

.download-img {
  width: 16px;
  height: 16px;
  object-fit: contain;
}

.robot-icon {
  width: 22px;
  height: 22px;
  position: relative;
  border: 2px solid white;
  border-radius: 6px;
}

.robot-icon::before {
  content: '';
  position: absolute;
  top: 5px;
  left: 3px;
  width: 3px;
  height: 3px;
  background: white;
  border-radius: 50%;
  box-shadow: 9px 0 0 white;
}

.robot-icon::after {
  content: '';
  position: absolute;
  bottom: 5px;
  left: 5px;
  width: 10px;
  height: 3px;
  background: white;
  border-radius: 2px;
}

.avatar-icon {
  width: 20px;
  height: 20px;
  position: relative;
}

.avatar-icon::before {
  content: '';
  position: absolute;
  top: 0;
  left: 50%;
  transform: translateX(-50%);
  width: 8px;
  height: 8px;
  border: 2px solid #0f5132;
  border-radius: 50%;
}

.avatar-icon::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 50%;
  transform: translateX(-50%);
  width: 14px;
  height: 8px;
  border: 2px solid #0f5132;
  border-radius: 8px 8px 0 0;
  border-bottom: none;
}

.chat-panel-card {
  display: flex;
  flex-direction: column;
}

.messages-container {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.empty-state {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.empty-icon {
  width: 150px;
  height: 150px;
}

.empty-text {
  color: #6c757d;
  font-size: 14px;
}

.message {
  display: flex;
  gap: 8px;
  align-items: flex-end;
}

.message.user {
  flex-direction: row-reverse;
}

.message-avatar {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.ai-avatar {
  background: #2d2d2d;
  color: white;
}

.user-avatar {
  background: #bdd6cd;
  color: #0f5132;
}

.message-content {
  max-width: 75%;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.message-header {
  font-size: 11px;
  color: #6c757d;
  font-weight: 500;
}

.message-text {
  padding: 5px 10px;
  border-radius: 12px;
  font-size: 12px;
  line-height: 1.5;
  word-break: break-word;
}

.message.ai .message-text {
  background: #f8f9fa;
  border: 1px solid #bbd6cd;
  color: #212529;
  border-bottom-left-radius: 4px;
}

.message.user .message-text {
  background: #bdd6cd;
  color: #0f5132;
  border-bottom-right-radius: 4px;
}

.thinking-bubble {
  display: flex;
  align-items: center;
  gap: 8px;
}

.thinking-dots {
  display: flex;
  gap: 4px;
}

.thinking-dots span {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #8ab4aa;
  animation: bounce 1.4s infinite ease-in-out both;
}

.thinking-dots span:nth-child(1) {
  animation-delay: -0.32s;
}

.thinking-dots span:nth-child(2) {
  animation-delay: -0.16s;
}

@keyframes bounce {
  0%, 80%, 100% {
    transform: scale(0);
  }
  40% {
    transform: scale(1);
  }
}

.markdown-content {
  word-break: break-word;
  overflow-x: hidden;
}

.markdown-content :deep(h1),
.markdown-content :deep(h2),
.markdown-content :deep(h3),
.markdown-content :deep(h4),
.markdown-content :deep(h5),
.markdown-content :deep(h6) {
  margin-top: 12px;
  margin-bottom: 6px;
  font-weight: 600;
}

.markdown-content :deep(h1) {
  font-size: 20px;
}

.markdown-content :deep(h2) {
  font-size: 18px;
}

.markdown-content :deep(h3) {
  font-size: 16px;
}

.markdown-content :deep(p) {
  margin: 6px 0;
}

.markdown-content :deep(ul),
.markdown-content :deep(ol) {
  margin: 6px 0;
  padding-left: 20px;
}

.markdown-content :deep(li) {
  margin: 3px 0;
}

.markdown-content :deep(code) {
  background: rgba(0, 0, 0, 0.05);
  padding: 2px 4px;
  border-radius: 4px;
  font-family: monospace;
  font-size: 12px;
}

.markdown-content :deep(pre) {
  background: #1e293b;
  color: #f8f9fa;
  padding: 10px;
  border-radius: 8px;
  overflow-x: auto;
  margin: 10px 0;
}

.markdown-content :deep(pre code) {
  background: none;
  padding: 0;
  color: inherit;
}

.markdown-content :deep(blockquote) {
  border-left: 3px solid #bdd6cd;
  padding-left: 10px;
  margin: 10px 0;
  color: #6c757d;
}

.markdown-content :deep(a) {
  color: #0f5132;
  text-decoration: underline;
}

.markdown-content :deep(table) {
  border-collapse: collapse;
  margin: 10px 0;
  width: 100%;
  max-width: 100%;
  display: block;
  overflow-x: auto;
}

.markdown-content :deep(th),
.markdown-content :deep(td) {
  border: 1px solid #e9ecef;
  padding: 6px 10px;
  text-align: left;
  font-size: 12px;
}

.markdown-content :deep(th) {
  background: #f8f9fa;
  font-weight: 600;
}

.markdown-content :deep(img) {
  max-width: 100%;
  height: auto;
  border-radius: 6px;
  margin: 6px 0;
}

.message-actions {
  display: flex;
  gap: 8px;
}

.action-btn.small {
  padding: 2px 10px;
  background: transparent;
  border: 1px solid #dee2e6;
  color: #6c757d;
  border-radius: 8px;
  font-size: 12px;
  cursor: pointer;
}

.action-btn.small:hover {
  background: #f8f9fa;
  color: #212529;
}

.input-area {
  padding: 12px;
  border-top: 1px solid #e9ecef;
  flex-shrink: 0;
}

.input-wrapper {
  border: 2px solid #dee2e6;
  border-radius: 12px;
  padding: 8px;
  background: white;
  transition: border-color 0.2s ease;
}

.input-wrapper.drag-over {
  border-color: #8ab4aa;
  background: #e8f3ed;
}

.input-wrapper:focus-within {
  border-color: #8ab4aa;
}

.textarea-wrapper {
  position: relative;
  display: flex;
  align-items: flex-end;
  min-height: 48px;
}

.chat-textarea {
  width: 100%;
  border: none;
  outline: none;
  resize: none;
  font-size: 13px;
  line-height: 1.4;
  color: #212529;
  background: transparent;
  min-height: 48px;
  max-height: 120px;
  padding-right: 90px;
  padding-top: 8px;
  padding-bottom: 8px;
}

.textarea-wrapper .send-btn {
  position: absolute;
  right: 0;
  bottom: 4px;
  padding: 4px 16px;
  white-space: nowrap;
}

.chat-textarea::placeholder {
  color: #6c757d;
}

.toolbar {
  display: flex;
  align-items: center;
  gap: 4px;
}

.toolbar-btn {
  width: 28px;
  height: 28px;
  border: none;
  background: #f8f9fa;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #495057;
  cursor: pointer;
}

.toolbar-btn:hover {
  background: #bdd6cd;
  color: #0f5132;
}

.toolbar-btn.recording {
  background: #f8d7da;
  color: #dc3545;
  animation: pulse 1s infinite;
}

@keyframes pulse {
  0%,
  100% {
    opacity: 1;
  }
  50% {
    opacity: 0.5;
  }
}

.toolbar-emoji {
  font-size: 16px;
}

.toolbar-img {
  width: 16px;
  height: 16px;
  object-fit: contain;
}

.toolbar-divider {
  width: 1px;
  height: 20px;
  background: #dee2e6;
}

.send-btn {
  padding: 4px 12px;
  background: #312f2f;
  color: white;
  border: none;
  border-radius: 12px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.2s ease;
}

.send-btn:hover:not(:disabled) {
  background: #000000;
}

.send-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.file-input {
  display: none;
}

.pending-files {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
  margin-bottom: 6px;
}

.pending-file {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px 8px;
  background: #bdd6cd;
  border-radius: 6px;
  font-size: 12px;
  color: #0f5132;
}

.remove-file {
  width: 16px;
  height: 16px;
  border: none;
  background: rgba(15, 81, 50, 0.2);
  color: #0f5132;
  border-radius: 50%;
  font-size: 12px;
  line-height: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
}

.remove-file:hover {
  background: rgba(15, 81, 50, 0.3);
}

.lesson-plan-images {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.lesson-plan-image {
  width: 100%;
  max-width: 800px;
  margin: 0 auto;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.word-preview-container {
  padding: 20px;
  min-height: 400px;
  background: white;
  overflow: auto;
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
}

.word-preview-container h1,
.word-preview-container h2,
.word-preview-container h3 {
  margin-top: 20px;
  margin-bottom: 10px;
}

.word-preview-container h1 {
  font-size: 24px;
  font-weight: 700;
  color: #1a1a1a;
}

.word-preview-container h2 {
  font-size: 20px;
  font-weight: 600;
  color: #1a1a1a;
}

.word-preview-container h3 {
  font-size: 18px;
  font-weight: 600;
  color: #1a1a1a;
}

.word-preview-container p {
  line-height: 1.6;
  margin-bottom: 10px;
  color: #1a1a1a;
}

.word-preview-container table {
  border-collapse: collapse;
  width: 100%;
  margin: 15px 0;
}

.word-preview-container td,
.word-preview-container th {
  border: 1px solid #ddd;
  padding: 8px;
}

.word-preview-container th {
  background: #f5f5f5;
}

.word-preview-container ul,
.word-preview-container ol {
  padding-left: 24px;
  margin: 10px 0;
}

.word-preview-container li {
  margin: 5px 0;
}

.word-preview-container img {
  max-width: 100%;
  height: auto;
}

.download-lesson-btn {
  padding: 8px 16px;
  background: var(--primary-color);
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.3s;
}

.download-lesson-btn:hover {
  background: #6da08e;
}
</style>
