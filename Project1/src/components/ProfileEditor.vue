<template>
  <div class="profile-editor">
    <!-- <h2 class="editor-title">编辑个人信息</h2> -->
    <form @submit.prevent="handleSave" class="editor-form">
      <div class="form-columns">
        <div class="form-column">
          <div class="avatar-section">
            <div class="avatar-wrapper" @click="triggerAvatarInput">
              <img v-if="formData.avatar" :src="formData.avatar" alt="头像" class="avatar-img">
              <div v-else class="avatar-placeholder"></div>
              <div class="avatar-overlay">
                <span class="change-text">点击更换</span>
              </div>
            </div>
          </div>
          <div class="form-group">
            <label class="form-label">教师姓名</label>
            <input 
              type="text" 
              v-model="formData.teacherName" 
              class="form-input"
              placeholder="请输入教师姓名"
            />
          </div>
          <div class="form-group">
            <label class="form-label">教学学科</label>
            <input 
              type="text" 
              v-model="formData.subject" 
              class="form-input"
              placeholder="请输入教学学科"
            />
          </div>
          <div class="form-group">
            <label class="form-label">学校名称</label>
            <input 
              type="text" 
              v-model="formData.schoolName" 
              class="form-input"
              placeholder="请输入学校名称"
            />
          </div>
        </div>
        <div class="form-column">
          <div class="form-group">
            <label class="form-label">用户名</label>
            <input 
              type="text" 
              v-model="formData.username" 
              class="form-input"
              placeholder="请输入用户名"
            />
          </div>
          <div class="form-group">
            <label class="form-label">旧密码</label>
            <input 
              type="password" 
              v-model="formData.oldPassword" 
              class="form-input"
              placeholder="请输入旧密码"
            />
          </div>
          <div class="form-group">
            <label class="form-label">新密码</label>
            <input 
              type="password" 
              v-model="formData.newPassword" 
              class="form-input"
              placeholder="请输入新密码"
            />
          </div>
          <div class="form-group">
            <label class="form-label">新密码确认</label>
            <input 
              type="password" 
              v-model="formData.confirmPassword" 
              class="form-input"
              placeholder="请再次输入新密码"
            />
          </div>
          <div class="form-actions">
            <button type="button" @click="handleCancel" class="btn btn-cancel">
              取消
            </button>
            <button type="submit" class="btn btn-save">
              保存信息
            </button>
          </div>
        </div>
      </div>
    </form>
    <input
      type="file"
      ref="avatarInput"
      accept="image/*"
      @change="handleAvatarSelect"
      style="display: none"
    />
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import store from '../store'

const emit = defineEmits(['save', 'cancel'])
const avatarInput = ref(null)

const formData = reactive({
  teacherName: '',
  subject: '',
  schoolName: '',
  username: '',
  oldPassword: '',
  newPassword: '',
  confirmPassword: '',
  avatar: null
})

onMounted(() => {
  if (store.user) {
    formData.teacherName = store.user.teacherName || ''
    formData.subject = store.user.subject || ''
    formData.schoolName = store.user.schoolName || ''
    formData.username = store.user.username || ''
    formData.avatar = store.user.avatar || null
  }
})

const triggerAvatarInput = () => {
  avatarInput.value.click()
}

const handleAvatarSelect = (e) => {
  const file = e.target.files[0]
  if (file) {
    const reader = new FileReader()
    reader.onload = (event) => {
      formData.avatar = event.target.result
    }
    reader.readAsDataURL(file)
  }
}

const handleSave = () => {
  if (formData.newPassword && formData.newPassword !== formData.confirmPassword) {
    alert('两次输入的新密码不一致')
    return
  }

  const updateData = {
    teacherName: formData.teacherName,
    subject: formData.subject,
    schoolName: formData.schoolName,
    username: formData.username,
    avatar: formData.avatar
  }

  if (formData.newPassword) {
    updateData.password = formData.newPassword
  }

  store.updateUser(updateData)
  emit('save')
}

const handleCancel = () => {
  emit('cancel')
}
</script>

<style scoped>
.profile-editor {
  flex: 1;
  overflow: hidden;
  padding: 52px 40px;
  display: flex;
  flex-direction: column;
}

.editor-title {
  font-size: 18px;
  font-weight: 600;
  color: #46736d;
  margin-bottom: 20px;
  text-align: center;
}

.editor-form {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.form-columns {
  display: flex;
  margin: 0 auto;
  width: 100%;
  gap: 42px;
  flex: 1;
  align-items: flex-start;
}

.form-column {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.avatar-section {
  display: flex;
  justify-content: center;
  margin-bottom: 16px;
}

.avatar-wrapper {
  position: relative;
  width: 80px;
  height: 80px;
  border-radius: 50%;
  cursor: pointer;
  overflow: hidden;
  background: #bdd6cd;
}

.avatar-wrapper:hover .avatar-overlay {
  opacity: 1;
}

.avatar-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.avatar-placeholder {
  width: 100%;
  height: 100%;
}

.avatar-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: opacity 0.2s ease;
}

.change-text {
  color: white;
  font-size: 12px;
  font-weight: 600;
}

.form-group {
  margin-bottom: 22px;
}

.form-label {
  display: block;
  padding-left: 4px;
  font-size: 14px;
  font-weight: 500;
  color: #312f2f;
  margin-bottom: 6px;
}

.form-input {
  width: 100%;
  padding: 10px 14px;
  border: 2px solid #cce4db;
  border-radius: 16px;
  font-size: 13px;
  color: #312f2f;
  background: white;
  transition: border-color 0.2s ease, box-shadow 0.2s ease;
  box-sizing: border-box;
}

.form-input:focus {
  outline: none;
  border-color: #46736d;
  box-shadow: 0 0 0 3px rgba(70, 115, 109, 0.1);
}

.form-input::placeholder {
  color: #6b9a93;
}

.form-actions {
  display: flex;
  gap: 10px;
  margin-top: 30px;
  justify-content: flex-end;
}

.btn {
  flex: 0 0 auto;
  padding: 10px 32px;
  border: none;
  border-radius: 16px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: opacity 0.2s ease, transform 0.1s ease;
}


.btn:active {
  transform: scale(0.98);
}

.btn-cancel {
  background: #f0f5f3;
  color: #46736d;
}

.btn-save {
  background: #46736d;
  color: white;
}
</style>
