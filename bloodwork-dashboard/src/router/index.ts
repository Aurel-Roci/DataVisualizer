import { createRouter, createWebHistory } from 'vue-router'
import DashboardView from '../views/DashboardView.vue'

// pages that are in the nav but not built yet
const comingSoon = (title: string) => ({
  component: () => import('../views/MessageView.vue'),
  props: { title, text: 'This page is coming soon.' },
})

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    { path: '/', component: DashboardView },
    { path: '/history', ...comingSoon('History') },
    { path: '/reference', ...comingSoon('Reference Ranges') },
    { path: '/settings', ...comingSoon('Settings') },
    {
      path: '/:pathMatch(.*)*',
      component: () => import('../views/MessageView.vue'),
      props: { title: 'Page not found', text: "That address doesn't exist." },
    },
  ],
})

export default router
