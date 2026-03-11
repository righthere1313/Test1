<template>
  <div class="profile-page">
    <div class="profile-container">
      <div class="profile-header">
        <h2>个人主页</h2>
      </div>
      <div class="profile-content">
        <div class="profile-left">
          <div class="profile-card">
            <div class="avatar-section">
              <div class="avatar">
                <img v-if="store.user.avatar" :src="store.user.avatar" alt="头像" class="avatar-img">
              </div>
            </div>
            <div class="username-section">
              <h3 class="username">{{ store.user.username }}</h3>
            </div>
            <div class="info-section">
              <div class="info-item">
                <span class="info-label">教师姓名：</span>
                <span class="info-value">{{ store.user.teacherName || '未设置' }}</span>
              </div>
              <div class="info-item">
                <span class="info-label">教学学科：</span>
                <span class="info-value">{{ store.user.subject || '未设置' }}</span>
              </div>
              <div class="info-item">
                <span class="info-label">学校名称：</span>
                <span class="info-value">{{ store.user.schoolName || '未设置' }}</span>
              </div>
            </div>
            <div class="action-buttons">
              <button @click="goToEdit" class="btn-edit">编辑信息</button>
              <button @click="handleLogout" class="btn-logout">退出登录</button>
            </div>
          </div>
        </div>
        <div class="profile-divider"></div>
        <div class="profile-right">
          <transition name="fade" mode="out-in">
            <HistoryCoursewareList 
              v-if="!showEditor" 
              :key="'history'"
              :history-coursewares="historyCoursewares"
              @download="downloadCourse"
            />
            <ProfileEditor 
              v-else 
              :key="'editor'"
              @save="handleSave"
              @cancel="handleCancelEdit"
            />
          </transition>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import store from '../store'
import HistoryCoursewareList from './HistoryCoursewareList.vue'
import ProfileEditor from './ProfileEditor.vue'

const router = useRouter()
const showEditor = ref(false)

const historyCoursewares = ref([
  { title: '勾股定理教学课件', date: '2025-03-04' },
  { title: '二次根式复习课', date: '2025-02-28' },
  { title: '函数图像分析', date: '2024-12-15' },
  { title: '三角函数入门', date: '2024-11-20' },
])

const goToEdit = () => {
  showEditor.value = true
}

const handleSave = () => {
  showEditor.value = false
}

const handleCancelEdit = () => {
  showEditor.value = false
}

const downloadCourse = (course) => {
  alert(`下载课件：${course.title}`)
}

const handleLogout = () => {
  if (confirm('确定要退出登录吗？')) {
    store.logout()
    router.push('/')
  }
}
</script>

<style scoped>
.profile-page {
  width: 100%;
  height: calc(100vh - 120px);
  display: flex;
  align-items: flex-start;
  justify-content: center;
  position: relative;
  z-index: 1;
}

.profile-container {
  width: 100%;
  height: 100%;
  background: white;
  border-radius: 4px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.12);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.profile-header {
  background: #ffffff;
  padding: 16px 32px;
  border-bottom: 1px solid #e9ecef;
}

.profile-header h2 {
  color: #000000;
  font-size: 22px;
  font-weight: 700;
  margin: 0;
}

.profile-content {
  flex: 1;
  display: flex;
  overflow: hidden;
}

.profile-left {
  width: 280px;
  padding: 24px;
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
}

.profile-card {
  background: #f8f9fa;
  border-radius: 12px;
  padding: 20px;
  display: flex;
  flex-direction: column;
  align-items: center;
  height: 100%;
}

.avatar-section {
  margin-bottom: 16px;
}

.avatar {
  width: 100px;
  height: 100px;
  border-radius: 50%;
  background: #bdd6cd;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  border: 3px solid #8ab4aa;
}

.avatar-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}



.username-section {
  margin-bottom: 20px;
}

.username {
  font-size: 18px;
  font-weight: 600;
  color: #212529;
  margin: 0;
}

.info-section {
  width: 100%;
  margin-bottom: auto;
}

.info-item {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  padding: 6px 0;
  border-bottom: 1px solid #e9ecef;
}

.info-label {
  color: #6c757d;
}

.info-value {
  color: #212529;
  font-weight: 500;
  text-align: right;
  flex: 1;
  margin-left: 8px;
}

.action-buttons {
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-top: 16px;
}

.btn-edit,
.btn-logout {
  padding: 10px 16px;
  border: none;
  border-radius: 16px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: opacity 0.2s ease;
  width: 100%;
}

.btn-edit {
  background: #8ab4aa;
  color: white;
}

.btn-edit:hover {
  background-color: #326e60;
}

.btn-logout {
  background: #312f2f;
  color: white;
}

.btn-logout:hover {
  background-color: #000000;
}

.profile-divider {
  width: 2px;
  background: #bdd6cd;
  flex-shrink: 0;
}

.profile-right {
  flex: 1;
  display: flex;
  overflow: hidden;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
