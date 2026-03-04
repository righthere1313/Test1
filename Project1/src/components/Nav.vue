<template>
  <header class="header">
    <div class="logo">
      <span class="logo-icon">🤖</span>
      <span class="logo-text">多模态AI教学智能体</span>
    </div>
    <nav class="nav">
      <router-link to="/chat" class="nav-item" active-class="active">
        <span class="nav-icon">💬</span>
        对话设计
      </router-link>
      <router-link to="/knowledge" class="nav-item" active-class="active">
        <span class="nav-icon">📚</span>
        知识库
      </router-link>
      <router-link to="/preview" class="nav-item" active-class="active">
        <span class="nav-icon">📖</span>
        课件预览
      </router-link>
    </nav>
    <div class="user-menu" @mouseenter="showDropdown = true" @mouseleave="showDropdown = false">
      <div class="user-info">
        <div class="user-avatar">
          <span class="avatar-icon">👤</span>
        </div>
        <span class="username">{{ store.user.username }}</span>
      </div>
      <div v-if="showDropdown" class="dropdown-menu">
        <button @click="handleLogout" class="dropdown-item">
          <span class="dropdown-icon">🚪</span>
          退出登录
        </button>
      </div>
    </div>
  </header>
</template>

<script setup>
import { ref } from 'vue'
import store from '../store'

const showDropdown = ref(false)

const handleLogout = () => {
  if (confirm('确定要退出登录吗？')) {
    console.log('退出登录')
  }
}
</script>

<style scoped>
.header {
  background: #312f2f;
  padding: 16px 24px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-radius: 16px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
  flex-shrink: 0;
}

.logo {
  display: flex;
  align-items: center;
  gap: 12px;
  color: white;
}

.logo-icon {
  font-size: 32px;
}

.logo-text {
  font-size: 18px;
  font-weight: 600;
}

.nav {
  display: flex;
  gap: 8px;
  background: #1a1a1a;
  padding: 6px;
  border-radius: 14px;
  margin-left: auto;
  margin-right: 24px;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 20px;
  color: #b0b0b0;
  text-decoration: none;
  border-radius: 12px;
  transition: all 0.2s ease;
  font-size: 14px;
  font-weight: 500;
}

.nav-icon {
  font-size: 18px;
}

.nav-item:hover {
  color: white;
  background: #2a2a2a;
}

.nav-item.active {
  background: white;
  color: #000000;
}

.user-menu {
  position: relative;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 12px;
  color: white;
  cursor: pointer;
  padding: 8px 16px;
  border-radius: 12px;
  transition: background 0.2s ease;
}

.user-info:hover {
  background: #1a1a1a;
}

.user-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: #d1e7dd;
  color: #0f5132;
  display: flex;
  align-items: center;
  justify-content: center;
}

.avatar-icon {
  font-size: 20px;
}

.username {
  font-size: 14px;
  font-weight: 500;
}

.dropdown-menu {
  position: absolute;
  top: 100%;
  right: 0;
  margin-top: 8px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
  min-width: 160px;
  z-index: 100;
}

.dropdown-item {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 16px;
  border: none;
  background: none;
  font-size: 14px;
  color: #212529;
  cursor: pointer;
  border-radius: 12px;
  transition: background 0.2s ease;
}

.dropdown-icon {
  font-size: 16px;
}

.dropdown-item:hover {
  background: #f8f9fa;
}
</style>
