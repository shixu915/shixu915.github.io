import { createRouter, createWebHashHistory } from 'vue-router';
import MainLayout from '../views/MainLayout.vue';

const router = createRouter({
  history: createWebHashHistory(),
  routes: [
    {
      path: '/',
      component: MainLayout,
      redirect: '/tasks',
      children: [
        {
          path: 'tasks',
          name: 'Tasks',
          component: () => import('../views/TaskView.vue'),
          meta: { title: '任务管理' }
        },
        {
          path: 'logs',
          name: 'Logs',
          component: () => import('../views/LogView.vue'),
          meta: { title: '系统日志' }
        },
        {
          path: 'settings',
          name: 'Settings',
          component: () => import('../views/SettingsView.vue'),
          meta: { title: '系统设置' }
        }
      ]
    }
  ]
});

export default router;
