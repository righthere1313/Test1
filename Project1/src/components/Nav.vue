<template>
  <header class="header">
    <div class="logo">
      <span class="logo-icon">
        <img src="/images/logo.jpg" alt="Logo" class="logo-img">
      </span>
      <span class="logo-text">多模态AI教学智能体</span>
    </div>
    <nav class="nav">
      <router-link 
        v-for="(item, index) in navItems" 
        :key="item.path"
        :to="item.path" 
        class="nav-item" 
        active-class="active"
      >
        <span class="nav-icon">
          <span :class="item.iconClass"></span>
        </span>
        {{ item.name }}
      </router-link>
    </nav>
    <div class="user-menu">
      <div class="user-menu-content" @click="goToProfile">
        <span class="username">{{ store.user.username }}</span>
        <span class="profile-text">的个人主页</span>
        <div class="user-avatar">
          <img v-if="store.user.avatar" :src="store.user.avatar" alt="头像" class="avatar-img">
        </div>
      </div>
      <div class="user-dropdown">
        <button @click="handleLogout" class="logout-btn">退出登录</button>
      </div>
    </div>
  </header>
</template>

<script setup>
import { computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import store from '../store'

const router = useRouter()
const route = useRoute()

const navItems = computed(() => [
  { path: '/chat', name: '对话聊天', iconClass: 'chat-icon' },
  { path: '/preview', name: '课件预览', iconClass: 'document-icon' },
  { path: '/knowledge', name: '资料管理', iconClass: 'library-icon' },
  { path: '/history-generation', name: '历史生成', iconClass: 'history-icon' },
  { 
    path: store.isLoggedIn ? '/introduction' : '/', 
    name: '功能介绍', 
    iconClass: 'home-icon' 
  }
])

const goToProfile = () => {
  router.push('/profile')
}

const handleLogout = () => {
  if (confirm('确定要退出登录吗？')) {
    store.logout()
    router.push('/')
  }
}
</script>

<style scoped>
.header {
  background: #1a1a1a;
  padding: 10px 24px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-radius: 4px;
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.2);
  flex-shrink: 0;
  position: relative;
  z-index: 10;
}

.logo {
  display: flex;
  align-items: center;
  gap: 12px;
  color: #cce4db;
}

