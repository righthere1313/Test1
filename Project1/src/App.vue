<template>
  <div class="app-container" :class="{ 'gradient-bg': !isHomeOrLogin }">
    <BubbleBackground v-if="isHomeOrLogin" />
    <div class="app-wrapper">
      <Nav v-if="!isLoginPage && isLoggedIn" />
      <main class="main-content">
        <router-view />
      </main>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import Nav from "./components/Nav.vue";
import BubbleBackground from "./components/BubbleBackground.vue";
import store from "./store";

const route = useRoute()
const isLoginPage = computed(() => route.path === '/login')
const isHomeOrLogin = computed(() => route.path === '/' || route.path === '/login')
const isLoggedIn = computed(() => store.isLoggedIn)
</script>

<style scoped>
.app-container {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background: linear-gradient(180deg, #a8c7ba 0%, #d1e7dd 100%);
  padding: 16px;
  position: relative;
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
}
</style>
