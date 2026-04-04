<template>
  <div class="app-container" :class="{ 'gradient-bg': !isHomeOrLogin || isLoggedIn }">
    <BubbleBackground v-if="(isHomeOrLogin && !isLoggedIn) || isLoading" />
    <LoadingOverlay v-if="isLoading" />
    <div v-if="!isLoading" class="app-wrapper">
      <Nav v-if="isLoggedIn" />
      <main class="main-content">
        <router-view v-slot="{ Component }">
          <transition name="fade" mode="out-in">
            <component :is="Component" :key="route.path" />
          </transition>
        </router-view>
      </main>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import Nav from "./components/Nav.vue";
import BubbleBackground from "./components/BubbleBackground.vue";
import LoadingOverlay from "./components/LoadingOverlay.vue";
import store from "./store";

const route = useRoute()

// 初始化store状态
onMounted(() => {
  store.init()
})

const isLoginPage = computed(() => route.path === '/login')
const isHomeOrLogin = computed(() => route.path === '/' || route.path === '/login')
const isLoggedIn = computed(() => store.isLoggedIn)
const isLoading = computed(() => store.isLoading)
</script>

<style scoped>
.app-container {
  min-height: 100vh;
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: linear-gradient(180deg, #a8c7ba 0%, #d1e7dd 100%);
  padding: 12px;
  position: relative;
  overflow: hidden;
}

.app-container.gradient-bg {
  background: linear-gradient(180deg, #a8c7ba 0%, #d1e7dd 100%);
}

.app-wrapper {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 12px;
  position: relative;
  z-index: 1;
}

.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
  overflow-y: auto;
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
