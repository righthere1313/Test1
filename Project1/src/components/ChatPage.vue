<template>
  <div class="chat-page">
    <ChatSidebar />
    <div class="chat-main">
      <div class="chat-container">
        <div class="chat-header">
          <button @click="startNewChat" class="new-chat-btn">
            + 开启新对话
          </button>
          <button @click="openTemplateModal" class="template-btn">
            确定PPT模板
          </button>
        </div>
        <div class="chat-messages" ref="messagesContainer">
          <div class="message ai-message">
            <div class="message-avatar ai-avatar">
              <div class="robot-icon"></div>
            </div>
            <div class="message-content">
              <div class="message-bubble">
                您好！我是AI教学智能体。请告诉我您的教学需求，比如：课程主题、教学目标、知识点等。您也可以上传参考资料（PDF、Word、PPT、图片、视频等）。
              </div>
              <div class="quick-replies">
                <button
                  v-for="reply in quickReplies"
                  :key="reply"
                  @click="sendQuickReply(reply)"
                  class="quick-reply-btn"
                >
                  {{ reply }}
                </button>
              </div>
            </div>
          </div>
          <div
            v-for="(msg, index) in messages"
            :key="index"
            :class="['message', msg.role + '-message']"
          >
            <div class="message-avatar" :class="msg.role + '-avatar'">
              <div v-if="msg.role === 'ai'" class="robot-icon"></div>
              <img v-else-if="store.user.avatar" :src="store.user.avatar" alt="头像" class="avatar-img">
            </div>
            <div class="message-content">
              <div
                v-if="msg.files && msg.files.length > 0"
                class="file-previews"
              >
                <div
                  v-for="(file, fIndex) in msg.files"
                  :key="fIndex"
                  class="file-preview-card"
                >
                  <div class="file-icon">
                    <img
                      v-if="file.type.includes('image')"
                      src="/images/图片.png"
                      :alt="file.type"
                      class="file-img"
                    />
                    <img
                      v-else
                      src="/images/文本.png"
                      :alt="file.type"
                      class="file-img"
                    />
                  </div>
                  <div class="file-info">
                    <div class="file-name">{{ file.name }}</div>
                  </div>
                </div>
              </div>
              <div v-if="msg.content && msg.content.trim()" class="message-bubble-container">
                <div class="message-bubble">
                  <span v-if="msg.role === 'user'">{{ msg.content }}</span>
                  <div v-else class="markdown-content" v-html="renderMarkdown(msg.content)"></div>
                </div>
                <div v-if="msg.hasGenerated" class="message-actions">
                  <router-link 
                    to="/preview" 
                    @click.native="store.setPreviewTab(store.generatedFiles.pptFilename ? 'ppt' : 'word')"
                    class="preview-btn"
                  >预览</router-link>
                </div>
              </div>
              <div v-if="msg.questions" class="ai-questions">
                <p class="question-text">{{ msg.questions.text }}</p>
                <div class="question-options">
                  <button
                    v-for="(option, i) in msg.questions.options"
                    :key="i"
                    @click="selectOption(option)"
                    class="option-btn"
                  >
                    {{ option }}
                  </button>
                </div>
              </div>
            </div>
          </div>
          <div v-if="isAwaitingAI" class="message ai-message">
            <div class="message-avatar ai-avatar">
              <div class="robot-icon"></div>
            </div>
            <div class="message-content">
              <div class="message-bubble thinking-bubble">
                <div class="thinking-dots">
                  <span></span>
                  <span></span>
                  <span></span>
                </div>
                正在思考
              </div>
            </div>
          </div>
        </div>
        <img src="/images/插画3.png" alt="插画" class="illustration-3">
        <div class="input-card">
          <div class="drop-zone"
            :class="{ 'drag-over': isDragOver }"
            @dragover.prevent="handleDragOver"
            @dragleave="handleDragLeave"
            @drop.prevent="handleDrop"
          >
            <div v-if="pendingFiles.length > 0" class="input-actions">
              <div class="pending-files">
                <div
                  v-for="(file, index) in pendingFiles"
                  :key="index"
                  class="pending-file"
                >
                  <span class="pending-file-name">{{ file.name }}</span>
                  <button
                    @click="removePendingFile(index)"
                    class="remove-file-btn"
                  >
                    ×
                  </button>
                </div>
              </div>
            </div>
            <div class="input-toolbar">
              <button
                @click="triggerFileInput"
                class="toolbar-btn"
                title="上传文件"
              >
                <img src="/images/添加附件.png" alt="上传文件" class="toolbar-img">
              </button>
              <button
                @click="toggleRecording"
                class="toolbar-btn"
                :class="{ recording: isRecording }"
                title="语音输入"
              >
                <img src="/images/语音.png" alt="语音输入" class="toolbar-img">
              </button>
              <div class="toolbar-divider"></div>
              <span class="upload-hint">支持 PDF, Word, PPT, 图片, 视频</span>
            </div>
            <div v-if="isRecording || tempVoiceText" class="voice-preview">
              <span class="voice-label">正在识别：</span>
              <span class="voice-text">{{ tempVoiceText }}</span>
            </div>
            <div class="textarea-wrapper">
              <textarea
                v-model="inputText"
                class="chat-textarea"
                placeholder="请描述您的教学需求..."
                @keydown="handleKeyDown"
                rows="3"
              ></textarea>
              <button
                @click="sendMessage"
                class="send-btn"
                :disabled="!inputText.trim() && pendingFiles.length === 0"
              >
                <span class="send-emoji">➤</span>
                发送
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
    <input
      type="file"
      ref="fileInput"
      multiple
      accept=".pdf,.doc,.docx,.ppt,.pptx,.jpg,.jpeg,.png,.gif,.mp4,.avi,.mov"
      @change="handleFileSelect"
      style="display: none"
    />
    <div
      v-if="showIntentModal"
      class="modal-overlay"
      @click.self="closeIntentModal"
    >
      <div class="modal">
        <div class="modal-header">
          <h3>标注文件用途</h3>
          <button @click="closeIntentModal" class="close-btn">
            <span class="close-icon">×</span>
          </button>
        </div>
        <div class="modal-body">
          <p class="file-name-display">{{ currentFile?.name }}</p>
          <div class="intent-options">
            <button
              v-for="intent in intentOptions"
              :key="intent"
              @click="selectIntent(intent)"
              class="intent-option"
              :class="{ selected: selectedIntent === intent }"
            >
              {{ intent }}
            </button>
          </div>
          <div class="custom-intent">
            <label>自定义说明：</label>
            <input
              v-model="customIntent"
              type="text"
              placeholder="例：提取第三章的内容"
              @input="selectedIntent = customIntent"
            />
          </div>
        </div>
        <div class="modal-footer">
          <button @click="closeIntentModal" class="btn-secondary">取消</button>
          <button
            @click="confirmIntent"
            class="btn-primary"
            :disabled="!selectedIntent"
          >
            确认
          </button>
        </div>
      </div>
    </div>
    <div
      v-if="showTemplateModal"
      class="modal-overlay template-modal-overlay"
      @click.self="showTemplateModal = false"
    >
      <div class="modal template-modal">
        <div class="modal-header">
          <h3>选择PPT模板</h3>
          <button @click="showTemplateModal = false" class="close-btn">
            <span class="close-icon">×</span>
          </button>
        </div>
        <div class="modal-body template-modal-body">
          <div v-if="isLoadingTemplates" class="loading-templates">
            <p>加载模板中...</p>
          </div>
          <div v-else class="template-grid">
            <div
              v-for="(template, index) in pptTemplates"
              :key="index"
              class="template-item"
              @click="selectTemplate(template)"
            >
              <div class="template-placeholder">
                <div class="template-image-area">
                  <img 
                    v-if="getTemplateCoverUrl(template)"
                    :src="getTemplateCoverUrl(template)"
                    :alt="template.name"
                    class="template-cover"
                  />
                  <span v-else class="template-icon">📄</span>
                </div>
                <span class="template-name">{{ template.name }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
    <div
      v-if="showConfirmModal"
      class="modal-overlay confirm-modal-overlay"
      @click.self="showConfirmModal = false"
    >
      <div class="modal confirm-modal">
        <div class="modal-header">
          <h3>确认选择</h3>
        </div>
        <div class="modal-body confirm-modal-body">
          <p>确定要选择「模板 {{ selectedTemplate?.id }}」吗？</p>
        </div>
        <div class="modal-footer">
          <button @click="cancelConfirm" class="btn-secondary">取消</button>
          <button @click="confirmTemplate" class="btn-primary">确定</button>
        </div>
      </div>
    </div>
    <div
      v-if="showTemplateChoiceModal"
      class="modal-overlay template-choice-modal-overlay"
      @click.self="showTemplateChoiceModal = false"
    >
      <div class="modal template-choice-modal">
        <div class="modal-header">
          <h3>PPT模板选择</h3>
          <button @click="showTemplateChoiceModal = false" class="close-btn">
            <span class="close-icon">×</span>
          </button>
        </div>
        <div class="modal-body template-choice-modal-body">
          <p>您已选择了「{{ store.selectedPptTemplate?.name || '模板' }}」</p>
          <p>是否继续使用此模板？</p>
        </div>
        <div class="modal-footer">
          <button @click="selectNewTemplate" class="btn-secondary">选择新模板</button>
          <button @click="continueWithCurrentTemplate" class="btn-primary">继续使用</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick, onMounted, onUnmounted, computed } from "vue";
