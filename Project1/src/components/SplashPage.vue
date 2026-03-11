<template>
  <div class="splash-page">
    <div class="splash-content">
      <div class="logo-placeholder"></div>
      <p class="slogan">让教学更简单，让课堂更精彩</p>
      <p class="english">From prep to class, we make it brilliant</p>
    </div>
  </div>
</template>

<script setup>
</script>

<style scoped>
.splash-page {
  width: 100%;
  height: 100%;
  display: flex;
  justify-content: center;
  align-items: center;
  background: transparent;
}

.splash-content {
  text-align: center;
  color: #46736d;
}

.logo-placeholder {
  width: 120px;
  height: 120px;
  margin: 0 auto 16px;
  border-radius: 24px;
  background: linear-gradient(135deg, #dbfff2 0%, #cce4db 100%);
  display: flex;
  justify-content: center;
  align-items: center;
  font-size: 48px;
}

.slogan {
  font-size: 40px;
  color: #46736d;
  font-weight: 600;
}

.english {
  font-size: 38px;
  color: #6b9a93;
  font-weight: 400;
}
</style>
