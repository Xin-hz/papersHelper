import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  { path: '/', name: 'Home', component: () => import('../views/Home.vue'), meta: { title: '首页' } },
  { path: '/write', name: 'Write', component: () => import('../views/Write.vue'), meta: { title: '写论文' } },
  { path: '/revise', name: 'Revise', component: () => import('../views/Revise.vue'), meta: { title: '改论文' } },
  { path: '/paper', redirect: '/write' },
  { path: '/daily', name: 'Daily', component: () => import('../views/Daily.vue'), meta: { title: '日常工具' } },
  { path: '/knowledge', name: 'Knowledge', component: () => import('../views/Knowledge.vue'), meta: { title: '知识库' } },
  { path: '/collector', name: 'PaperCollector', component: () => import('../views/Collector.vue'), meta: { title: '论文采集' } },
  { path: '/topics', name: 'TopicLibrary', component: () => import('../views/TopicLibrary.vue'), meta: { title: '选题库' } },
  { path: '/rewrite', name: 'PaperRewrite', component: () => import('../views/PaperRewrite.vue'), meta: { title: '论文降重' } },
  // 原有路由保留为子路由
  { path: '/daily/lesson', name: 'Lesson', component: () => import('../views/Lesson.vue'), meta: { title: '教案' } },
  { path: '/daily/case', name: 'Case', component: () => import('../views/Case.vue'), meta: { title: '教学案例' } },
  { path: '/daily/topic', name: 'TopicApplication', component: () => import('../views/TopicApplication.vue'), meta: { title: '课题申报' } },
  // 404 兜底：未知路径回首页
  { path: '/:pathMatch(.*)*', redirect: '/' },
]

// base 必须与 vite base（/app/）一致，否则挂在 /app/ 下时路由匹配不到任何页面
const router = createRouter({ history: createWebHistory(import.meta.env.BASE_URL), routes })
router.afterEach((to) => { document.title = to.meta.title ? `${to.meta.title} - 幼儿园教师 AI 论文助手` : '幼儿园教师 AI 论文助手' })
export default router
