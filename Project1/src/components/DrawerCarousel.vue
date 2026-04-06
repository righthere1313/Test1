<template>
  <div id="main" @click="handleClick">
    <div id="click-section">
      <div id="drawerboxes">
        <div class="drawerbox" :class="{ active: chosenSlideNumber === 1 }">
          <button class="drawer-btn" :class="{ active: chosenSlideNumber === 1 }" @click.stop="slideTo(1)">智能对话<span class="drawer-head">1</span></button>
        </div>
        <div class="drawerbox" :class="{ active: chosenSlideNumber === 2 }">
          <button class="drawer-btn" :class="{ active: chosenSlideNumber === 2 }" @click.stop="slideTo(2)">知识库管理<span class="drawer-head">2</span></button>
        </div>
        <div class="drawerbox" :class="{ active: chosenSlideNumber === 3 }">
          <button class="drawer-btn" :class="{ active: chosenSlideNumber === 3 }" @click.stop="slideTo(3)">课件预览生成<span class="drawer-head">3</span></button>
        </div>
        <div class="drawerbox" :class="{ active: chosenSlideNumber === 4 }">
          <button class="drawer-btn" :class="{ active: chosenSlideNumber === 4 }" @click.stop="slideTo(4)">历史管理<span class="drawer-head">4</span></button>
        </div>
      </div>
    </div>
    <div id="slide-section">
      <div id="slide-bar">
        <div id="bar" :style="{ transform: `translateY(${barOffset}%)` }"></div>
      </div>
      <div id="card-section">
        <div id="card1" class="card" :style="{ transform: `translateY(${offset}%)` }">
          <div class="card-small-title">智能对话</div>
          <div class="card-title-box">
            <img src="/images/介绍截图/对话页.png" alt="对话页">
          </div>
          <div class="card-content">与智能体自然对话，根据教学需求调整个性化内容，为您提供专业的建议和方案。</div>
        </div>
        <div id="card2" class="card" :style="{ transform: `translateY(${offset}%)` }">
          <div class="card-small-title">知识库管理</div>
          <div class="card-title-box">
            <img src="/images/介绍截图/资料管理.png" alt="知识库管理">
          </div>
          <div class="card-content">上传并管理各类教学资料，构建专属资料库，支持多种检索方式，提升备课效率。</div>
        </div>
        <div id="card3" class="card" :style="{ transform: `translateY(${offset}%)` }">
          <div class="card-small-title">课件预览生成</div>
          <div class="card-title-box">
            <img src="/images/介绍截图/历史生成.png" alt="课件预览生成">
          </div>
          <div class="card-content">生成美观实用的教学课件，包含完整教学结构，支持实时预览和编辑。</div>
        </div>
        <div id="card4" class="card" :style="{ transform: `translateY(${offset}%)` }">
          <div class="card-small-title">历史管理</div>
          <div class="card-title-box">
            <img src="/images/介绍截图/历史生成.png" alt="历史管理">
          </div>
          <div class="card-content">历史课件按年份排序便于查看管理，可查找配套资料，记录工作细节。</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'

const emit = defineEmits(['nextPage'])

const chosenSlideNumber = ref(1)
const offset = ref(0)
const barOffset = ref(0)

const slideTo = (slideNumber) => {
  let previousSlideNumber = chosenSlideNumber.value
  chosenSlideNumber.value = slideNumber
  offset.value += (chosenSlideNumber.value - previousSlideNumber) * (-100)
  barOffset.value += (chosenSlideNumber.value - previousSlideNumber) * (100)
}

const handleClick = () => {
  if (chosenSlideNumber.value < 4) {
    slideTo(chosenSlideNumber.value + 1)
  } else {
    emit('nextPage')
  }
}

onMounted(() => {
  chosenSlideNumber.value = 1
  offset.value = 0
  barOffset.value = 0
})
</script>

<style scoped>
* {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

#main {
  height: 100%;
  width: 100%;
  display: flex;
  justify-content: center;
  align-items: center;
}

#click-section {
  width: 30%;
  height: 100%;
  padding: 20px 0;
  position: relative;
}

#drawerboxes {
  margin-left: 10%;
  width: 100%;
  height: 100%;
  position: relative;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  justify-content: space-evenly;
}

.drawerbox {
  height: calc(100% / 5.5);
  width: 70%;
  position: relative;
  z-index: 100;
  transform: translateX(-70%);
  transition: transform .5s ease-in-out;
}

.drawerbox.active {
  transform: translateX(0);
}

.drawer-btn {
  width: 100%;
  height: 100%;
  border-radius: 4px;
  font: 700 24px '';
  background: rgba(255, 255, 255, 0.3);
  border: none;
  transition: background-color .5s ease-in-out;
  color: #16493900;
  cursor: pointer;
}

.drawer-btn.active {
  background-color: #8ab4aa;
  color: #424242;
}

.drawer-head {
  position: absolute;
  color: #ffffff;
  font-size: 80px;
  font-weight: 700;
  right: -30px;
  top: calc(50% - 55px);
}

#slide-section {
  position: relative;
  height: 100%;
  width: 65%;
  display: flex;
  justify-content: center;
  padding: 0 40px;
  background: linear-gradient(to right,
      rgba(255, 255, 255, .7),
      rgba(255, 255, 255, .5),
      rgba(255, 255, 255, .3));
  backdrop-filter: blur(11px);
  border-radius: 4px;
}

#slide-bar {
  position: absolute;
  top: 10%;
  left: 40px;
  height: 80%;
  width: 1px;
  background-color: rgb(223, 223, 223);
}

#bar {
  position: absolute;
  height: calc(100% / 4);
  width: 5px;
  top: 0;
  left: -1.2px;
  background-color: #8ab4aa;
  transition: transform .5s ease-in-out;
}

#card-section {
  height: 100%;
  width: 80%;
  overflow: hidden;
}

.card {
  display: flex;
  flex-direction: column;
  height: 100%;
  width: 100%;
  padding: 10% 0;
  color: white;
  font-size: 30px;
  transition: transform .5s ease-in-out;
}

.card-small-title {
  font-size: 30px;
  font-weight: 600;
  padding-bottom: min(5%, 10px);
  color: #46736d;
}

.card-title-box {
  width: 100%;
  aspect-ratio: 16/9;
  border-radius: 12px;
  overflow: hidden;
  margin-bottom: 20px;
  border: 2px solid #8ab4aa;
  background: #f8f9fa;
}

.card-title-box img {
  width: 100%;
  height: 100%;
  object-fit: contain;
  background: white;
}

.card-content {
  font-size: 18px;
  font-weight: 400;
  color: #46736d;
  line-height: 1.6;
}
</style>
