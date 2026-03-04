<template>
  <div class="chat-page">
    <ChatSidebar />
    <div class="chat-main">
      <div class="chat-container">
        <div class="chat-messages" ref="messagesContainer">
          <div class="message ai-message">
            <div class="message-avatar ai-avatar">
              <span class="avatar-emoji">🤖</span>
            </div>
            <div class="message-content">
              <div class="message-bubble">
                您好！我是AI教学智能体。请告诉我您的教学需求，比如：课程主题、教学目标、知识点等。您也可以上传参考资料（PDF、Word、PPT、图片、视频等）。
              </div>
              <div class="quick-replies">
                <button v-for="reply in quickReplies" :key="reply" @click="sendQuickReply(reply)" class="quick-reply-btn">
                  {{ reply }}
                </button>
              </div>
            </div>
          </div>
          <div v-for="(msg, index) in messages" :key="index" :class="['message', msg.role + '-message']">
            <div class="message-avatar" :class="msg.role + '-avatar'">
              <span v-if="msg.role === 'ai'" class="avatar-emoji">🤖</span>
              <span v-else class="avatar-emoji">👤</span>
            </div>
            <div class="message-content">
              <div v-if="msg.files && msg.files.length > 0" class="file-previews">
                <div v-for="(file, fIndex) in msg.files" :key="fIndex" class="file-preview-card">
                  <div class="file-icon">
                    <span v-if="file.type.includes('pdf')" class="file-emoji">📕</span>
                    <span v-else-if="file.type.includes('word') || file.type.includes('document')" class="file-emoji">📄</span>
                    <span v-else-if="file.type.includes('ppt') || file.type.includes('presentation')" class="file-emoji">📊</span>
                    <span v-else-if="file.type.includes('image')" class="file-emoji">🖼️</span>
                    <span v-else-if="file.type.includes('video')" class="file-emoji">🎬</span>
                    <span v-else class="file-emoji">📁</span>
                  </div>
                  <div class="file-info">
                    <div class="file-name">{{ file.name }}</div>
                    <div class="file-meta">{{ file.intent }}</div>
                  </div>
                </div>
              </div>
              <div v-if="msg.content" class="message-bubble">{{ msg.content }}</div>
              <div v-if="msg.structuredSummary" class="structured-summary">
                <h4>教学需求确认</h4>
                <div v-if="msg.structuredSummary.knowledgePoints" class="summary-section">
                  <span class="summary-label">知识点清单：</span>
                  <div class="tag-list">
                    <span v-for="(point, i) in msg.structuredSummary.knowledgePoints" :key="i" class="tag">{{ point }}</span>
                  </div>
                </div>
                <div v-if="msg.structuredSummary.difficulties" class="summary-section">
                  <span class="summary-label">教学难点：</span>
                  <div class="highlight-list">
                    <span v-for="(diff, i) in msg.structuredSummary.difficulties" :key="i" class="highlight-tag">{{ diff }}</span>
                  </div>
                </div>
                <div v-if="msg.structuredSummary.objectives" class="summary-section">
                  <span class="summary-label">教学目标：</span>
                  <p>{{ msg.structuredSummary.objectives }}</p>
                </div>
                <div class="summary-actions">
                  <button @click="confirmRequirements" class="btn-primary">确认并生成课件</button>
                  <button @click="editRequirements" class="btn-secondary">修改需求</button>
                </div>
              </div>
              <div v-if="msg.questions" class="ai-questions">
                <p class="question-text">{{ msg.questions.text }}</p>
                <div class="question-options">
                  <button v-for="(option, i) in msg.questions.options" :key="i" @click="selectOption(option)" class="option-btn">
                    {{ option }}
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
      <div class="chat-input-area">
        <div class="input-card">
          <div 
            class="drop-zone" 
            :class="{ 'drag-over': isDragOver }"
            @dragover.prevent="handleDragOver"
            @dragleave="handleDragLeave"
            @drop.prevent="handleDrop"
          >
            <div class="input-toolbar">
              <button @click="triggerFileInput" class="toolbar-btn" title="上传文件">
                <span class="toolbar-emoji">📎</span>
              </button>
              <button 
                @click="toggleRecording" 
                class="toolbar-btn" 
                :class="{ 'recording': isRecording }"
                title="语音输入"
              >
                <span class="toolbar-emoji">🎤</span>
              </button>
              <div class="toolbar-divider"></div>
              <span class="upload-hint">支持 PDF, Word, PPT, 图片, 视频</span>
            </div>
            <textarea 
              v-model="inputText"
              class="chat-textarea"
              placeholder="请描述您的教学需求..."
              @keydown="handleKeydown"
              rows="3"
            ></textarea>
            <div class="input-actions">
              <div v-if="pendingFiles.length > 0" class="pending-files">
                <div v-for="(file, index) in pendingFiles" :key="index" class="pending-file">
                  <span class="pending-file-name">{{ file.name }}</span>
                  <button @click="removePendingFile(index)" class="remove-file-btn">×</button>
                </div>
              </div>
              <button @click="sendMessage" class="send-btn" :disabled="!inputText.trim() && pendingFiles.length === 0">
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
    <div v-if="showIntentModal" class="modal-overlay" @click.self="closeIntentModal">
      <div class="modal">
        <div class="modal-header">
          <h3>标注文件用途</h3>
          <button @click="closeIntentModal" class="close-btn">×</button>
        </div>
        <div class="modal-body">
          <p class="file-name-display">{{ currentFile?.name }}</p>
          <div class="intent-options">
            <button 
              v-for="intent in intentOptions" 
              :key="intent"
              @click="selectIntent(intent)"
              class="intent-option"
              :class="{ 'selected': selectedIntent === intent }"
            >
              {{ intent }}
            </button>
          </div>
          <div class="custom-intent">
            <label>或自定义说明：</label>
            <input 
              v-model="customIntent" 
              type="text" 
              placeholder="例如：提取第三章内容作为案例"
              @input="selectedIntent = customIntent"
            />
          </div>
        </div>
        <div class="modal-footer">
          <button @click="closeIntentModal" class="btn-secondary">取消</button>
          <button @click="confirmIntent" class="btn-primary" :disabled="!selectedIntent">确认</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import store from '../store'
