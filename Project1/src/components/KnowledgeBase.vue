<template>
  <div class="knowledge-page">
    <KnowledgeSidebar :documents="documents" />
    <div class="main-content">
      <div class="page-header">
        <div class="header-left">
          <h1>本地资料库</h1>
          <p>上传并管理教学参考资料，用于RAG检索增强</p>
        </div>
        <div class="header-right">
          <div class="search-input-wrapper">
            <input
              v-model="searchQuery"
              type="text"
              placeholder="输入查询内容..."
              class="search-input"
            />
          </div>
          <button @click="searchFullText" class="search-btn full-text">
            <img src="/images/搜索.png" alt="搜索" class="btn-img">
            全文查询
          </button>
          <button @click="triggerUpload" class="upload-btn">
            <img src="/images/导入.png" alt="上传" class="btn-img">
            上传资料
          </button>
        </div>
      </div>
      <div class="document-card">
        <div class="list-header">
          <span class="col-name">文件名</span>
          <span class="col-type">类型</span>
          <span class="col-time">上传时间</span>
          <span class="col-status">状态</span>
          <span class="col-actions">操作</span>
        </div>
        <div class="document-list">
          <div
            v-for="(doc, index) in documents"
            :key="doc.id"
            class="document-item"
          >
            <div class="col-name">
              <div class="file-icon" :class="doc.typeClass">
                <img 
                  v-if="doc.type === 'image'"
                  src="/images/图片.png" 
                  :alt="doc.type" 
                  class="file-img"
                />
                <img 
                  v-else
                  src="/images/文本.png" 
                  :alt="doc.type" 
                  class="file-img"
                />
              </div>
              <span class="file-name">{{ doc.name }}</span>
            </div>
            <div class="col-type">{{ doc.typeLabel }}</div>
            <div class="col-time">{{ doc.uploadTime }}</div>
            <div class="col-status">
              <span
                v-if="doc.status === 'processed'"
                class="status-badge success"
              >
                已完成
              </span>
              <span
                v-else-if="doc.status === 'processing'"
                class="status-badge processing"
              >
                向量化中 {{ doc.progress }}%
              </span>
              <span v-else class="status-badge error">
                处理失败
              </span>
            </div>
            <div class="col-actions">
              <button
                @click="viewDocument(doc)"
                class="action-btn view"
                title="预览"
              >
                <img src="/images/眼睛_显示.png" alt="预览" class="action-img">
              </button>
              <button
                @click="deleteDocument(doc.id)"
                class="action-btn delete"
                title="删除"
              >
                <img src="/images/删除.png" alt="删除" class="action-img">
              </button>
            </div>
          </div>
          <div v-if="documents.length === 0" class="empty-state">
            <span class="empty-emoji">📁</span>
            <h3>暂无文档</h3>
            <p>上传教学参考资料开始使用</p>
          </div>
        </div>
      </div>
    </div>
    <input
      type="file"
      ref="fileInput"
      multiple
      accept=".pdf,.doc,.docx,.ppt,.pptx,.jpg,.jpeg,.png,.gif"
      @change="handleFileUpload"
      style="display: none"
    />
    <div v-if="showPreview" class="modal-overlay" @click.self="closePreview">
      <div class="preview-modal">
        <div class="modal-header">
          <h3>{{ previewDoc?.name }}</h3>
          <button @click="closePreview" class="close-btn">×</button>
        </div>
        <div class="modal-body">
          <div class="preview-content">
            <div v-if="previewDoc?.content" class="text-preview">
              <pre>{{ previewDoc.content }}</pre>
            </div>
            <div v-else class="no-preview">
              <span class="no-preview-emoji">📄</span>
              <p>暂无预览内容</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from "vue";
import KnowledgeSidebar from "./KnowledgeSidebar.vue";

const fileInput = ref(null);
const showPreview = ref(false);
const previewDoc = ref(null);
const searchQuery = ref("");

const documents = ref([
  {
    id: 1,
    name: "初中数学-勾股定理教案.pdf",
    type: "pdf",
    typeClass: "pdf",
    typeLabel: "PDF文档",
    uploadTime: "2024-03-04 10:30",
    status: "processed",
    progress: 100,
    content:
      "勾股定理是一个基本的几何定理，指直角三角形的两条直角边的平方和等于斜边的平方。\n\n教学目标：\n1. 理解勾股定理的内容\n2. 掌握勾股定理的证明方法\n3. 能够应用勾股定理解决实际问题",
  },
  {
    id: 2,
    name: "语文-古诗词鉴赏.pptx",
    type: "ppt",
    typeClass: "ppt",
    typeLabel: "PPT演示",
    uploadTime: "2024-03-04 11:20",
    status: "processing",
    progress: 65,
    content: null,
  },
  {
    id: 3,
    name: "高中物理-力学知识点.docx",
    type: "word",
    typeClass: "word",
    typeLabel: "Word文档",
    uploadTime: "2024-03-03 15:45",
    status: "processed",
    progress: 100,
    content:
      "力学知识点总结：\n\n一、牛顿运动定律\n1. 牛顿第一定律：惯性定律\n2. 牛顿第二定律：F=ma\n3. 牛顿第三定律：作用力与反作用力",
  },
  {
    id: 4,
    name: "化学实验示意图.png",
    type: "image",
    typeClass: "image",
    typeLabel: "图片",
    uploadTime: "2024-03-03 09:15",
    status: "processed",
    progress: 100,
    content: null,
  },
  {
    id: 5,
    name: "英语语法-时态讲解.pdf",
    type: "pdf",
    typeClass: "pdf",
    typeLabel: "PDF文档",
    uploadTime: "2024-03-02 14:00",
    status: "error",
    progress: 0,
    content: null,
  },
]);

