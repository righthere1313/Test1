<template>
  <div class="knowledge-sidebar">
    <div class="sidebar-card">
      <div class="stats-section">
        <h4>本地资料库统计</h4>
        <div class="stats-bar">
          <div class="stat-item">
            <div class="stat-value">{{ documents.length }}</div>
            <div class="stat-label">文档总数</div>
          </div>
          <div class="stat-divider"></div>
          <div class="stat-item">
            <div class="stat-value">{{ processedCount }}</div>
            <div class="stat-label">已向量化</div>
          </div>
          <div class="stat-divider"></div>
          <div class="stat-item">
            <div class="stat-value">{{ processingCount }}</div>
            <div class="stat-label">处理中</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  documents: {
    type: Array,
    default: () => []
  }
})

const processedCount = computed(() => 
  props.documents.filter(d => d.status === 'processed').length
)

const processingCount = computed(() => 
  props.documents.filter(d => d.status === 'processing').length
)
</script>

<style scoped>
.knowledge-sidebar {
  display: flex;
  flex-direction: column;
  gap: 16px;
  height: 100%;
  min-height: 0;
}

.sidebar-card {
  background: white;
  border-radius: 4px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.12);
  flex: 1;
  display: flex;
  flex-direction: column;
}

.stats-section h4 {
  font-size: 15px;
  color: #212529;
  margin-bottom: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  font-weight: 600;
}

.stats-bar {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.stat-item {
  text-align: center;
  padding: 16px;
  background: #f8f9fa;
  border-radius: 12px;
}

.stat-divider {
  display: none;
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
  color: #212529;
  line-height: 1.2;
  margin-bottom: 4px;
}

.stat-label {
  font-size: 13px;
  color: #6c757d;
}
</style>