import ChatSidebar from './ChatSidebar.vue'

const router = useRouter()
const messagesContainer = ref(null)
const inputText = ref('')
const isRecording = ref(false)
const isDragOver = ref(false)
const fileInput = ref(null)
const pendingFiles = ref([])
const showIntentModal = ref(false)
const currentFile = ref(null)
const selectedIntent = ref('')
const customIntent = ref('')

const messages = computed(() => store.chatHistory)

const quickReplies = [
  '我想设计一节数学课',
  '帮我生成语文教案',
  '我有参考资料需要上传'
]

const intentOptions = [
  '以此为参考风格',
  '提取全部内容',
  '参照此版式',
  '作为案例使用'
]

const scrollToBottom = () => {
  nextTick(() => {
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
    }
  })
}

onMounted(() => {
  scrollToBottom()
})

const sendQuickReply = (text) => {
  inputText.value = text
  sendMessage()
}

const sendMessage = () => {
  if (!inputText.value.trim() && pendingFiles.value.length === 0) return
  
  const userMsg = {
    role: 'user',
    content: inputText.value,
    files: [...pendingFiles.value]
  }
  
  store.addMessage(userMsg)
  inputText.value = ''
  pendingFiles.value = []
  scrollToBottom()
  
  setTimeout(() => {
    const aiMsg = {
      role: 'ai',
      structuredSummary: {
        knowledgePoints: ['勾股定理', '二次根式', '平方根'],
        difficulties: ['定理的证明过程', '实际应用'],
        objectives: '理解并掌握勾股定理，能够应用于实际问题解决'
      }
    }
    store.addMessage(aiMsg)
    scrollToBottom()
  }, 1500)
}

const handleKeydown = (e) => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    sendMessage()
  }
}

const triggerFileInput = () => {
  fileInput.value.click()
}

const handleFileSelect = (e) => {
  const files = Array.from(e.target.files)
  processFiles(files)
  e.target.value = ''
}

const handleDragOver = () => {
  isDragOver.value = true
}

const handleDragLeave = () => {
  isDragOver.value = false
}

const handleDrop = (e) => {
  isDragOver.value = false
  const files = Array.from(e.dataTransfer.files)
  processFiles(files)
}

const processFiles = (files) => {
  files.forEach(file => {
    currentFile.value = file
    selectedIntent.value = ''
    customIntent.value = ''
    showIntentModal.value = true
  })
}

const selectIntent = (intent) => {
  selectedIntent.value = intent
  customIntent.value = ''
}

const confirmIntent = () => {
  if (!selectedIntent.value) return
  
  pendingFiles.value.push({
    name: currentFile.value.name,
    type: currentFile.value.type,
    intent: selectedIntent.value
  })
  
  closeIntentModal()
}

const closeIntentModal = () => {
  showIntentModal.value = false
  currentFile.value = null
  selectedIntent.value = ''
  customIntent.value = ''
}

const removePendingFile = (index) => {
  pendingFiles.value.splice(index, 1)
}

