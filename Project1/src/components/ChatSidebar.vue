<template>
  <div class="chat-sidebar">
    <div class="profile-section">
      <div class="avatar" @click="editAvatar">
        <img v-if="store.user.avatar" :src="store.user.avatar" alt="头像" class="avatar-img">
      </div>
      <div class="username-wrapper">
        <span
          v-if="!isEditingUsername"
          class="username"
          @click="isEditingUsername = true"
        >
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
      <div class="info-display">
        <div class="info-item">
          <span class="info-label">教师姓名：</span>
          <span class="info-value">{{
            store.user.teacherName || "未设置"
          }}</span>
        </div>
        <div class="info-item">
          <span class="info-label">教学学科：</span>
          <span class="info-value">{{ store.user.subject || "未设置" }}</span>
        </div>
        <div class="info-item">
          <span class="info-label">学校名称：</span>
          <span class="info-value">{{
            store.user.schoolName || "未设置"
          }}</span>
        </div>
        <p class="info-note">这些信息将作为课件署名</p>
      </div>
    </div>
    <div class="history-card">
      <div class="history-section">
        <h4>历史课件</h4>
        <div class="history-list">
          <div
            v-for="(item, index) in historyCoursewares"
            :key="index"
            class="history-item"
            @click="goToProfile"
          >
            <div class="history-icon">
              <img src="/images/ppt.png" alt="课件" class="history-icon-emoji">
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
import { ref, onMounted, nextTick } from "vue";
import { useRouter } from "vue-router";
import store from "../store";

const router = useRouter();
const isEditingUsername = ref(false);
const editUsername = ref("");
const usernameInput = ref(null);

const historyCoursewares = ref([
  { title: "勾股定理教学课件", date: "2024-03-04" },
  { title: "二次根式复习课", date: "2024-03-03" },
  { title: "函数图像分析", date: "2024-03-02" },
]);

const editAvatar = () => {
  router.push("/profile");
};

const saveUsername = () => {
  if (editUsername.value.trim()) {
    store.updateUser({ username: editUsername.value.trim() });
  }
  isEditingUsername.value = false;
};

const goToProfile = () => {
  router.push("/profile");
};
</script>

<style scoped>
.chat-sidebar {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: white;
  border-radius: 4px;
  overflow: hidden;
  padding: 16px;
  gap: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.12);
}

.profile-section {
  padding: 16px 16px;
  text-align: center;
  border-bottom: 1px solid #e9ecef;
  background: white;
}

.avatar {
  width: 52px;
  height: 52px;
  border-radius: 50%;
  background: #bdd6cd;
  color: #0f5132;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 10px;
  cursor: pointer;
  transition: transform 0.2s ease;
}

.avatar:hover {
  transform: scale(1.05);
}

.avatar-icon {
  font-size: 26px;
}

.avatar-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  border-radius: 50%;
}

.username-wrapper {
  display: flex;
  justify-content: center;
}

.username {
  font-size: 14px;
  font-weight: 600;
  color: #212529;
  cursor: pointer;
  padding: 3px 6px;
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
  padding: 14px 16px;
  background: white;
  border-radius: 12px;
}

.history-card {
  flex: 1;
  background: #2d2d2d;
  border-radius: 12px;
  overflow: hidden;
}

.info-section h4,
.history-section h4 {
  font-size: 13px;
  color: #212529;
  margin-bottom: 12px;
  font-weight: 600;
}

.history-section h4 {
  color: white;
}

.info-display {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.info-item {
  display: flex;
  justify-content: space-between;
  font-size: 13px;
}

.info-label {
  color: #6c757d;
}

.info-value {
  color: #212529;
  font-weight: 500;
}

.info-note {
  font-size: 11px;
  color: #6c757d;
  margin-top: 8px;
  font-style: italic;
  text-align: center;
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
  gap: 8px;
  padding: 4px 8px;
  background: #bdd6cd;
  border-radius: 8px;
  margin-bottom: 6px;
  cursor: pointer;
  transition: transform 0.2s ease;
}

.history-item:hover {
  transform: translateX(4px);
}

.history-icon {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  color: #ffffff;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.history-icon-emoji {
  width: 18px;
  height: 18px;
  object-fit: contain;
}

.history-info {
  flex: 1;
  min-width: 0;
}

.history-title {
  font-size: 12px;
  font-weight: 500;
  color: #000000;
  margin-bottom: 1px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.history-date {
  font-size: 10px;
  color: #000000;
}
</style>
