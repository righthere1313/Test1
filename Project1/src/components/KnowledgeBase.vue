<template>
  <div class="knowledge-page">
    <KnowledgeSidebar :documents="documents" :all-documents="allDocuments" />
    <div class="main-content">
      <div class="page-header">
        <div class="header-left">
          <h1>本地资料库</h1>
          <p>上传并管理教学参考资料，用于RAG检索增强</p>
        </div>
        <div class="header-right search-area">
          <div class="search-input-wrapper">
            <button v-if="isSearchMode" @click="clearSearch" class="back-btn">
              返回
            </button>
            <input
              v-model="searchQuery"
              type="text"
              placeholder="输入查询内容..."
              class="search-input"
            />
          </div>
          <button @click="searchFullText" class="search-btn full-text">
            <img src="/images/搜索.png" alt="搜索" class="btn-img">
            查找
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
        <transition name="fade" mode="out-in">
          <div :key="searchKey">
            <div
              v-for="(doc, index) in documents"
              :key="doc.id"
              class="document-item"
            >
              <div class="col-name">
                <div class="file-icon" :class="'file-icon-' + doc.typeClass">
                  <img 
                    :src="getFileIconSrc(doc.type)" 
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
                  @click="downloadDocument(doc)"
                  class="action-btn download"
                  title="下载"
                >
                  <img src="/images/下载.png" alt="下载" class="action-img">
                </button>
                <button
                  @click="deleteDocument(doc)"
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
        </transition>
      </div>
    </div>
  </div>
    <input
      type="file"
      ref="fileInput"
      multiple
      accept=".pdf,.doc,.docx,.ppt,.pptx,.jpg,.jpeg,.png,.gif,.txt"
      @change="handleFileUpload"
      style="display: none"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from "vue";
import KnowledgeSidebar from "./KnowledgeSidebar.vue";
import { documentsAPI, searchAPI } from "../services/api";

const fileInput = ref(null);
const searchQuery = ref("");
const documents = ref([]);
const allDocuments = ref([]); // 存储所有文档
const isSearchMode = ref(false); // 是否为搜索模式
const searchKey = ref(0); // 用于触发transition动画的key

onMounted(() => {
  loadDocuments();
});

const loadDocuments = async () => {
  try {
    const data = await documentsAPI.getList();
    // 过滤掉所有测试文档，只保留用户上传的
    const testFiles = [
      'smoke_kb.txt', 'load_4.txt', 'load_0.txt', 'load_6.txt', 
      'load_1.txt', 'load_9.txt', 'load_8.txt', 'load_2.txt', 
      'load_3.txt', 'load_5.txt', 'load_7.txt', 'seed.txt', 
      'connectivity.txt', 'kb.txt', 'connectivity_seed.txt', 't.txt',
      'ai_intro_seed.md'
    ];
    const filteredData = data.filter(doc => {
      const filename = doc.filename || '';
      const lowerFilename = filename.toLowerCase();
      return !testFiles.includes(filename) &&
             !lowerFilename.includes('sample') && 
             !lowerFilename.includes('test') &&
             !lowerFilename.includes('demo') &&
             !filename.includes('sample_doc') && 
             !filename.includes('sample-doc');
    });
    
    const docs = filteredData.map(doc => ({
      id: doc.document_id,
      name: doc.filename,
      type: doc.file_type,
      typeClass: doc.file_type,
      typeLabel: getTypeLabel(doc.file_type),
      uploadTime: formatDate(doc.created_at),
      status: 'processed',
      progress: 100,
      content: null,
      currentVersion: doc.current_version,
      updatedAt: doc.updated_at
    }));
    
    // 保存所有文档到allDocuments
    allDocuments.value = docs;
    // 如果不在搜索模式，显示所有文档
    if (!isSearchMode.value) {
      documents.value = [...docs]; // 使用展开运算符创建新数组
    }
  } catch (error) {
    console.error('加载文档失败:', error);
    // 404 错误时不弹出提示，显示空状态
    if (error.message !== '资源未找到' && error.message !== 'Not Found') {
      alert('加载文档失败：' + error.message);
    }
    // 如果API不可用，显示空列表而不是模拟数据
    console.log('API不可用，显示空列表');
    allDocuments.value = [];
    if (!isSearchMode.value) {
      documents.value = [];
    }
  }
};

