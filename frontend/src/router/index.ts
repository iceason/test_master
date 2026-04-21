import { createRouter, createWebHashHistory } from 'vue-router'
import { getToken } from '@/utils/axios'
import DefaultLayout from '@/layouts/DefaultLayout.vue'
import NProgress from 'nprogress'
import 'nprogress/nprogress.css'

const routes = [
  {
    path: '/login',
    component: () => import('@/views/login/index.vue'),
    meta: { title: 'Login' }
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('@/views/register/index.vue'),
    meta: { title: 'Register' }
  },
  {
    path: '/:pathMatch(.*)*',
    component: () => import('@/views/error/NotFound.vue'),
    meta: { title: '404' }
  },
  {
    path: '/',
    component: DefaultLayout,
    redirect: '/dashboard',
    meta: { requiresAuth: true },
    children: [
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('@/views/dashboard/index.vue'),
        meta: { title: 'Dashboard' }
      },
      {
        path: 'generation',
        name: 'Generation',
        component: () => import('@/views/generation/index.vue'),
        meta: { title: 'Test Generation' }
      },
      {
        path: 'projects',
        name: 'Projects',
        component: () => import('@/views/project/index.vue'),
        meta: { title: 'Projects' }
      },
      {
        path: 'interface',
        name: 'Interfaces',
        component: () => import('@/views/interface/index.vue'),
        meta: { title: 'Interfaces' }
      },
      {
        path: 'testcase',
        name: 'TestCases',
        component: () => import('@/views/testcase/index.vue'),
        meta: { title: 'Test Cases' }
      },
      {
        path: 'testing/agents',
        name: 'ExecutorAgents',
        component: () => import('@/views/testing/agents/index.vue'),
        meta: { title: 'Executor Agents' }
      },
      {
        path: 'testing/plans',
        name: 'BuildPlans',
        component: () => import('@/views/testing/plans/index.vue'),
        meta: { title: 'Build Plans' }
      },
      {
        path: 'testing/plans/:id',
        name: 'BuildPlanDetail',
        component: () => import('@/views/testing/plans/detail.vue'),
        meta: { title: 'Build Plan Detail' }
      },
      {
        path: 'testing/executions',
        name: 'ExecutionRecords',
        component: () => import('@/views/testing/executions/index.vue'),
        meta: { title: 'Execution Records' }
      },
      {
        path: 'execution',
        name: 'Execution',
        component: () => import('@/views/execution/index.vue'),
        meta: { title: 'Test Execution' }
      },
      {
        path: 'profile',
        name: 'Profile',
        component: () => import('@/views/profile/index.vue'),
        meta: { title: 'Profile' }
      },
      {
        path: 'settings/email-templates',
        name: 'EmailTemplates',
        component: () => import('@/views/settings/EmailTemplates.vue'),
        meta: { title: 'Email Templates' }
      },
      {
        path: 'settings/environments',
        name: 'Environments',
        component: () => import('@/views/settings/Environments.vue'),
        meta: { title: 'Environments' }
      },
      {
        path: 'settings/dingtalk-groups',
        name: 'DingTalkGroups',
        component: () => import('@/views/settings/DingTalkGroups.vue'),
        meta: { title: 'DingTalk Groups' }
      },
      {
        path: 'settings/dingtalk-templates',
        name: 'DingTalkTemplates',
        component: () => import('@/views/settings/DingTalkTemplates.vue'),
        meta: { title: 'DingTalk Templates' }
      }
    ]
  }
]

const router = createRouter({
  history: createWebHashHistory(),
  routes,
})

router.beforeEach((to, from, next) => {
  NProgress.start()
  const token = getToken()
  
  // 动态设置标题
  const title = to.meta.title as string
  if (title) {
    document.title = `${title} - Test Master`
  } else {
    document.title = 'Test Master'
  }

  if (to.meta.requiresAuth && !token) {
    next('/login')
  } else if (to.path === '/login' && token) {
    next('/')
  } else {
    next()
  }
})

router.afterEach(() => {
  NProgress.done()
})

export default router
