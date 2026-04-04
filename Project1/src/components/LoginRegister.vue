<template>
  <div class="login-page">
    <div class="box">
      <div class="pre-box" :class="{ 'switched': isSwitched }">
        <h1 class="dis">
          <span class="row">
            <div class="text">WELCOME!</div>
          </span>
          <span class="row">
            <div class="text">WELCOME!</div>
          </span>
          <span class="row">
            <div class="text">WELCOME!</div>
          </span>
          <span class="row">
            <div class="text">WELCOME!</div>
          </span>
          <span class="row">
            <div class="text">WELCOME!</div>
          </span>
          <span class="row">
            <div class="text">WELCOME!</div>
          </span>
        </h1>
        <div class="project-title">
          AI互动式教学智能体
        </div>
        <div class="slogan">
          让教学更简单，让课堂更精彩
        </div>
      </div>
      <div class="register-form">
        <div class="title-box">
          <h1>注册</h1>
        </div>
        <div class="input-box">
          <input v-model="registerData.username" type="text" placeholder="用户名">
          <input v-model="registerData.password" type="password" placeholder="密码">
          <input v-model="registerData.confirmPassword" type="password" placeholder="确认密码">
        </div>
        <div class="btn-box">
          <button @click="handleRegister">注册</button>
          <p @click="toggleForm">已有账号?去登录</p>
        </div>
      </div>
      <div class="login-form">
        <div class="title-box">
          <h1>登录</h1>
        </div>
        <div class="input-box">
          <input v-model="loginData.username" type="text" placeholder="用户名">
          <input v-model="loginData.password" type="password" placeholder="密码">
        </div>
        <div class="btn-box">
          <button @click="handleLogin" :disabled="isLoading">
            {{ isLoading ? '登录中...' : '登录' }}
          </button>
          <p @click="toggleForm">没有账号?去注册</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import store from '../store'

const router = useRouter()
const isSwitched = ref(false)

const loginData = ref({
  username: '',
  password: ''
})

const registerData = ref({
  username: '',
  password: '',
  confirmPassword: ''
})

const toggleForm = () => {
  isSwitched.value = !isSwitched.value
}

const isLoading = ref(false)

const handleLogin = async () => {
  if (!loginData.value.username || !loginData.value.password) {
    alert('请填写完整信息')
    return
  }
  
  isLoading.value = true
  try {
    const result = await store.login(loginData.value.username, loginData.value.password)
    
    if (result.success) {
      store.isLoading = true
      setTimeout(() => {
        store.isLoading = false
        router.push('/chat')
      }, 1000)
    } else {
      alert(result.error || '登录失败')
      isLoading.value = false
    }
  } catch (error) {
    alert('登录失败：' + (error.message || '未知错误'))
    isLoading.value = false
  }
}

const handleRegister = async () => {
  if (!registerData.value.username || !registerData.value.password) {
    alert('请填写完整信息')
    return
  }
  if (registerData.value.password !== registerData.value.confirmPassword) {
    alert('两次密码输入不一致')
    return
  }
  
  isLoading.value = true
  try {
    const result = await store.register(
      registerData.value.username,
      registerData.value.password
    )
    
    if (result.success) {
      alert('注册成功！请登录')
      registerData.value = {
        username: '',
        password: '',
        confirmPassword: ''
      }
      toggleForm()
    } else {
      alert(result.error || '注册失败')
    }
  } catch (error) {
    alert('注册失败：' + (error.message || '未知错误'))
  } finally {
    isLoading.value = false
  }
}
</script>

<style scoped>
.login-page {
  width: 100%;
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  z-index: 1;
}

.box {
  width: 800px;
  height: 500px;
  display: flex;
  position: relative;
  z-index: 2;
  border-radius: 4px;
  border: 1px solid rgba(255, 255, 255, 0.6);
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.3);
  overflow: hidden;
}

.pre-box {
  width: 50%;
  height: 100%;
  position: absolute;
  left: 0;
  top: 0;
  z-index: 99;
  border-radius: 2px;
  background-color: #312f2f;
  box-shadow: 2px 1px 19px rgba(0, 0, 0, 0.1);
  transition: 0.5s ease-in-out;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
}

