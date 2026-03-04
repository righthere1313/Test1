import { reactive } from 'vue'

const store = reactive({
  user: {
    username: '张老师',
    avatar: null
  },
  userInfo: {
    subject: '',
    grade: '',
    students: ''
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
  updateUserInfo(info) {
    Object.assign(this.userInfo, info)
  }
})

export default store
