<template>
  <div class="history-section">
    <div v-for="group in groupedHistory" :key="group.year" class="year-group">
      <h3 class="year-title">{{ group.year }}年</h3>
      <div class="course-list">
        <div v-for="(course, index) in group.courses" :key="index" class="course-item">
          <div class="course-icon">
            <img src="/images/ppt-profile.png" alt="课件" class="course-icon-img">
          </div>
          <div class="course-info">
            <div class="course-title">{{ course.title }}</div>
            <div class="course-date">{{ course.date }}</div>
          </div>
          <button @click="downloadCourse(course)" class="download-btn">
            <img src="/images/下载.png" alt="下载" class="download-icon">
          </button>
        </div>
      </div>
    </div>
    <div v-if="historyCoursewares.length === 0" class="empty-state">
      <span class="empty-emoji">📁</span>
      <h3>暂无历史课件</h3>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  historyCoursewares: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['download'])

const groupedHistory = computed(() => {
  const groups = {}
  const sortedCourses = [...props.historyCoursewares].sort((a, b) => 
    new Date(b.date) - new Date(a.date)
  )
  sortedCourses.forEach(course => {
    const year = course.date.split('-')[0]
    if (!groups[year]) {
      groups[year] = []
    }
    groups[year].push(course)
  })
  const sortedYears = Object.keys(groups).sort((a, b) => parseInt(b) - parseInt(a))
  return sortedYears.map(year => ({
    year: year,
    courses: groups[year]
  }))
})

const downloadCourse = (course) => {
  emit('download', course)
}
</script>

<style scoped>
.history-section {
  flex: 1;
  overflow-y: auto;
  padding: 20px 40px;
}

.year-group {
  margin-bottom: 24px;
}

.year-title {
  font-size: 16px;
  font-weight: 600;
  color: #46736d;
  margin-bottom: 12px;
  padding-left: 8px;
  border-left: 3px solid #6b9a93;
}

.course-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.course-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 12px;
  background: #312f2f;
  border-radius: 16px;
  transition: all 0.5s ease;
}

.course-item:hover {
  opacity: 0.9;
  transform: scale(1.01);
}

.course-icon {
  width: 40px;
  height: 40px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.course-icon-img {
  width: 28px;
  height: 32px;
}

.course-info {
  flex: 1;
  min-width: 0;
}

.course-title {
  font-size: 14px;
  font-weight: 500;
  color: #ffffff;
  margin-bottom: 4px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.course-date {
  font-size: 12px;
  color: #ffffff;
}

.download-btn {
  width: 36px;
  height: 36px;
  background: #bbded6;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.2s ease;
  flex-shrink: 0;
}

.download-btn:hover {
  background: #ffffff;
}

.download-icon {
  width: 18px;
  height: 18px;
}

.empty-state {
  text-align: center;
  padding: 60px 20px;
  color: #6b9a93;
}

.empty-emoji {
  font-size: 48px;
  display: block;
  margin-bottom: 16px;
}

.empty-state h3 {
  font-size: 16px;
  font-weight: 400;
}
</style>