const processedCount = computed(
  () => documents.value.filter((d) => d.status === "processed").length,
);

const processingCount = computed(
  () => documents.value.filter((d) => d.status === "processing").length,
);

const triggerUpload = () => {
  fileInput.value.click();
};

const handleFileUpload = (e) => {
  const files = Array.from(e.target.files);
  files.forEach((file, index) => {
    const typeMap = {
      "application/pdf": {
        type: "pdf",
        typeClass: "pdf",
        typeLabel: "PDF文档",
      },
      "application/msword": {
        type: "word",
        typeClass: "word",
        typeLabel: "Word文档",
      },
      "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        { type: "word", typeClass: "word", typeLabel: "Word文档" },
      "application/vnd.ms-powerpoint": {
        type: "ppt",
        typeClass: "ppt",
        typeLabel: "PPT演示",
      },
      "application/vnd.openxmlformats-officedocument.presentationml.presentation":
        { type: "ppt", typeClass: "ppt", typeLabel: "PPT演示" },
      "image/jpeg": { type: "image", typeClass: "image", typeLabel: "图片" },
      "image/png": { type: "image", typeClass: "image", typeLabel: "图片" },
      "image/gif": { type: "image", typeClass: "image", typeLabel: "图片" },
    };

    const fileType = typeMap[file.type] || {
      type: "other",
      typeClass: "other",
      typeLabel: "文件",
    };

    const newDoc = {
      id: Date.now() + index,
      name: file.name,
      ...fileType,
      uploadTime: new Date()
        .toLocaleString("zh-CN", {
          year: "numeric",
          month: "2-digit",
          day: "2-digit",
          hour: "2-digit",
          minute: "2-digit",
        })
        .replace(/\//g, "-"),
      status: "processing",
      progress: 0,
      content: null,
    };

    documents.value.unshift(newDoc);

    simulateProcessing(newDoc.id);
  });
  e.target.value = "";
};

const simulateProcessing = (docId) => {
  const doc = documents.value.find((d) => d.id === docId);
  if (!doc) return;

  const interval = setInterval(() => {
    if (doc.progress < 100) {
      doc.progress += Math.floor(Math.random() * 15) + 5;
      if (doc.progress > 100) doc.progress = 100;
    } else {
      doc.status = "processed";
      clearInterval(interval);
    }
  }, 500);
};

const viewDocument = (doc) => {
  previewDoc.value = doc;
  showPreview.value = true;
};

const closePreview = () => {
  showPreview.value = false;
  previewDoc.value = null;
};

const searchFullText = () => {
  if (!searchQuery.value.trim()) {
    alert("请输入查询内容");
    return;
  }
  alert(`执行全文查询: ${searchQuery.value}`);
};

const searchSimilarity = () => {
  if (!searchQuery.value.trim()) {
    alert("请输入查询内容");
    return;
  }
  alert(`执行相似度查询: ${searchQuery.value}`);
};

const deleteDocument = (id) => {
  if (confirm("确定要删除这个文档吗？")) {
    const index = documents.value.findIndex((d) => d.id === id);
    if (index > -1) {
      documents.value.splice(index, 1);
    }
  }
};
</script>

<style scoped>
.knowledge-page {
  height: calc(100vh - 120px);
  display: grid;
  grid-template-columns: 280px 1fr;
  gap: 8px;
}

.main-content {
  display: flex;
  flex-direction: column;
  gap: 8px;
  height: 100%;
}

.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: white;
  border-radius: 4px;
  padding: 20px 24px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.12);
  flex-shrink: 0;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.search-input-wrapper {
  display: flex;
  align-items: center;
}

.search-input {
  padding: 10px 16px;
  border: 2px solid #dee2e6;
  border-radius: 12px;
  font-size: 14px;
  outline: none;
  transition: border-color 0.2s ease;
  width: 200px;
}

.search-input:focus {
  border-color: #0f5132;
}