import { useRouter } from "vue-router";
import store from "../store";
import ChatSidebar from "./ChatSidebar.vue";
import { chatAPI, filesAPI, templatesAPI, generateAPI } from "../services/api";
import { loadPptPreview as loadPptPreviewInBackground } from "../utils/previewHelper";
import MarkdownIt from "markdown-it";

const router = useRouter();
const messagesContainer = ref(null);
const inputText = ref("");
const isRecording = ref(false);
const tempVoiceText = ref("");
const isDragOver = ref(false);
const fileInput = ref(null);
const pendingFiles = ref([]);
const showIntentModal = ref(false);
const currentFile = ref(null);
const selectedIntent = ref("");
const customIntent = ref("");
const showTemplateModal = ref(false);
const showConfirmModal = ref(false);
const showTemplateChoiceModal = ref(false);
const selectedTemplate = ref(null);
const isAwaitingAI = ref(false);
const pendingGenerationData = ref(null);
const isTemplateJustSelected = ref(false);

const md = new MarkdownIt();

const renderMarkdown = (content) => {
  if (!content) return '';
  let processedContent = content.replace(/<br\s*\/?>/gi, '\n');
  return md.render(processedContent);
};

const messages = computed(() => store.chatHistory);

const quickReplies = [
  "我想设计一个课件",
  "帮我生成教案",
  "我有资料需要上传",
];

