import { createRouter, createWebHistory } from 'vue-router'
import ChatPage from '../components/ChatPage.vue'
import KnowledgeBase from '../components/KnowledgeBase.vue'
import CoursewarePreview from '../components/CoursewarePreview.vue'

const routes = [
  {
    path: '/',
    redirect: '/chat'
  },
  {
    path: '/chat',
    name: 'Chat',
    component: ChatPage
  },
  {
    path: '/knowledge',
    name: 'Knowledge',
    component: KnowledgeBase
  },
  {
    path: '/preview',
    name: 'Preview',
    component: CoursewarePreview
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