const formatDate = (dateString) => {
  if (!dateString) return '';
  const date = new Date(dateString);
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
};

const getTypeLabel = (type) => {
  const typeMap = {
    'pdf': 'PDF文档',
    'docx': 'Word文档',
    'doc': 'Word文档',
    'ppt': 'PPT演示',
    'pptx': 'PPT演示',
    'txt': '文本文件',
    'md': 'Markdown文档',
    'markdown': 'Markdown文档',
    'image': '图片',
    'jpg': '图片',
    'jpeg': '图片',
    'png': '图片',
    'gif': '图片'
  };
  return typeMap[type] || '文件';
};

const getFileIconSrc = (type) => {
  const typeLower = type?.toLowerCase() || '';
  if (typeLower === 'pdf') {
    return '/images/文件类型/pdf.png';
  } else if (typeLower === 'docx' || typeLower === 'doc') {
    return '/images/文件类型/docx.png';
  } else if (typeLower === 'ppt' || typeLower === 'pptx') {
    return '/images/文件类型/ppt.png';
  } else if (typeLower === 'txt') {
    return '/images/文件类型/txt.png';
  } else if (['jpg', 'jpeg', 'png', 'gif', 'image'].includes(typeLower)) {
    return '/images/文件类型/png.png';
  } else if (typeLower === 'md' || typeLower === 'markdown') {
    return '/images/文件类型/txt.png';
  }else if (typeLower === 'mp4') {
    return '/images/文件类型/mp4.png';
  }
  return '/images/文件类型/txt.png';
};

const processedCount = computed(
  () => documents.value.filter((d) => d.status === "processed").length,
);

const processingCount = computed(
  () => documents.value.filter((d) => d.status === "processing").length,
);

const triggerUpload = () => {
  fileInput.value.click();
};

const handleFileUpload = async (e) => {
  const files = Array.from(e.target.files);
  for (const file of files) {
    try {
      // 根据接口文档支持的格式进行验证
      const supportedTypes = {
        "application/pdf": "pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
        "text/plain": "txt",
        "text/markdown": "md"
      };

      // 检查文件类型是否支持
      if (!supportedTypes[file.type]) {
        alert(`不支持的文件类型: ${file.type}\n支持的格式: .pdf, .docx, .txt, .md`);
        continue;
      }

      // 直接上传文件，不在界面上显示临时文档
      const uploadResponse = await documentsAPI.upload(file);
      
      // 创建最终文档对象
      const finalDoc = {
        id: uploadResponse.document_id,
        name: uploadResponse.filename,
        type: uploadResponse.file_type,
        typeClass: uploadResponse.file_type,
        typeLabel: getTypeLabel(uploadResponse.file_type),
        uploadTime: formatDate(uploadResponse.created_at || new Date().toISOString()),
        status: "processed",
        progress: 100,
        content: null,
        currentVersion: uploadResponse.version,
        chunkCount: uploadResponse.chunk_count,
        sections: uploadResponse.sections || []
      };
      
      // 只在allDocuments中添加，避免重复显示
      allDocuments.value.unshift(finalDoc);
      
      // 如果当前不是搜索模式，才显示在文档列表中
      if (!isSearchMode.value) {
        documents.value.unshift(finalDoc);
      } else {
        console.log('文件已上传，但在搜索模式下不显示:', uploadResponse.filename);
      }
      
      // 上传成功，不显示弹窗
      console.log('上传成功:', uploadResponse.filename);
    } catch (error) {
      console.error('上传失败:', error);
      // 404 错误时不弹出提示
      if (error.message !== '资源未找到' && error.message !== 'Not Found') {
        alert('上传失败：' + error.message);
      }
    }
  }
  e.target.value = "";
};