const intentOptions = [
  "提取内容",
  "提取思路",
  "提取风格",
  "提取排版",
];

const pptTemplates = ref([]);
const isLoadingTemplates = ref(false);
const templateCoverUrls = ref({});

const loadTemplates = async () => {
  if (pptTemplates.value.length > 0) {
    console.log('✅ 使用缓存的模板数据');
    return;
  }
  
  isLoadingTemplates.value = true;
  try {
    console.log('========== 开始加载PPT模板 ==========');
    const [layouts, covers] = await Promise.all([
      templatesAPI.getLayouts(),
      templatesAPI.getCovers().catch(err => {
        console.warn('⚠️ 获取模板封面失败:', err);
        return [];
      })
    ]);
    
    console.log('✅ 获取到的layouts:', layouts);
    console.log('✅ 获取到的covers:', covers);
    
    let layoutList = layouts;
    if (!Array.isArray(layouts)) {
      console.warn('⚠️ layouts不是数组，尝试提取数据');
      if (layouts && typeof layouts === 'object') {
        if (layouts.layouts) layoutList = layouts.layouts;
        else if (layouts.data) layoutList = layouts.data;
        else if (layouts.items) layoutList = layouts.items;
      }
    }
    
    const coverMap = {};
    if (Array.isArray(covers)) {
      covers.forEach(cover => {
        if (cover.layout) {
          coverMap[cover.layout] = cover;
        }
      });
    }
    
    if (!Array.isArray(layoutList) || layoutList.length === 0) {
      console.warn('⚠️ 没有获取到有效的模板数据，使用默认模板');
      pptTemplates.value = Array.from({ length: 9 }, (_, i) => ({
        id: i + 1,
        name: `模板 ${i + 1}`,
        originalName: `模板 ${i + 1}`,
        layout: 'general',
        cover: null
      }));
    } else {
      console.log('✅ 有效模板数量:', layoutList.length);
      pptTemplates.value = layoutList.map((layout, index) => {
        const originalName = typeof layout === 'string' ? layout : (layout.name || `模板 ${index + 1}`);
        const layoutKey = typeof layout === 'string' ? layout : (layout.layout || 'general');
        const cover = coverMap[layoutKey];
        
        return {
          id: index + 1,
          name: `模板 ${index + 1}`,
          originalName: originalName,
          layout: layoutKey,
          cover: cover
        };
      });
    }
    console.log('✅ 最终的pptTemplates:', pptTemplates.value);
  } catch (error) {
    console.error('❌ 加载模板失败:', error);
    pptTemplates.value = Array.from({ length: 9 }, (_, i) => ({
      id: i + 1,
      name: `模板 ${i + 1}`,
      originalName: `模板 ${i + 1}`,
      layout: 'general',
      cover: null
    }));
  } finally {
    isLoadingTemplates.value = false;
  }
};

const getTemplateCoverUrl = (template) => {
  if (!template?.id) return null;
  
  if (templateCoverUrls.value[template.id]) {
    return templateCoverUrls.value[template.id];
  }
  
  if (template?.cover?.svg) {
    const svgBlob = new Blob([template.cover.svg], { type: 'image/svg+xml' });
    const url = URL.createObjectURL(svgBlob);
    templateCoverUrls.value[template.id] = url;
    return url;
  }
  return null;
};

const cleanupTemplateCoverUrls = () => {
  Object.values(templateCoverUrls.value).forEach(url => {
    if (url) {
      URL.revokeObjectURL(url);
    }
  });
  templateCoverUrls.value = {};
};

const scrollToBottom = () => {
  nextTick(() => {
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight;
    }
  });
};

onMounted(() => {
  scrollToBottom();
});

onUnmounted(() => {
  cleanupTemplateCoverUrls();
});

const sendQuickReply = (text) => {
  inputText.value = text;
  sendMessage();
};

