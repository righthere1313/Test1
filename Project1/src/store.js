import { reactive, watch } from 'vue'

const loadFromStorage = () => {
  try {
    const saved = localStorage.getItem('appState')
    if (saved) {
      return JSON.parse(saved)
    }
  } catch (e) {
    console.error('Failed to load from localStorage:', e)
  }
  return null
}

const savedState = loadFromStorage()

const store = reactive({
  isLoggedIn: savedState?.isLoggedIn || false,
  user: savedState?.user || {
    username: '老师',
    avatar: null,
    teacherName: '',
    subject: '',
    schoolName: '',
    password: ''
  },
  chatHistory: [
    { role: 'user', content: '我想设计一节关于勾股定理的课' },
    { role: 'ai', content: '好的，请问这节课的教学目标是什么？' },
    { role: 'user', content: '理解并掌握勾股定理，能够应用于实际问题' },
    { role: 'ai', content: '明白了，我来为您生成课件...' }
  ],
  addMessage(message) {
    this.chatHistory.push(message)
  },
  updateUser(userData) {
    Object.assign(this.user, userData)
  },
  logout() {
    this.isLoggedIn = false
    this.user = {
      username: '老师',
      avatar: null,
      teacherName: '',
      subject: '',
      schoolName: '',
      password: ''
    }
    localStorage.removeItem('appState')
  }
})

watch(
  () => ({ isLoggedIn: store.isLoggedIn, user: store.user }),
  (newState) => {
    localStorage.setItem('appState', JSON.stringify(newState))
  },
  { deep: true }
)

export default store
