<template>
  <div class="knowledge-sidebar">
    <div class="sidebar-card">
      <div class="stats-section">
        <h4>本地资料库统计</h4>
        <div class="counts-grid">
          <div class="count-item">
            <div class="count-number">{{ totalCount }}</div>
            <div class="count-label">总文件数</div>
          </div>
          <div class="count-item">
            <div class="count-number">{{ processedCount }}</div>
            <div class="count-label">已向量化</div>
          </div>
          <div class="count-item">
            <div class="count-number">{{ processingCount }}</div>
            <div class="count-label">处理中</div>
          </div>
        </div>
        <div class="chart-container">
          <canvas ref="typeChart"></canvas>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, nextTick, ref, watch } from 'vue'
import { Chart, registerables } from 'chart.js'

Chart.register(...registerables)

const props = defineProps({
  documents: {
    type: Array,
    default: () => []
  },
  allDocuments: {
    type: Array,
    default: () => []
  }
})

const typeChart = ref(null)
let chartInstance = null

const totalCount = computed(() => props.allDocuments.length)

const processedCount = computed(() => 
  props.allDocuments.filter(d => d.status === 'processed').length
)

const processingCount = computed(() => 
  props.allDocuments.filter(d => d.status === 'processing').length
)

const typeDistribution = computed(() => {
  const typeCount = {}
  
  if (props.allDocuments.length === 0) {
    return [
      { label: 'PDF文档', value: 5, color: '#8ab4aa' },
      { label: 'Word 文档', value: 3, color: '#bdd6cd' },
      { label: 'PPT 演示', value: 2, color: '#64a596' },
      { label: '文本文件', value: 1, color: '#312f2f' }
    ]
  }
  
  props.allDocuments.forEach(doc => {
    const type = doc.typeLabel || '其他'
    typeCount[type] = (typeCount[type] || 0) + 1
  })
  
  const colors = {
    'PDF文档': '#8ab4aa',
    'Word 文档': '#bdd6cd',
    'PPT 演示': '#64a596',
    '文本文件': '#312f2f',
    'Markdown 文档': '#495057',
    '图片': '#e9ecef'
  }
  
  return Object.entries(typeCount).map(([label, value]) => ({
    label,
    value,
    color: colors[label] || '#ced4da'
  }))
})

const initChart = () => {
  if (!typeChart.value) return
  
  const ctx = typeChart.value.getContext('2d')
  
  if (chartInstance) {
    chartInstance.destroy()
  }
  
  const data = typeDistribution.value
  
  chartInstance = new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: data.map(d => d.label),
      datasets: [{
        data: data.map(d => d.value),
        backgroundColor: data.map(d => d.color),
        borderWidth: 2,
        borderColor: '#fff'
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: true,
      aspectRatio: 1,
      plugins: {
        legend: {
          position: 'bottom',
          labels: {
            padding: 16,
            font: {
              size: 12
            },
            color: '#495057',
            usePointStyle: true,
            pointStyle: 'circle'
          }
        },
        tooltip: {
          callbacks: {
            label: function(context) {
              const label = context.label || ''
              const value = context.parsed || 0
              const total = context.dataset.data.reduce((a, b) => a + b, 0)
              const percentage = total > 0 ? ((value / total) * 100).toFixed(1) : 0
              return `${label}: ${value} (${percentage}%)`
            }
          }
        }
      },
      cutout: '60%'
    }
  })
}

onMounted(() => {
  nextTick(() => {
    initChart()
  })
})

watch(() => props.allDocuments, () => {
  nextTick(() => {
    initChart()
  })
}, { deep: true })
</script>

<style scoped>
.knowledge-sidebar {
  display: flex;
  flex-direction: column;
  gap: 16px;
  height: 100%;
  min-height: 0;
  overflow: visible;
}

.sidebar-card {
  background: white;
  border-radius: 4px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.12);
  flex: 1;
  display: flex;
  flex-direction: column;
  position: relative;
  overflow: visible;
}

.stats-section {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.stats-section h4 {
  font-size: 16px;
  color: #212529;
  margin-bottom: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  font-weight: 600;
  flex-shrink: 0;
}

.counts-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
  margin-bottom: 50px;
  flex-shrink: 0;
}

.count-item {
  background: #f8f9fa;
  border-radius: 12px;
  padding: 16px 12px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.count-number {
  font-size: 28px;
  font-weight: 700;
  color: #8ab4aa;
}

.count-label {
  font-size: 12px;
  color: #6c757d;
}

.chart-container {
  flex: 1;
  min-height: 0;
  display: flex;
  /* align-items: center; */
  justify-content: center;
}

.chart-container canvas {
  max-width: 100%;
  max-height: 100%;
}
</style>
