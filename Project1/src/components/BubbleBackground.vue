<template>
  <div class="bubble-background">
    <span v-for="bubble in bubbles" :key="bubble.id" :style="bubble.style" class="bubble"></span>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'

const bubbles = ref([])
let bubbleId = 0
let intervalId = null

const createBubble = () => {
  const r = Math.random() * 40 + 60
  const left = Math.random() * window.innerWidth
  const id = bubbleId++
  
  bubbles.value.push({
    id,
    style: {
      width: r + 'px',
      height: r + 'px',
      left: left + 'px',
      animationDelay: Math.random() * 0.2 + 's'
    }
  })

  setTimeout(() => {
    const index = bubbles.value.findIndex(b => b.id === id)
    if (index > -1) {
      bubbles.value.splice(index, 1)
    }
  }, 15000)
}

onMounted(() => {
  intervalId = setInterval(createBubble, 500)
})

onUnmounted(() => {
  if (intervalId) {
    clearInterval(intervalId)
  }
})
</script>

<style scoped>
.bubble-background {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: 0;
  pointer-events: none;
  overflow: hidden;
}

.bubble {
  position: absolute;
  z-index: 0;
  bottom: 0;
  border-radius: 50%;
  background: radial-gradient(circle at center, #000000 0%, #1a1a1a 20%, #333333 40%, #555555 60%, #999999 80%, #cccccc 100%);
  box-shadow: inset 0 0 20px rgba(0, 0, 0, 0.8),
              inset 10px 0 30px rgba(0, 0, 0, 0.4),
              0 0 40px rgba(0, 0, 0, 0.1);
  animation: myMove 15s ease-in-out forwards;
  opacity: 0;
  filter: blur(3px);
}

@keyframes myMove {
  0% {
    transform: translateY(0%);
    opacity: 0;
  }
  15% {
    opacity: 0.6;
  }
  85% {
    opacity: 0.6;
  }
  100% {
    transform: translateY(-100vh) scale(1.3);
    opacity: 0;
  }
}
</style>
