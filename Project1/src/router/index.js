import { createRouter, createWebHistory } from 'vue-router'
import ChatPage from '../components/ChatPage.vue'
import KnowledgeBase from '../components/KnowledgeBase.vue'
import CoursewarePreview from '../components/CoursewarePreview.vue'
import LoginRegister from '../components/LoginRegister.vue'
import Profile from '../components/Profile.vue'
import HomePage from '../components/HomePage.vue'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: HomePage
  },
  {
    path: '/introduction',
    name: 'Introduction',
    component: HomePage
  },
  {
    path: '/login',
    name: 'Login',
    component: LoginRegister
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
  },
  {
    path: '/profile',
    name: 'Profile',
    component: Profile
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