const sendMessage = async () => {
  if (!inputText.value.trim() && pendingFiles.value.length === 0) return;
  if (isAwaitingAI.value) return;

  let effectiveQueryText = inputText.value;
  let fileIntentsText = '';
  let displayText = inputText.value;
  
  if (pendingFiles.value.length > 0) {
    const intentParts = pendingFiles.value.map(fileObj => {
      if (fileObj.intent) {
        return `- ${fileObj.name}：${fileObj.intent}`;
      }
      return `- ${fileObj.name}`;
    }).filter(Boolean).join('\n');
    
    if (intentParts) {
      fileIntentsText = `\n\n【文件用途标注】\n${intentParts}`;
    }
  }

  const fullQuery = effectiveQueryText + fileIntentsText;

  const userMsg = {
    role: "user",
    content: displayText,
    files: [...pendingFiles.value],
  };

  store.addMessage(userMsg);
  const queryText = fullQuery;
  inputText.value = "";
  pendingFiles.value = [];
  scrollToBottom();
  isAwaitingAI.value = true;

  try {
    const tempDocIds = [];

    for (const fileObj of userMsg.files) {
      try {
        const result = await filesAPI.uploadStaging(fileObj.file, store.sessionId);
        tempDocIds.push(result.temp_document_id);
        store.addTemporaryDocument(result.temp_document_id);
      } catch (err) {
        console.error("上传临时文件失败:", err);
      }
    }

    const effectiveQuery = queryText || '请分析这个文件';
    console.log('发送QA请求:', { queryText, effectiveQuery, tempDocIds, sessionId: store.sessionId, selectedPptTemplate: store.selectedPptTemplate });
    
    let aiResponse;
    try {
      const qaOptions = {
        top_k: 5,
        temporary_document_ids: tempDocIds,
        session_id: store.sessionId,
      };
      
      if (store.selectedPptTemplate?.layout) {
        qaOptions.ppt_template = store.selectedPptTemplate.layout;
        console.log('传递PPT模板:', store.selectedPptTemplate.layout, '(layout)');
      }
      
      aiResponse = await chatAPI.qa(effectiveQuery, qaOptions);
    } catch (qaError) {
      console.error('QA请求失败，尝试意图识别:', qaError);
      aiResponse = { answer: qaError.message || '请求失败' };
    }
    
    console.log('QA响应:', aiResponse);

    if (aiResponse.intent === 'generate_ppt') {
      if (!store.selectedPptTemplate) {
        console.log('⚠️ 需要生成PPT但未选择模板，提示用户选择');
        
        pendingGenerationData.value = {
          aiResponse,
          userMsg,
          tempDocIds,
          queryText
        };
        
        const aiMsg = {
          role: "ai",
          content: aiResponse.answer,
          citations: aiResponse.citations,
        };
        store.addMessage(aiMsg);
        scrollToBottom();
        
        const templatePromptMsg = {
          role: "ai",
          content: '请先选择一个PPT模板，然后再继续生成课件。'
        };
        store.addMessage(templatePromptMsg);
        scrollToBottom();
        isAwaitingAI.value = false;
        
        openTemplateModal();
        return;
      } else if (!isTemplateJustSelected.value) {
        console.log('✅ 已有选中的模板:', store.selectedPptTemplate);
        
        if (aiResponse.task_result && aiResponse.task_result.status === 'success') {
          console.log('✅ 已有生成结果，直接处理');
          await processAiResponse(aiResponse, userMsg);
          return;
        }
        
        pendingGenerationData.value = {
          aiResponse,
          userMsg,
          tempDocIds,
          queryText
        };
        
        const aiMsg = {
          role: "ai",
          content: aiResponse.answer,
          citations: aiResponse.citations,
        };
        store.addMessage(aiMsg);
        scrollToBottom();
        isAwaitingAI.value = false;
        
        showTemplateChoiceModal.value = true;
        return;
      } else {
        console.log('✅ 模板刚刚选择，直接继续生成');
        isTemplateJustSelected.value = false;
      }
    }

    await processAiResponse(aiResponse, userMsg);
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

const triggerFileInput = () => {
  fileInput.value.click();
};

const handleFileSelect = (e) => {
  const files = Array.from(e.target.files);
  processFiles(files);
  e.target.value = "";
};

const handleDragOver = () => {
  isDragOver.value = true;
};

const handleDragLeave = () => {
  isDragOver.value = false;
};

const handleDrop = (e) => {
  isDragOver.value = false;
  const files = Array.from(e.dataTransfer.files);
  processFiles(files);
};

const processFiles = (files) => {
  files.forEach((file) => {
    currentFile.value = file;
    selectedIntent.value = "";
    customIntent.value = "";
    showIntentModal.value = true;
  });
};

const selectIntent = (intent) => {
  selectedIntent.value = intent;
  customIntent.value = "";
};

const confirmIntent = () => {
  if (!selectedIntent.value) return;

  pendingFiles.value.push({
    file: currentFile.value,
    name: currentFile.value.name,
    type: currentFile.value.type,
    intent: selectedIntent.value,
  });

  closeIntentModal();
};

const closeIntentModal = () => {
  showIntentModal.value = false;
  currentFile.value = null;
  selectedIntent.value = "";
  customIntent.value = "";
};

const removePendingFile = (index) => {
  pendingFiles.value.splice(index, 1);
};

let recognition = null;

const toggleRecording = () => {
  if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
    alert('您的浏览器不支持语音识别功能，请使用Chrome浏览器');
    return;
  }

  if (!isRecording.value) {
    tempVoiceText.value = '';
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    recognition = new SpeechRecognition();
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

    recognition.onerror = (event) => {
      console.error('语音识别错误:', event.error);
      isRecording.value = false;
    };

    recognition.onend = () => {
      if (tempVoiceText.value.trim()) {
        if (inputText.value.trim()) {
          inputText.value += ' ' + tempVoiceText.value;
        } else {
          inputText.value = tempVoiceText.value;
        }
      }
      isRecording.value = false;
      tempVoiceText.value = '';
    };

    recognition.start();
  } else {
    if (recognition) {
      recognition.stop();
    }
  }
};

const selectOption = (option) => {
  store.addMessage({
    role: "user",
    content: option,
  });
  scrollToBottom();
};

const goToPreview = () => {
  store.setPreviewTab('word');
  router.push("/preview");
};

const startNewChat = () => {
  store.chatHistory = [];
  inputText.value = "";
  pendingFiles.value = [];
  store.clearSelectedPptTemplate();
  scrollToBottom();
};

const openTemplateModal = async () => {
  showTemplateModal.value = true;
  if (pptTemplates.value.length === 0) {
    await loadTemplates();
  }
};

const continueWithCurrentTemplate = async () => {
  console.log('继续使用当前模板，继续生成');
  showTemplateChoiceModal.value = false;
  if (pendingGenerationData.value) {
    const data = pendingGenerationData.value;
    pendingGenerationData.value = null;
    
    console.log('重新调用QA接口，传递模板:', store.selectedPptTemplate?.layout);
    
    try {
      const qaOptions = {
        top_k: 5,
        temporary_document_ids: data.tempDocIds,
        session_id: store.sessionId,
      };
      
      if (store.selectedPptTemplate?.layout) {
        qaOptions.ppt_template = store.selectedPptTemplate.layout;
        console.log('传递PPT模板:', store.selectedPptTemplate.layout, '(layout)');
      }
      
      const aiResponse = await chatAPI.qa(data.queryText, qaOptions);
      console.log('QA响应（带模板）:', aiResponse);
      
      await processAiResponse(aiResponse, data.userMsg);
    } catch (error) {
      console.error('重新调用QA失败:', error);
      isAwaitingAI.value = false;
    }
  }
};

const selectNewTemplate = async () => {
  console.log('选择新模板');
  showTemplateChoiceModal.value = false;
  openTemplateModal();
};

const selectTemplate = (template) => {
  selectedTemplate.value = template;
  showTemplateModal.value = false;
  showConfirmModal.value = true;
};

const processAiResponse = async (aiResponse, userMsg) => {
  const aiMsg = {
    role: "ai",
    content: aiResponse.answer,
    citations: aiResponse.citations,
  };
  
  if (aiResponse.intent === 'generate_ppt' || aiResponse.intent === 'generate_word') {
    if (aiResponse.task_result && aiResponse.task_result.status === 'success') {
      console.log('========== QA已经返回了生成结果 ==========');
      console.log('task_result:', aiResponse.task_result);
      console.log('task_result完整结构:', JSON.stringify(aiResponse.task_result, null, 2));
      
      let pptFilename = null;
      let docxFilename = null;
      let pptPreviewId = null;
      let pptPreviewPages = [];
      
      if (aiResponse.task_result.filename) {
        console.log('找到单个filename字段:', aiResponse.task_result.filename);
        if (aiResponse.task_result.filename.endsWith('.pptx')) {
          pptFilename = aiResponse.task_result.filename;
          console.log('PPT文件名:', pptFilename);
        } else if (aiResponse.task_result.filename.endsWith('.docx')) {
          docxFilename = aiResponse.task_result.filename;
          console.log('Word文件名:', docxFilename);
        }
      }
      
      if (aiResponse.task_result.filenames && Array.isArray(aiResponse.task_result.filenames)) {
        console.log('找到filenames数组:', aiResponse.task_result.filenames);
        aiResponse.task_result.filenames.forEach(filename => {
          if (filename.endsWith('.pptx')) {
            pptFilename = filename;
            console.log('从filenames数组获取PPT文件名:', pptFilename);
          } else if (filename.endsWith('.docx')) {
            docxFilename = filename;
            console.log('从filenames数组获取Word文件名:', docxFilename);
          }
        });
      }
      
      if (aiResponse.task_result.pptFilename) {
        pptFilename = aiResponse.task_result.pptFilename;
        console.log('从pptFilename字段获取:', pptFilename);
      }
      
      if (aiResponse.task_result.docxFilename) {
        docxFilename = aiResponse.task_result.docxFilename;
        console.log('从docxFilename字段获取:', docxFilename);
      }
      
      console.log('最终识别结果 - pptFilename:', pptFilename, ', docxFilename:', docxFilename);
      
      store.setGeneratedFiles(pptFilename, docxFilename, null, [], null, false);
      
      const generation = store.addGeneration({
        pptFilename,
        docxFilename,
        pptPreviewId: null,
        pptPreviewPages: [],
        requirements: store.teachingRequirements,
        selectedTemplate: store.selectedPptTemplate
      });
      
      if (pptFilename) {
        console.log('========== 开始后台加载PPT预览 ==========');
        await loadPptPreviewInBackground(store, pptFilename);
      }
      
      isAwaitingAI.value = false;
      
      const completedMsg = {
        role: "ai",
        content: '已生成完成！',
        hasGenerated: true,
        generationId: generation.id
      };
      store.addMessage(completedMsg);
      scrollToBottom();
      return;
    }
  }
  
  if (aiResponse.structuredSummary || (aiResponse.answer && (aiResponse.answer.includes('教学目标') || aiResponse.answer.includes('重点内容')))) {
      let summary = aiResponse.structuredSummary;
      if (!summary) {
        summary = {
          objectives: '',
          knowledgePoints: [],
          difficulties: []
        };
        if (aiResponse.answer) {
          const answerText = aiResponse.answer;
          const objectivesMatch = answerText.match(/教学目标[：:]\s*([\s\S]*?)(?=(重点内容|难点|$))/);
          const knowledgeMatch = answerText.match(/重点内容[：:]\s*([\s\S]*?)(?=(难点|教学目标|$))/);
          const difficultiesMatch = answerText.match(/难点[：:]\s*([\s\S]*?)(?=(重点内容|教学目标|$))/);
          
          if (objectivesMatch) summary.objectives = objectivesMatch[1].trim();
          if (knowledgeMatch) summary.knowledgePoints = knowledgeMatch[1].split(/[、，,]/).map(s => s.trim()).filter(Boolean);
          if (difficultiesMatch) summary.difficulties = difficultiesMatch[1].split(/[、，,]/).map(s => s.trim()).filter(Boolean);
        }
      }
      
      aiMsg.structuredSummary = summary;
      store.setTeachingRequirements(summary);
    }
    
    store.addMessage(aiMsg);
    scrollToBottom();
};

const confirmTemplate = () => {
  console.log('确认选择模板:', selectedTemplate.value);
  const templateToSave = {
    ...selectedTemplate.value
  };
  store.setSelectedPptTemplate(templateToSave);
  showConfirmModal.value = false;
  selectedTemplate.value = null;
  isTemplateJustSelected.value = true;
  
  if (pendingGenerationData.value) {
    console.log('继续之前的生成流程，重新调用QA传递模板:', pendingGenerationData.value);
    const data = pendingGenerationData.value;
    pendingGenerationData.value = null;
    
    console.log('重新调用QA接口，传递模板:', store.selectedPptTemplate?.layout);
    
    (async () => {
      try {
        const qaOptions = {
          top_k: 5,
          temporary_document_ids: data.tempDocIds,
          session_id: store.sessionId,
        };
        
        if (store.selectedPptTemplate?.layout) {
          qaOptions.ppt_template = store.selectedPptTemplate.layout;
          console.log('传递PPT模板:', store.selectedPptTemplate.layout, '(layout)');
        }
        
        const aiResponse = await chatAPI.qa(data.queryText, qaOptions);
        console.log('QA响应（带模板）:', aiResponse);
        
        await processAiResponse(aiResponse, data.userMsg);
      } catch (error) {
        console.error('重新调用QA失败:', error);
        isAwaitingAI.value = false;
      }
    })();
  }
};

const cancelConfirm = () => {
  showConfirmModal.value = false;
  selectedTemplate.value = null;
};
</script>

<style scoped>
.chat-page {
  height: calc(100vh - 110px);
  display: grid;
  grid-template-columns: 280px 1fr;
  gap: 8px;
}

.chat-main {
  display: flex;
  flex-direction: column;
  gap: 8px;
  height: 100%;
  min-height: 0;
}

.chat-container {
  background: white;
  border-radius: 4px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  flex: 1;
  min-height: 0;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.12);
  position: relative;
}

