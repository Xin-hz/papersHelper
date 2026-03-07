import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  { path: '/', name: 'Home', component: () => import('../views/Home.vue'), meta: { title: '首页' } },
  { path: '/paper', name: 'Paper', component: () => import('../views/Paper.vue'), meta: { title: '论文' } },
  { path: '/lesson', name: 'Lesson', component: () => import('../views/Lesson.vue'), meta: { title: '教案' } },
  { path: '/case', name: 'Case', component: () => import('../views/Case.vue'), meta: { title: '教学案例' } },
  { path: '/topic', name: 'TopicApplication', component: () => import('../views/TopicApplication.vue'), meta: { title: '课题申报' } },
  { path: '/knowledge', name: 'Knowledge', component: () => import('../views/Knowledge.vue'), meta: { title: '知识库' } },
]

const router = createRouter({ history: createWebHistory(), routes })
router.afterEach((to) => { document.title = to.meta.title ? `${to.meta.title} - 幼儿园教师 AI 论文助手` : '幼儿园教师 AI 论文助手' })
export default router