.search-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 10px 16px;
  border: none;
  border-radius: 16px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.2s ease;
}

.search-btn.full-text {
  background: #312f2f;
  color: white;
}

.search-btn.full-text:hover {
  background: #1a1a1a;
}

.search-btn.similarity {
  background: #312f2f;
  color: white;
}

.search-btn.similarity:hover {
  background: #1a1a1a;
}

.btn-img {
  width: 16px;
  height: 16px;
  object-fit: contain;
}

.header-left h1 {
  font-size: 20px;
  color: #212529;
  margin-bottom: 4px;
}

.header-left p {
  font-size: 13px;
  color: #6c757d;
}

.upload-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 20px;
  background: #312f2f;
  color: white;
  border: none;
  border-radius: 16px;
  font-size: 14px;
  font-weight: 500;
}

.upload-btn:hover {
  background: #1a1a1a;
}

.file-img {
  width: 24px;
  height: 24px;
  object-fit: contain;
}

.action-img {
  width: 18px;
  height: 18px;
  object-fit: contain;
}

.document-card {
  background: white;
  border-radius: 4px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  flex: 1;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.12);
}

.list-header {
  display: grid;
  grid-template-columns: 2.5fr 1fr 1.2fr 1fr 0.8fr;
  gap: 16px;
  padding: 16px 20px;
  background: #f8f9fa;
  border-bottom: 1px solid #e9ecef;
  font-size: 13px;
  font-weight: 600;
  color: #495057;
}

.document-list {
  flex: 1;
  overflow-y: auto;
}

.document-item {
  display: grid;
  grid-template-columns: 2.5fr 1fr 1.2fr 1fr 0.8fr;
  gap: 16px;
  padding: 16px 20px;
  align-items: center;
  border-bottom: 1px solid #f8f9fa;
}

.document-item:hover {
  background: #f8f9fa;
}

.col-name {
  display: flex;
  align-items: center;
  gap: 12px;
}

.file-icon {
  width: 40px;
  height: 40px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  font-size: 24px;
}

.file-icon.pdf {
  background: #bdd6cd;
  color: #0f5132;
}

.file-icon.word {
  background: #cff4fc;
  color: #055160;
}

.file-icon.ppt {
  background: #fff3cd;
  color: #664d03;
}

.file-icon.image {
  background: #f8d7da;
  color: #842029;
}

.file-icon.other {
  background: #e9ecef;
  color: #495057;
}

.file-name {
  font-size: 14px;
  color: #212529;
  font-weight: 500;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.col-type,
.col-time {
  font-size: 14px;
  color: #6c757d;
}

.status-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  border-radius: 20px;
  font-size: 13px;
  font-weight: 500;
}

.status-emoji {
  font-size: 16px;
}

.processing .status-emoji {
  animation: spin 1s linear infinite;
}

.status-badge.success {
  background: #d1e7dd;
  color: #0f5132;
}

.status-badge.processing {
  background: #cff4fc;
  color: #055160;
}

.status-badge.error {
  background: #f8d7da;
  color: #842029;
}

.spin {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

.col-actions {
  display: flex;
  gap: 8px;
}

.action-btn {
  width: 36px;
  height: 36px;
  border: none;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
}

.action-btn.view {
  background: #e9ecef;
  color: #495057;
}

.action-btn.view:hover {
  background: #1a1a1a;
  color: white;
}

.action-btn.delete {
  background: #f8d7da;
  color: #842029;
}

.action-btn.delete:hover {
  background: #842029;
  color: white;
}

.empty-state {
  padding: 80px 20px;
  text-align: center;
  color: #6c757d;
}

.empty-emoji {
  font-size: 80px;
  margin-bottom: 16px;
  opacity: 0.3;
  display: block;
}

.empty-state h3 {
  font-size: 18px;
  color: #495057;
  margin-bottom: 8px;
}

.empty-state p {
  font-size: 14px;
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

.preview-modal {
  background: white;
  border-radius: 20px;
  width: 90%;
  max-width: 800px;
  max-height: 80vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.modal-header {
  padding: 20px 24px;
  border-bottom: 1px solid #e9ecef;
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-shrink: 0;
}

.modal-header h3 {
  font-size: 18px;
  color: #212529;
}

.close-btn {
  width: 36px;
  height: 36px;
  border: none;
  background: #f8f9fa;
  border-radius: 50%;
  font-size: 24px;
  color: #6c757d;
  cursor: pointer;
}

.modal-body {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
}

.text-preview pre {
  font-family: inherit;
  white-space: pre-wrap;
  line-height: 1.8;
  color: #212529;
  font-size: 14px;
}

.no-preview {
  text-align: center;
  padding: 60px 20px;
  color: #6c757d;
}

.no-preview-emoji {
  font-size: 64px;
  margin-bottom: 16px;
  opacity: 0.3;
  display: block;
}
</style>