.illustration-3 {
  position: absolute;
  bottom: 134px;
  right: 24px;
  width: 200px;
  height: 200px;
  object-fit: contain;
  pointer-events: none;
  z-index: 0;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
  min-height: 0;
  height: 0;
  position: relative;
  z-index: 1;
}

.message {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
}

.ai-message {
  flex-direction: row;
}

.user-message {
  flex-direction: row-reverse;
}

.message-avatar {
  width: 34px;
  height: 34px;
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

.avatar-emoji {
  font-size: 22px;
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

.avatar-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  border-radius: 50%;
}

.message-content {
  max-width: 80%;
}

.message-bubble {
  padding: 8px 20px;
  border-radius: 16px;
  line-height: 1.6;
  font-size: 15px;
}

.ai-message .message-bubble {
  background: #f8f9fa;
  color: #1e293b;
  border: 1px solid #bbd6cd;
}

.user-message .message-bubble {
  background: #bdd6cd;
  color: #0f5132;
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
  margin-top: 16px;
  margin-bottom: 8px;
  font-weight: 600;
}

.markdown-content :deep(h1) {
  font-size: 24px;
}

.markdown-content :deep(h2) {
  font-size: 20px;
}

.markdown-content :deep(h3) {
  font-size: 18px;
}

.markdown-content :deep(p) {
  margin: 8px 0;
}

.markdown-content :deep(ul),
.markdown-content :deep(ol) {
  margin: 8px 0;
  padding-left: 24px;
}

.markdown-content :deep(li) {
  margin: 4px 0;
}

.markdown-content :deep(code) {
  background: rgba(0, 0, 0, 0.05);
  padding: 2px 6px;
  border-radius: 4px;
  font-family: monospace;
  font-size: 14px;
}

.markdown-content :deep(pre) {
  background: #1e293b;
  color: #f8f9fa;
  padding: 12px;
  border-radius: 8px;
  overflow-x: auto;
  margin: 12px 0;
}

.markdown-content :deep(pre code) {
  background: none;
  padding: 0;
  color: inherit;
}

.markdown-content :deep(blockquote) {
  border-left: 4px solid #bdd6cd;
  padding-left: 12px;
  margin: 12px 0;
  color: #6c757d;
}

.markdown-content :deep(a) {
  color: #0f5132;
  text-decoration: underline;
}

.markdown-content :deep(table) {
  border-collapse: collapse;
  margin: 12px 0;
  width: 100%;
  max-width: 100%;
  display: block;
  overflow-x: auto;
}

.markdown-content :deep(th),
.markdown-content :deep(td) {
  border: 1px solid #e9ecef;
  padding: 8px 12px;
  text-align: left;
}

.markdown-content :deep(th) {
  background: #f8f9fa;
  font-weight: 600;
}

.markdown-content :deep(img) {
  max-width: 100%;
  height: auto;
  border-radius: 8px;
  margin: 8px 0;
}

.quick-replies {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  margin-top: 6px;
}

.quick-reply-btn {
  padding: 4px 12px;
  border: 1px solid #ffffff;
  background: #d8e9e4;
  border-radius: 12px;
  font-size: 13px;
  color: #0f5132;
  cursor: pointer;
}

.file-previews {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 8px;
}

.file-preview-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: #f8f9fa;
  border-radius: 12px;
  border: 1px solid #e9ecef;
}

