<template>
  <div class="send-message-wrap">
    <div class="wrap" :style="{ transform: `scale(0.85) translateY(70px)`, transformOrigin: 'center center' }">
      <h1>JOIN THE EXPERIENCE</h1>
      <div class="form-wrap" :class="{ hide: isSubmitted, expanded: isAlwaysExpanded || isHovered || isFocused }" @mouseenter="isHovered = true" @mouseleave="isHovered = false">
        <div class="letter">
          <div class="letter-content">
            <p class="greeting">亲爱的老师，</p>
            <p class="line">让AI教学智能体陪您一起</p>
            <p class="line">启便捷教学之门</p>
            <p class="line">享高效工作之趣</p>
            <p class="signoff">此致</p>
            <p class="signature">五金松鼠团队</p>
          </div>
          
          <button v-if="!hideStartButton" @click="handleSubmit" class="cta-btn">
            开始体验
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'

const props = defineProps({
  autoExpand: {
    type: Boolean,
    default: false
  },
  hideStartButton: {
    type: Boolean,
    default: false
  }
})

const isHovered = ref(false)
const isFocused = ref(false)
const isSubmitted = ref(false)
const isAlwaysExpanded = ref(false)

const emit = defineEmits(['start'])

const handleSubmit = () => {
  emit('start')
}

watch(() => props.autoExpand, (newVal) => {
  if (newVal) {
    isAlwaysExpanded.value = true
  }
})
</script>

<style scoped>
.send-message-wrap {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}

.wrap {
  width: 530px;
  margin: 0 auto;
}

h1 {
  margin-top: 20px;
  text-align: center;
  font-size: 35px;
  font-family: tahoma;
  color: black;
}

.form-wrap {
  overflow: hidden;
  height: 447px;
  position: relative;
  top: 0px;
  transition: all 1s ease-in-out 0.3s;
}

.form-wrap.expanded {
  height: 777px;
  top: -200px;
}

.form-wrap:before {
  content: "";
  position: absolute;
  bottom: 128px;
  left: 0px;
  background: url('/images/messagesend/before.png');
  width: 530px;
  height: 317px;
}

.form-wrap:after {
  content: "";
  position: absolute;
  bottom: 0px;
  left: 0;
  background: url('/images/messagesend/after.png');
  width: 530px;
  height: 259px;
}

.form-wrap.hide:after,
.form-wrap.hide:before {
  display: none;
}

.letter {
  background: url('/images/messagesend/letter_bg.png');
  position: relative;
  top: 250px;
  overflow: hidden;
  height: 200px;
  width: 400px;
  margin: 0px auto;
  padding: 0;
  border: 1px solid white;
  border-right: 3px;
  transition: all 1s ease-in-out 0.3s;
  box-sizing: border-box;
}

.form-wrap.expanded .letter {
  height: 530px;
}

.letter-content {
  padding: 25px 40px;
  background-image: repeating-linear-gradient(
    transparent,
    transparent 44px,
    #e0e0e0 44px,
    #e0e0e0 45px
  );
  background-size: 100% 45px;
  background-position: 0 10px;
}

p.greeting {
  font-family: '楷体', 'KaiTi', serif;
  font-size: 22px;
  color: #333;
  margin: 0;
  line-height: 45px;
  height: 45px;
}

p.line {
  font-family: '楷体', 'KaiTi', serif;
  font-size: 20px;
  color: #444;
  margin: 0;
  line-height: 45px;
  height: 45px;
  text-align: center;
}

p.signoff {
  font-family: '楷体', 'KaiTi', serif;
  font-size: 20px;
  color: #333;
  margin: 0;
  line-height: 45px;
  height: 45px;
  text-align: right;
}

p.signature {
  font-family: '楷体', 'KaiTi', serif;
  font-size: 20px;
  color: #333;
  margin: 0;
  line-height: 45px;
  height: 45px;
  text-align: right;
}

.cta-btn {
  position: relative;
  font-family: tahoma;
  font-size: 22px;
  color: gray;
  width: 300px;
  text-align: center;
  opacity: 0;
  background: none;
  cursor: pointer;
  border-radius: 3px;
  transition: all 0.7s ease-in-out 0s;
  border: none;
  margin-left: 50px;
}
.cta-btn:hover {
  color: #000000;
}

.form-wrap.expanded .cta-btn {
  z-index: 1;
  opacity: 1;
  transition: opacity 0.5s ease-in-out 1.3s;
}
</style>
