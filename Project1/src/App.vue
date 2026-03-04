<template>
  <div class="app-container">
    <div class="app-wrapper">
      <Nav />
      <main class="main-content">
        <router-view />
      </main>
    </div>
  </div>
</template>

<script setup>
import Nav from './components/Nav.vue'
</script>

<style scoped>
.app-container {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background: #d1e7dd;
  padding: 20px;
}

.app-wrapper {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.main-content {
  flex: 1;
  overflow: hidden;
}
</style>