.file-icon {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.file-img {
  width: 24px;
  height: 24px;
  object-fit: contain;
}

.file-name {
  font-weight: 500;
  font-size: 14px;
  color: #1e293b;
}

.file-meta {
  font-size: 12px;
  color: #6c757d;
}

.structured-summary {
  background: #bdd6cd;
  padding: 20px;
  border-radius: 16px;
  margin-top: 12px;
  border: 1px solid #93bfab;
}

.structured-summary h4 {
  margin-bottom: 16px;
  color: #0f5132;
  font-size: 16px;
}

.summary-section {
  margin-bottom: 12px;
}

.summary-label {
  font-weight: 600;
  color: #0f5132;
  font-size: 14px;
}

.tag-list {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  margin-top: 8px;
}

.tag {
  padding: 6px 14px;
  background: white;
  border: 1px solid #93bfab;
  color: #0f5132;
  border-radius: 16px;
  font-size: 13px;
}

.highlight-list {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  margin-top: 8px;
}

.highlight-tag {
  padding: 6px 14px;
  background: #ffd967;
  border: 1px solid #d6ae35;
  color: #000000;
  border-radius: 16px;
  font-size: 13px;
}

.message-actions {
  display: flex;
  gap: 8px;
  margin-top: auto;
  margin-bottom: 4px;
  flex-wrap: wrap;
  align-self: flex-end;
}

.message-bubble-container {
  display: flex;
  align-items: stretch;
  gap: 8px;
  min-height: 44px;
}

.preview-btn,
.update-btn {
  padding: 4px 12px;
  border: 1px solid #ffffff;
  background: #d8e9e4;
  color: #0f5132;
  border-radius: 12px;
  font-size: 13px;
  cursor: pointer;
  text-decoration: none;
  flex-shrink: 0;
}

.preview-btn:hover,
.update-btn:hover {
  background: #d8e9e4;
  border-color: #ffffff;
  text-decoration: none;
}

.summary-section p {
  margin-top: 8px;
  color: #0f5132;
  font-size: 14px;
}

.summary-actions {
  display: flex;
  gap: 12px;
  margin-top: 20px;
}

.ai-questions {
  margin-top: 12px;
}

.question-text {
  margin-bottom: 12px;
  color: #495057;
}

.question-options {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.option-btn {
  padding: 10px 20px;
  background: white;
  border: 2px solid #dee2e6;
  border-radius: 10px;
  font-size: 14px;
  color: #212529;
  cursor: pointer;
}

.option-btn:hover {
  border-color: #93bfab;
  color: #0f5132;
}

.chat-input-area {
  flex-shrink: 0;
}

.input-card {
  background: white;
  border-radius: 4px;
  padding: 0px 64px 16px 64px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.12);
  position: relative;
  z-index: 2;
}

.drop-zone {
  border: 2px dashed #bbd6cd;
  border-radius: 16px;
  padding: 6px 16px 16px 16px;
}

.drop-zone.drag-over {
  border-color: #93bfab;
  background: #bdd6cd;
}

.input-toolbar {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 2px;
}

.toolbar-btn {
  width: 32px;
  height: 32px;
  border: none;
  background: #f8f9fa;
  border-radius: 8px;
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
  font-size: 20px;
}

.toolbar-img {
  width: 18px;
  height: 18px;
  object-fit: contain;
}

.toolbar-divider {
  width: 1px;
  height: 24px;
  background: #dee2e6;
}

.upload-hint {
  font-size: 13px;
  color: #6c757d;
}

.voice-preview {
  background: #bdd6cd;
  border: 1px solid #8ab4aa;
  border-radius: 8px;
  padding: 4px 14px;
  margin-bottom: 16px;
  display: flex;
  align-items: flex-start;
  gap: 8px;
}

.voice-label {
  font-size: 14px;
  color: #0f5132;
  white-space: nowrap;
}

.voice-text {
  color: #0f5132;
  flex: 1;
  word-break: break-word;
}

.textarea-wrapper {
  position: relative;
  display: flex;
  align-items: flex-end;
  min-height: 45px;
}

.chat-textarea {
  width: 100%;
  border: none;
  outline: none;
  resize: none;
  font-size: 15px;
  line-height: 1.4;
  color: #212529;
  background: transparent;
  min-height: 50px;
  padding-left:10px;
  padding-right: 100px;
  padding-bottom: 8px;
}

.chat-textarea::placeholder {
  color: #6c757d;
}

.input-actions {
  display: flex;
  align-items: center;
  justify-content: flex-start;
  margin-top: 12px;
}

.pending-files {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  flex: 1;
  margin-right: 12px;
}

.pending-file {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  background: #bdd6cd;
  border-radius: 8px;
  font-size: 13px;
  color: #0f5132;
}

.remove-file-btn {
  width: 18px;
  height: 18px;
  border: none;
  background: rgba(15, 81, 50, 0.2);
  color: #0f5132;
  border-radius: 50%;
  font-size: 14px;
  line-height: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
}

.textarea-wrapper .send-btn {
  position: absolute;
  right: 0;
  bottom: 4px;
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 20px;
  background: #312f2f;
  color: white;
  border: none;
  border-radius: 16px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  white-space: nowrap;
}


.send-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.send-emoji {
  font-size: 18px;
}

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal {
  background: white;
  border-radius: 20px;
  width: 90%;
  max-width: 500px;
  max-height: 80vh;
  overflow: hidden;
}

.modal-header {
  padding: 16px 24px;
  border-bottom: 1px solid #e9ecef;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.modal-header h3 {
  font-size: 18px;
  color: #212529;
}

.close-btn {
  width: 32px;
  height: 32px;
  border: none;
  background: #f8f9fa;
  border-radius: 50%;
  color: #6c757d;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0;
}

.close-icon {
  font-size: 22px;
  font-weight: bold;
  line-height: 1;
  margin-top: -2px;
}

.modal-body {
  padding: 32px;
  padding-top: 10px;
}

.file-name-display {
  padding: 12px 16px;
  background: #f8f9fa;
  border-radius: 12px;
  margin-bottom: 20px;
  font-weight: 500;
  color: #212529;
}

.intent-options {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
  margin-bottom: 20px;
}

.intent-option {
  padding: 12px 16px;
  border: 2px solid #dee2e6;
  background: #ffffff;
  border-radius: 12px;
  font-size: 14px;
  color: #212529;
  cursor: pointer;
  transition: all 0.3s ease;
}

.intent-option:hover {
  transform: scale(1.02);
  border-color: #8ab4aa;
  background: #e8f3ed;
  color: #0f5132;
}

.intent-option.selected {
  border-color: #8ab4aa;
  background: #e8f3ed;
  color: #0f5132;
}

.custom-intent {
  margin-top: 16px;
}

.custom-intent label {
  display: block;
  font-size: 14px;
  color: #495057;
  margin-bottom: 8px;
}

.custom-intent input {
  width: 100%;
  padding: 12px 16px;
  border: 2px solid #dee2e6;
  border-radius: 12px;
  font-size: 14px;
  outline: none;
}

.custom-intent input:focus {
  border-color: #8ab4aa;
}

.modal-footer {
  padding: 16px 24px;
  border-top: 1px solid #e9ecef;
  display: flex;
  gap: 12px;
  justify-content: flex-end;
}

.btn-primary,
.btn-secondary {
  padding: 8px 24px;
  border-radius: 16px;
  font-size: 14px;
  font-weight: 500;
  border: none;
  cursor: pointer;
}

.btn-primary {
  background: #1a1a1a;
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background: #2d2d2d;
}

.btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-secondary {
  background: #f8f9fa;
  color: #495057;
}

.btn-secondary:hover {
  background: #e9ecef;
}

.chat-header {
  padding: 12px 16px;
  /* border-bottom: 1px solid #bbd6bb; */
  display: flex;
  align-items: center;
  gap: 12px;
}

.new-chat-btn {
  padding: 4px 12px;
  background: #bdd6cd;
  color: #0f5132;
  border: none;
  border-radius: 16px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.2s ease;
}



.template-btn{
  margin-left: 6px;
  padding: 4px 12px;
  border: rgba(0, 0, 0, 0);
  background: #bdd6cd;
  color: #0f5132;
  border-radius: 16px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
}

.template-modal-overlay {
  z-index: 1001;
}

.template-modal {
  width: 90%;
  max-width: 700px;
  max-height: 80vh;
}

.template-modal-body {
  max-height: 500px;
  overflow-y: auto;
}

.template-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
}

.template-item {
  cursor: pointer;
  transition: transform 0.2s ease;
}

.template-item:hover {
  transform: scale(1.05);
}

.template-placeholder {
  width: 100%;
  aspect-ratio: 4/3;
  background: #f8f9fa;
  border: 2px solid #dee2e6;
  border-radius: 12px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  transition: all 0.3s ease;
  padding: 8px;
}

.template-item:hover .template-placeholder {
  border-color: #8ab4aa;
  background: #e8f3ed;
}

.template-image-area {
  width: 100%;
  flex: 1;
  background: #e9ecef;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}

.template-cover {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.loading-templates {
  text-align: center;
  padding: 40px;
  color: #6c757d;
}

.template-icon {
  font-size: 40px;
}

.template-name {
  font-size: 14px;
  color: #495057;
  font-weight: 500;
}

.confirm-modal-overlay {
  z-index: 1002;
}

.confirm-modal {
  width: 90%;
  max-width: 400px;
}

.confirm-modal-body {
  padding: 24px;
  text-align: center;
}

.confirm-modal-body p {
  font-size: 15px;
  color: #495057;
  margin: 0;
}
</style>