const downloadDocument = async (doc) => {
  try {
    // 使用当前版本下载，根据新接口文档
    await documentsAPI.downloadVersion(doc.id, doc.currentVersion || 1);
  } catch (error) {
    console.error('下载失败:', error);
    // 404 错误时不弹出提示
    if (error.message !== '资源未找到' && error.message !== 'Not Found') {
      alert('下载失败：' + error.message);
    }
  }
};

const searchFullText = async () => {
  if (!searchQuery.value.trim()) {
    // 如果搜索框为空，显示所有文档
    searchKey.value++;
    isSearchMode.value = false;
    documents.value = [...allDocuments.value];
    return;
  }
  try {
    searchKey.value++;
    isSearchMode.value = true;
    const query = searchQuery.value.trim().toLowerCase();
    
    // 1. 前端按标题搜索
    const frontendSearchResults = allDocuments.value.filter(doc => 
      doc.name.toLowerCase().includes(query)
    );
    
    // 2. 调用后端混合检索API
    let backendSearchResults = [];
    try {
      const response = await searchAPI.hybrid(searchQuery.value);
      console.log('混合检索响应:', response);
      
      const results = response.results || [];
      
      // 按document_id去重，避免同一个文档显示多次，并过滤所有测试文档
      const seenDocumentIds = new Set();
      const uniqueResults = [];
      const testFiles = [
        'smoke_kb.txt', 'load_4.txt', 'load_0.txt', 'load_6.txt', 
        'load_1.txt', 'load_9.txt', 'load_8.txt', 'load_2.txt', 
        'load_3.txt', 'load_5.txt', 'load_7.txt', 'seed.txt', 
        'connectivity.txt', 'kb.txt', 'connectivity_seed.txt', 't.txt'
      ];
      
      for (const result of results) {
        const metadata = result.metadata || {};
        const documentId = metadata.document_id;
        const filename = metadata.filename || '';
        const lowerFilename = filename.toLowerCase();
        
        // 过滤掉所有测试文档
        if (testFiles.includes(filename) ||
            lowerFilename.includes('sample') || 
            lowerFilename.includes('test') ||
            lowerFilename.includes('demo') ||
            filename.includes('sample_doc') || 
            filename.includes('sample-doc')) {
          continue;
        }
        
        // 如果已经见过这个document_id，跳过
        if (documentId && seenDocumentIds.has(documentId)) {
          continue;
        }
        
        // 记录已见过的document_id
        if (documentId) {
          seenDocumentIds.add(documentId);
        }
        
        uniqueResults.push(result);
      }
      
      // 根据接口文档格式处理搜索结果
      backendSearchResults = uniqueResults.map(result => {
        const metadata = result.metadata || {};
        return {
          id: metadata.document_id || result.chunk_id,
          name: metadata.filename || '搜索结果',
          type: metadata.filename?.split('.').pop() || 'txt',
          typeClass: metadata.filename?.split('.').pop() || 'txt',
          typeLabel: getTypeLabel(metadata.filename?.split('.').pop() || 'txt'),
          uploadTime: formatDate(new Date().toISOString()),
          status: 'processed',
          progress: 100,
          content: result.content || result.text,
          score: result.score,
          chunkId: result.chunk_id,
          page: metadata.page,
          version: metadata.version,
          searchMode: response.mode || 'hybrid'
        };
      });
    } catch (apiError) {
      console.error('后端搜索失败，仅使用前端搜索:', apiError);
    }
    
    // 3. 合并结果：前端搜索结果置顶，然后是后端搜索结果，去重
    const finalResults = [];
    const finalSeenIds = new Set();
    
    // 添加前端搜索结果
    for (const doc of frontendSearchResults) {
      if (!finalSeenIds.has(doc.id)) {
        finalSeenIds.add(doc.id);
        finalResults.push({ ...doc, isFrontendResult: true });
      }
    }
    
    // 添加后端搜索结果（排除已在前端结果中的）
    for (const doc of backendSearchResults) {
      if (!finalSeenIds.has(doc.id)) {
        finalSeenIds.add(doc.id);
        finalResults.push(doc);
      }
    }
    
    documents.value = finalResults;
  } catch (error) {
    console.error('搜索失败:', error);
    // 404 错误时不弹出提示
    if (error.message !== '资源未找到' && error.message !== 'Not Found') {
      alert('搜索失败：' + error.message);
    }
  }
};