const toggleRecording = () => {
  isRecording.value = !isRecording.value
  if (isRecording.value) {
    setTimeout(() => {
      isRecording.value = false
      inputText.value += '（语音输入的文字内容）'
    }, 2000)
  }
}

const selectOption = (option) => {
  store.addMessage({
    role: 'user',
    content: option
  })
  scrollToBottom()
}

const confirmRequirements = () => {
  router.push('/preview')
}

const editRequirements = () => {
  inputText.value = '我需要修改一下需求...'
}
</script>

<style scoped>
.chat-page {
  height: 100%;
  display: grid;
  grid-template-columns: 320px 1fr;
  gap: 16px;
}

.chat-main {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.chat-container {
  flex: 1;
  background: white;
  border-radius: 16px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
}

.message {
  display: flex;
  gap: 12px;
  margin-bottom: 24px;
}

.ai-message {
  flex-direction: row;
}

.user-message {
  flex-direction: row-reverse;
}

.message-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.ai-avatar {
  background: #1a1a1a;
  color: white;
}

.user-avatar {
  background: #d1e7dd;
  color: #0f5132;
}

.avatar-emoji {
  font-size: 22px;
}

.message-content {
  max-width: 70%;
}

.message-bubble {
  padding: 14px 18px;
  border-radius: 16px;
  line-height: 1.6;
  font-size: 15px;
}

.ai-message .message-bubble {
  background: #f8f9fa;
  color: #1e293b;
  border: 1px solid #e9ecef;
}

.user-message .message-bubble {
  background: #d1e7dd;
  color: #0f5132;
}

.quick-replies {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  margin-top: 12px;
}

.quick-reply-btn {
  padding: 8px 16px;
  border: 1px solid #d1e7dd;
  background: white;
  border-radius: 20px;
  font-size: 14px;
  color: #0f5132;
  cursor: pointer;
}

.quick-reply-btn:hover {
  background: #d1e7dd;
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
  font-size: 24px;
}

.file-emoji {
  font-size: 24px;
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
  background: #d1e7dd;
  padding: 20px;
  border-radius: 16px;
  margin-top: 12px;
  border: 1px solid #a3cfbb;
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
  border: 1px solid #a3cfbb;
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
  background: #ffc107;
  color: #000000;
  border-radius: 16px;
  font-size: 13px;
  font-weight: 500;
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
  border-color: #a3cfbb;
  color: #0f5132;
}

.chat-input-area {
  flex-shrink: 0;
}

.input-card {
  background: white;
  border-radius: 16px;
  padding: 16px;
}

.drop-zone {
  border: 2px dashed #dee2e6;
  border-radius: 16px;
  padding: 16px;
}

.drop-zone.drag-over {
  border-color: #a3cfbb;
  background: #d1e7dd;
}

.input-toolbar {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
}

.toolbar-btn {
  width: 40px;
  height: 40px;
  border: none;
  background: #f8f9fa;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #495057;
  cursor: pointer;
}

.toolbar-btn:hover {
  background: #d1e7dd;
  color: #0f5132;
}

.toolbar-btn.recording {
  background: #f8d7da;
  color: #dc3545;
  animation: pulse 1s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.toolbar-emoji {
  font-size: 20px;
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

.chat-textarea {
  width: 100%;
  border: none;
  outline: none;
  resize: none;
  font-size: 15px;
  line-height: 1.6;
  color: #212529;
  background: transparent;
}

.chat-textarea::placeholder {
  color: #6c757d;
}

.input-actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 12px;
}

.pending-files {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  flex: 1;
}

.pending-file {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  background: #d1e7dd;
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

.send-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 24px;
  background: #1a1a1a;
  color: white;
  border: none;
  border-radius: 12px;
  font-size: 15px;
  font-weight: 500;
  cursor: pointer;
}

.send-btn:hover:not(:disabled) {
  background: #2d2d2d;
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
  padding: 20px 24px;
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
  font-size: 20px;
  color: #6c757d;
  cursor: pointer;
}

.modal-body {
  padding: 24px;
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
  background: white;
  border-radius: 12px;
  font-size: 14px;
  color: #212529;
  cursor: pointer;
}

.intent-option:hover {
  border-color: #ced4da;
}

.intent-option.selected {
  border-color: #0f5132;
  background: #d1e7dd;
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
  border-color: #0f5132;
}

.modal-footer {
  padding: 16px 24px;
  border-top: 1px solid #e9ecef;
  display: flex;
  gap: 12px;
  justify-content: flex-end;
}

.btn-primary, .btn-secondary {
  padding: 10px 24px;
  border-radius: 12px;
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
</style>
