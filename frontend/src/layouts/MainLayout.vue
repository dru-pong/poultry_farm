<template>
  <q-layout view="hHh lpR fFf">
    <!-- Header -->
    <q-header elevated class="bg-primary text-white">
      <q-toolbar>
        <q-btn flat dense round icon="menu" aria-label="Menu" @click="toggleLeftDrawer" />

        <q-toolbar-title> AmaSika Farms </q-toolbar-title>

        <q-space />

        <div class="row items-center no-wrap">
          <q-btn flat round dense icon="notifications" class="q-mr-sm">
            <q-badge color="red" floating> 2 </q-badge>
          </q-btn>

          <q-btn flat round dense icon="account_circle" @click="showUserMenu = true" />
        </div>

        <q-menu v-model="showUserMenu" anchor="bottom end" self="top end">
          <q-list style="min-width: 100px">
            <q-item clickable v-close-popup @click="logout">
              <q-item-section avatar>
                <q-icon name="logout" />
              </q-item-section>
              <q-item-section>Logout</q-item-section>
            </q-item>
          </q-list>
        </q-menu>
      </q-toolbar>
    </q-header>

    <!-- Left Drawer (Navigation) -->
    <q-drawer v-model="leftDrawerOpen" show-if-above bordered class="bg-grey-2">
      <q-list>
        <q-item-label header> Navigation </q-item-label>

        <EssentialLink v-for="link in essentialLinks" :key="link.title" v-bind="link" />
      </q-list>
    </q-drawer>

    <!-- Page Content -->
    <q-page-container>
      <router-view />
    </q-page-container>
  </q-layout>
</template>

<script>
import { ref } from 'vue'
import EssentialLink from 'components/EssentialLink.vue'

const linksList = [
  {
    title: 'Dashboard',
    caption: 'Overview & Analytics',
    icon: 'dashboard',
    link: '/dashboard',
  },
  {
    title: 'Inventory',
    caption: 'Egg Stock Management',
    icon: 'inventory_2',
    link: '/inventory',
  },
  {
    title: 'Sales',
    caption: 'Record & Track Sales',
    icon: 'shopping_cart',
    link: '/sales',
  },
  {
    title: 'Expenses',
    caption: 'Track Business Costs',
    icon: 'receipt_long',
    link: '/expenses',
  },
  {
    title: 'Customers',
    caption: 'Wholesale Customer Management',
    icon: 'people',
    link: '/customers',
  },
  {
    title: 'Reports',
    caption: 'Analytics & Insights',
    icon: 'analytics',
    link: '/reports',
  },
]

export default {
  name: 'MainLayout',

  components: {
    EssentialLink,
  },

  setup() {
    const leftDrawerOpen = ref(false)
    const showUserMenu = ref(false)

    return {
      essentialLinks: linksList,
      leftDrawerOpen,
      showUserMenu,
      toggleLeftDrawer() {
        leftDrawerOpen.value = !leftDrawerOpen.value
      },
      logout() {
        // Redirect to Django admin login
        window.location.href = '/admin/logout/'
      },
    }
  },
}
</script>