const deleteDocument = async (doc) => {
  if (confirm(`确定要删除文档 "${doc.name}" 吗？`)) {
    try {
      await documentsAPI.delete(doc.id);
      
      const index = documents.value.findIndex((d) => d.id === doc.id);
      if (index > -1) {
        documents.value.splice(index, 1);
      }
      
      const allIndex = allDocuments.value.findIndex((d) => d.id === doc.id);
      if (allIndex > -1) {
        allDocuments.value.splice(allIndex, 1);
      }
      
      console.log('文档已删除:', doc.name);
    } catch (error) {
      console.error('删除失败:', error);
      alert('删除失败：' + error.message);
    }
  }
};

// 清空搜索
const clearSearch = () => {
  searchKey.value++;
  searchQuery.value = '';
  isSearchMode.value = false;
  documents.value = [...allDocuments.value]; // 显示所有文档
};
</script>

<style scoped>
/* 返回按钮样式 */
.back-btn {
    background: #8ab4aa;
    color: #000000;
    border: none;
    border-radius: 12px;
    padding: 6px 10px;
    font-size: 12px;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s ease;
    margin-right: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
}

.back-btn:hover {
  background: #64a596;
}
/* 淡入淡出动画 */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

.knowledge-page {
  height: calc(100vh - 110px);
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

.search-btn.similarity {
  background: #8ab4aa;
  color: white;
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
  grid-template-columns: 2.5fr 1fr 1.2fr 1fr 1fr;
  gap: 20px;
  padding: 20px 32px 20px 32px;
  background: #f8f9fa;
  border-bottom: 1px solid #e9ecef;
  font-size: 16px;
  font-weight: 600;
  color: #495057;
}

.document-list {
  flex: 1;
  overflow-y: auto;
  max-height: calc(100vh - 280px); /* 限制最大高度，避免拉长盒子 */
}

.document-item {
  display: grid;
  grid-template-columns: 2.5fr 1fr 1.2fr 1fr 1fr;
  gap: 20px;
  padding: 20px 32px 20px 32px;
  align-items: center;
  border-bottom: 1px solid #f8f9fa;
}

.document-item:hover {
  background: #f8f9fa;
}

.col-name {
  display: flex;
  align-items: center;
  gap: 18px;
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

.file-icon-pdf {
  background: #fce2e2;
}

.file-icon-docx {
  background: #dde7ec;
}

.file-icon-doc {
  background: #d3e3ec;
}

.file-icon-ppt {
  background: #fff1c4;
}

.file-icon-pptx {
  background: #fff1c4;
}

.file-icon-txt {
  background: #e7e5ff;
}

.file-icon-md {
  background: #bafff5;
}

.file-icon-markdown {
  background: #dddcff;
}

.file-icon-image {
  background: #f8d7da;
}

.file-icon-png {
  background: #f8d7da;
}

.file-name {
  font-size: 14px;
  color: #212529;
  font-weight: 500;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 200px; /* 限制最大宽度 */
  display: inline-block; /* 确保宽度限制生效 */
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

.action-btn.download {
  background: #8ab4aa;
  color: white;
}

.action-btn.download:hover {
  background: #64a596;
}

.action-btn.delete {
  background: #f8d7da;
  color: #842029;
}

.action-btn.delete:hover {
  background: #ff8f98;
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
