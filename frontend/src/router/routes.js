const routes = [
  {
    path: '/',
    component: () => import('layouts/MainLayout.vue'),
    children: [
      {
        path: '',
        name: 'Dashboard',
        component: () => import('pages/DashboardPage.vue'),
      },
      {
        path: 'dashboard',
        component: () => import('pages/DashboardPage.vue'),
      },
      {
        path: 'inventory',
        name: 'Inventory',
        component: () => import('pages/InventoryPage.vue'),
      },
      {
        path: 'sales',
        name: 'Sales',
        component: () => import('pages/SalesPage.vue'),
      },
      {
        path: 'expenses',
        name: 'Expenses',
        component: () => import('pages/ExpensesPage.vue'),
      },
      {
        path: 'customers',
        name: 'Customers',
        component: () => import('pages/CustomersPage.vue'),
      },
      {
        path: 'reports',
        name: 'Reports',
        component: () => import('pages/ReportsPage.vue'),
      },
    ],
  },

  // Always leave this as last one
  {
    path: '/:catchAll(.*)*',
    component: () => import('pages/ErrorNotFound.vue'),
  },
]

export default routes