.logo-icon {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.logo-img {
  width: 100%;
  height: 100%;
  object-fit: contain;
}

.logo-text {
  font-size: 18px;
  font-weight: 600;
}

.nav {
  position: relative;
  display: flex;
  gap: 8px;
  background: #1a1a1a;
  /* padding: 4px; */
  border-radius: 16px;
  margin-left: auto;
  margin-right: 24px;
  height: 40px;
}

.nav-item {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 0;
  color: white;
  text-decoration: none;
  border-radius: 8px;
  font-size: 15px;
  font-weight: 500;
  height: 100%;
  z-index: 10;
  transition: background-color 0.5s ease;
}

.nav-item:nth-child(1) {
  width: 120px;
}

.nav-item:nth-child(2) {
  width: 120px;
}

.nav-item:nth-child(3) {
  width: 120px;
}

.nav-item:nth-child(4) {
  width: 120px;
}

.nav-item:nth-child(5) {
  width: 120px;
}

.nav-icon {
  width: 18px;
  height: 18px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.nav-icon span {
  display: block;
}

.home-icon {
  width: 14px;
  height: 14px;
  position: relative;
}

.home-icon::before {
  content: '';
  position: absolute;
  top: 0;
  left: 1px;
  width: 0;
  height: 0;
  border-left: 6px solid transparent;
  border-right: 6px solid transparent;
  border-bottom: 8px solid currentColor;
}

.home-icon::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 2px;
  width: 10px;
  height: 6px;
  border-bottom: 2px solid currentColor;
  border-left: 2px solid currentColor;
  border-right: 2px solid currentColor;
}

.chat-icon {
  width: 14px;
  height: 14px;
  position: relative;
  border: 2px solid currentColor;
  border-radius: 4px;
}

.chat-icon::before {
  content: '';
  position: absolute;
  bottom: -3px;
  left: 2px;
  width: 0;
  height: 0;
  border-left: 3px solid transparent;
  border-right: 3px solid transparent;
  border-top: 4px solid currentColor;
}

.chat-icon::after {
  content: '';
  position: absolute;
  top: 2px;
  left: 2px;
  width: 6px;
  height: 2px;
  background: currentColor;
  border-radius: 1px;
  box-shadow: 0 3px 0 currentColor;
}

.library-icon {
  width: 14px;
  height: 14px;
  position: relative;
}

.library-icon::before {
  content: '';
  position: absolute;
  bottom: 0;
  left: 0;
  width: 3px;
  height: 12px;
  background: currentColor;
  border-radius: 1px 1px 0 0;
}

.library-icon::after {
  content: '';
  position: absolute;
  bottom: 0;
  right: 0;
  width: 3px;
  height: 12px;
  background: currentColor;
  border-radius: 1px 1px 0 0;
  box-shadow: -4px 0 0 currentColor;
}

.document-icon {
  width: 14px;
  height: 14px;
  position: relative;
  border: 2px solid currentColor;
  border-radius: 1px 4px 1px 1px;
}

.document-icon::before {
  content: '';
  position: absolute;
  top: 0;
  right: 0;
  width: 6px;
  height: 6px;
  border-left: 2px solid currentColor;
  border-bottom: 2px solid currentColor;
}

.document-icon::after {
  content: '';
  position: absolute;
  left: 2px;
  top: 6px;
  width: 6px;
  height: 2px;
  background: currentColor;
  border-radius: 1px;
  box-shadow: 0 3px 0 currentColor;
}

.history-icon {
  width: 14px;
  height: 14px;
  position: relative;
}

.history-icon::before {
  content: '';
  position: absolute;
  bottom: 0;
  left: 0;
  width: 12px;
  height: 10px;
  border: 2px solid currentColor;
  border-radius: 2px;
}

.history-icon::after {
  content: '';
  position: absolute;
  top: 2px;
  left: 50%;
  transform: translateX(-50%);
  width: 6px;
  height: 2px;
  background: currentColor;
  border-radius: 1px;
  box-shadow: 0 3px 0 currentColor;
}


.nav-item.active {
  background-color: black;
  box-shadow: 0 0 15px rgba(0, 0, 0, 0.4),
              0 0 30px rgba(0, 0, 0, 0.2);
}

.user-menu {
  position: relative;
  display: flex;
  align-items: center;
  gap: 12px;
  color: white;
  cursor: pointer;
  padding: 8px 16px;
  border-radius: 4px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.user-menu-content {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 15px;
}

.user-dropdown {
  position: absolute;
  top: 100%;
  right: 20px;
  margin-top: 16px;
  background: white;
  border-radius: 16px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.2);
  opacity: 0;
  visibility: hidden;
  transform: translateY(-10px);
  transition: all 0.3s ease;
  z-index: 100;
}

.user-menu:hover .user-dropdown {
  opacity: 1;
  visibility: visible;
  transform: translateY(0);
}

.logout-btn {
  padding: 12px 14px;
  background: #bdd6cd;
  color: #000000;
  border: none;
  width: 140px;
  text-align: center;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  border-radius: 16px;
  transition: background-color 0.2s ease;
}

.logout-btn:hover {
  background-color: #ffffff;
}

.user-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: #bdd6cd;
  color: #0f5132;
  display: flex;
  align-items: center;
  justify-content: center;
}

.avatar-icon {
  width: 20px;
  height: 20px;
  position: relative;
}

.avatar-icon::before {
  content: '';
  position: absolute;
  top: 0;
  left: 50%;
  transform: translateX(-50%);
  width: 8px;
  height: 8px;
  border: 2px solid #0f5132;
  border-radius: 50%;
}

.avatar-icon::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 50%;
  transform: translateX(-50%);
  width: 14px;
  height: 8px;
  border: 2px solid #0f5132;
  border-radius: 8px 8px 0 0;
  border-bottom: none;
}

.avatar-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  border-radius: 50%;
}

.username {
  font-weight: 500;
}

.profile-text {
  font-weight: 500;
  color: #ffffff;
}
</style>
