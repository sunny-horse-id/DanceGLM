import { createRouter, createWebHistory } from 'vue-router'

//导入Vue组件
import TestVue from "@/views/TestVue.vue";
import IndexVue from "@/views/IndexVue.vue";

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      children: [
        {
          path: '/test',
          component: TestVue,
        },
        {
          path: '',
          component: IndexVue,
        }
      ],
    },
  ]
})

export default router