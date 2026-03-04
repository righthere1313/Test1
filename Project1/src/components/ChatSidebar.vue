<template>
  <div class="chat-sidebar">
    <div class="profile-section">
      <div class="avatar" @click="editAvatar">
        <span class="avatar-icon">👤</span>
      </div>
      <div class="username-wrapper">
        <span v-if="!isEditingUsername" class="username" @click="isEditingUsername = true">
          {{ store.user.username }}
        </span>
        <input 
          v-else 
          v-model="editUsername" 
          @blur="saveUsername" 
          @keyup.enter="saveUsername"
          class="username-input"
          ref="usernameInput"
        />
      </div>
    </div>
    <div class="info-section">
      <h4>个人信息</h4>
      <div v-if="!isEditingInfo" class="info-display">
        <div class="info-item">
          <span class="info-label">教学学科：</span>
          <span class="info-value">{{ store.userInfo.subject || '未设置' }}</span>
        </div>
        <div class="info-item">
          <span class="info-label">教学年级：</span>
          <span class="info-value">{{ store.userInfo.grade || '未设置' }}</span>
        </div>
        <div class="info-item">
          <span class="info-label">班级人数：</span>
          <span class="info-value">{{ store.userInfo.students || '未设置' }}</span>
        </div>
        <button @click="isEditingInfo = true" class="edit-info-btn">编辑</button>
      </div>
      <div v-else class="info-edit">
        <div class="form-group">
          <label>教学学科：</label>
          <input v-model="editInfo.subject" type="text" placeholder="如：数学" />
        </div>
        <div class="form-group">
          <label>教学年级：</label>
          <input v-model="editInfo.grade" type="text" placeholder="如：八年级" />
        </div>
        <div class="form-group">
          <label>班级人数：</label>
          <input v-model="editInfo.students" type="number" placeholder="如：45" />
        </div>
        <div class="edit-actions">
          <button @click="cancelEditInfo" class="btn-secondary">取消</button>
          <button @click="saveInfo" class="btn-primary">保存</button>
        </div>
      </div>
    </div>
    <div class="history-card">
      <div class="history-section">
        <h4>历史课件</h4>
        <div class="history-list">
          <div v-for="(item, index) in historyCoursewares" :key="index" class="history-item">
            <div class="history-icon">
              <span class="history-icon-emoji">📄</span>
            </div>
            <div class="history-info">
              <div class="history-title">{{ item.title }}</div>
              <div class="history-date">{{ item.date }}</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, nextTick } from 'vue'
import store from '../store'

const isEditingUsername = ref(false)
const editUsername = ref('')
const usernameInput = ref(null)
const isEditingInfo = ref(false)
const editInfo = reactive({
  subject: '',
  grade: '',
  students: ''
})

const historyCoursewares = ref([
  { title: '勾股定理教学课件', date: '2024-03-04' },
  { title: '二次根式复习课', date: '2024-03-03' },
  { title: '函数图像分析', date: '2024-03-02' }
])

const editAvatar = () => {
  console.log('编辑头像')
}

const saveUsername = () => {
  if (editUsername.value.trim()) {
    store.updateUser({ username: editUsername.value.trim() })
  }
  isEditingUsername.value = false
}

const saveInfo = () => {
  store.updateUserInfo({ ...editInfo })
  isEditingInfo.value = false
}

const cancelEditInfo = () => {
  editInfo.subject = store.userInfo.subject
  editInfo.grade = store.userInfo.grade
  editInfo.students = store.userInfo.students
  isEditingInfo.value = false
}

onMounted(() => {
  editInfo.subject = store.userInfo.subject
  editInfo.grade = store.userInfo.grade
  editInfo.students = store.userInfo.students
})
</script>

<style scoped>
.chat-sidebar {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: white;
  border-radius: 16px;
  overflow: hidden;
  padding: 16px;
  gap: 16px;
}

.profile-section {
  padding: 24px 20px;
  text-align: center;
  border-bottom: 1px solid #e9ecef;
  background: white;
}

.avatar {
  width: 64px;
  height: 64px;
  border-radius: 50%;
  background: #d1e7dd;
  color: #0f5132;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 12px;
  cursor: pointer;
  transition: transform 0.2s ease;
}

.avatar:hover {
  transform: scale(1.05);
}

.avatar-icon {
  font-size: 32px;
}

.username-wrapper {
  display: flex;
  justify-content: center;
}

.username {
  font-size: 16px;
  font-weight: 600;
  color: #212529;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 6px;
  transition: background 0.2s ease;
}

.username:hover {
  background: #f8f9fa;
}

.username-input {
  font-size: 16px;
  font-weight: 600;
  color: #212529;
  text-align: center;
  padding: 4px 8px;
  border: 2px solid #1a1a1a;
  border-radius: 6px;
  outline: none;
  width: 100%;
  max-width: 200px;
}

.info-section {
  padding: 20px;
  background: white;
  border-radius: 12px;
}

.history-card {
  flex: 1;
  background: #312f2f;
  border-radius: 12px;
  overflow: hidden;
}

.info-section h4,
.history-section h4 {
  font-size: 14px;
  color: #212529;
  margin-bottom: 16px;
  font-weight: 600;
}

.history-section h4 {
  color: white;
}

.info-display {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.info-item {
  display: flex;
  justify-content: space-between;
  font-size: 14px;
}

.info-label {
  color: #6c757d;
}

.info-value {
  color: #212529;
  font-weight: 500;
}

.edit-info-btn {
  margin-top: 12px;
  padding: 8px 16px;
  background: #f8f9fa;
  color: #495057;
  border: none;
  border-radius: 10px;
  font-size: 14px;
  cursor: pointer;
  width: 100%;
}

.edit-info-btn:hover {
  background: #e9ecef;
}

.info-edit {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.form-group label {
  font-size: 13px;
  color: #495057;
}

.form-group input {
  padding: 10px 12px;
  border: 1px solid #dee2e6;
  border-radius: 10px;
  font-size: 14px;
  outline: none;
  transition: border-color 0.2s ease;
}

.form-group input:focus {
  border-color: #1a1a1a;
}

.edit-actions {
  display: flex;
  gap: 10px;
  margin-top: 8px;
}

.btn-secondary,
.btn-primary {
  flex: 1;
  padding: 10px 16px;
  border: none;
  border-radius: 10px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
}

.btn-secondary {
  background: #f8f9fa;
  color: #495057;
}

.btn-secondary:hover {
  background: #e9ecef;
}

.btn-primary {
  background: #1a1a1a;
  color: white;
}

.btn-primary:hover {
  background: #2d2d2d;
}

.history-section {
  padding: 20px;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.history-list {
  flex: 1;
  overflow-y: auto;
}

.history-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: #ffd967;
  border-radius: 12px;
  margin-bottom: 10px;
  cursor: pointer;
  transition: transform 0.2s ease;
}

.history-item:hover {
  transform: translateX(4px);
}

.history-icon {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  background: #ffd967;
  color: #664d03;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.history-icon-emoji {
  font-size: 20px;
}

.history-info {
  flex: 1;
  min-width: 0;
}

.history-title {
  font-size: 14px;
  font-weight: 500;
  color: #664d03;
  margin-bottom: 2px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.history-date {
  font-size: 12px;
  color: #856404;
}
</style>