.pre-box.switched {
  transform: translateX(100%);
  background-color: #1a1a1a;
}

.dis {
  position: relative;
  font-size: 48px;
  font-family: 'Staatliches', sans-serif;
  color: #fff;
  margin-bottom: 30px;
}

.row {
  display: block;
  top: 0;
  left: 0;
  user-select: none;
  -webkit-user-select: none;
  -moz-user-select: none;
}

.row:nth-child(1) {
  clip-path: polygon(0% 75%, 100% 75%, 100% 100%, 0% 100%);
}

.row:nth-child(2) {
  clip-path: polygon(0% 50%, 100% 50%, 100% 75.5%, 0% 75.5%);
  position: absolute;
}

.row:nth-child(3) {
  clip-path: polygon(0% 25%, 100% 25%, 100% 50.5%, 0% 50.5%);
  position: absolute;
}

.row:nth-child(4) {
  clip-path: polygon(0% 0%, 100% -10%, 100% 35.5%, 0% 25.5%);
  position: absolute;
}

.row:nth-child(5) {
  clip-path: polygon(0% -25%, 100% -45%, 100% -9.5%, 0% 0.5%);
  position: absolute;
}

.row:nth-child(6) {
  clip-path: polygon(0% -50%, 100% -85%, 100% -44.4%, 0% -24.5%);
  position: absolute;
}

.dis .text {
  display: block;
  transform-origin: bottom left;
  animation: in 2.5s ease-in-out infinite alternate;
}

.dis .row:nth-child(1) .text {
  transform: translateY(-0.1em);
}

.dis .row:nth-child(2) .text {
  transform: translateY(-0.3em) scaleY(1.1);
}

.dis .row:nth-child(3) .text {
  transform: translateY(-0.5em) scaleY(1.2) rotate(-1deg);
}

.dis .row:nth-child(4) .text {
  transform: translateY(-0.7em) scaleY(1.3) rotate(-2deg);
}

.dis .row:nth-child(5) .text {
  transform: translateY(-0.9em) scaleY(1.4) rotate(-3deg);
}

.dis .row:nth-child(6) .text {
  transform: translateY(-1.1em) scaleY(1.5) rotate(-4deg);
}

@keyframes in {
  60%,
  100% {
    transform: translateX(0em);
  }
}

.project-title {
  color: #d1e7dd;
  font-size: 20px;
  font-weight: 600;
  text-align: center;
  user-select: none;
  margin-bottom: 8px;
}

.slogan {
  color: #67aaa0;
  font-size: 14px;
  font-weight: 500;
  text-align: center;
  user-select: none;
}

.login-form,
.register-form {
  flex: 1;
  height: 100%;
  background: #ffffff;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.title-box {
  margin-bottom: 20px;
}

.title-box h1 {
  text-align: center;
  color: #1a1a1a;
  user-select: none;
  letter-spacing: 5px;
  font-size: 36px;
}

.input-box {
  display: flex;
  flex-direction: column;
  align-items: center;
}

input {
  width: 60%;
  height: 44px;
  margin-bottom: 20px;
  text-indent: 16px;
  border: 2px solid #a3cfbb;
  background-color: rgba(255, 255, 255, 0.8);
  border-radius: 22px;
  backdrop-filter: blur(10px);
  font-size: 15px;
  color: #0f5132;
  outline: none;
  transition: border-color 0.2s ease;
}

input:focus {
  border-color: #1a1a1a;
}

input:focus::placeholder {
  opacity: 0;
}

input::placeholder {
  color: #6c757d;
}

.btn-box {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 16px;
  margin-top: 20px;
}

button {
  width: 120px;
  height: 32px;
  line-height: 32px;
  border: none;
  border-radius: 16px;
  background-color: #312f2f;
  color: white;
  font-size: 15px;
  font-weight: 500;
  cursor: pointer;
  transition: opacity 0.2s ease;
}


.btn-box p {
  height: 30px;
  line-height: 30px;
  user-select: none;
  font-size: 14px;
  color: #1a1a1a;
  cursor: pointer;
  transition: border-bottom 0.2s ease;
}

.btn-box p:hover {
  border-bottom: 1px solid #1a1a1a;
}
</style>
