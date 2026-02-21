<template>
  <q-page class="q-pa-md">
    <!-- ADD: Loading Overlay -->
    <q-inner-loading :showing="loading">
      <q-spinner-gears size="50px" color="primary" />
    </q-inner-loading>

    <div class="row q-col-gutter-md">
      <!-- Header -->
      <div class="col-12">
        <div class="row items-center">
          <div class="col">
            <h4 class="q-my-none">Dashboard</h4>
            <p class="text-grey-7 q-my-xs">
              <!-- CHANGE: Show selected date instead of generic text -->
              Welcome back! Here's your business overview for
              <span class="text-weight-bold">{{ formattedDate }}</span>
            </p>
          </div>
          <div class="col-auto">
            <!-- CHANGE: Add event listener for date changes -->
            <q-date
              v-model="selectedDate"
              minimal
              @update:model-value="onDateChange"
              mask="YYYY-MM-DD"
            />
          </div>
        </div>
      </div>

      <!-- Stats Cards -->
      <div class="col-12 col-md-3">
        <q-card class="bg-primary text-white">
          <q-card-section>
            <!-- CHANGE: Dynamic date label -->
            <div class="text-h6">{{ dateLabel }} Revenue</div>
            <div class="text-h4 q-mt-md">₵{{ formatNumber(dashboardData.revenue) }}</div>
            <div class="row items-center q-mt-sm">
              <q-icon name="trending_up" size="sm" class="q-mr-xs" />
              <span>+12% from yesterday</span>
            </div>
          </q-card-section>
        </q-card>
      </div>

      <div class="col-12 col-md-3">
        <q-card class="bg-red text-white">
          <q-card-section>
            <div class="text-h6">{{ dateLabel }} Expenses</div>
            <div class="text-h4 q-mt-md">₵{{ formatNumber(dashboardData.expenses) }}</div>
            <div class="row items-center q-mt-sm">
              <q-icon name="trending_down" size="sm" class="q-mr-xs" />
              <span>-5% from yesterday</span>
            </div>
          </q-card-section>
        </q-card>
      </div>

      <div class="col-12 col-md-3">
        <q-card class="bg-green text-white">
          <q-card-section>
            <div class="text-h6">Net Profit</div>
            <div class="text-h4 q-mt-md">₵{{ formatNumber(dashboardData.profit) }}</div>
            <div class="row items-center q-mt-sm">
              <q-icon name="trending_up" size="sm" class="q-mr-xs" />
              <span>{{ dashboardData.profit_margin }}% margin</span>
            </div>
          </q-card-section>
        </q-card>
      </div>

      <div class="col-12 col-md-3">
        <q-card class="bg-purple text-white">
          <q-card-section>
            <div class="text-h6">Total Sales</div>
            <div class="text-h4 q-mt-md">{{ formatNumber(dashboardData.total_sales) }}</div>
            <div class="row items-center q-mt-sm">
              <q-icon name="shopping_cart" size="sm" class="q-mr-xs" />
              <span>{{ formatNumber(dashboardData.total_expenses) }} expenses logged</span>
            </div>
          </q-card-section>
        </q-card>
      </div>

      <!-- Charts Row -->
      <div class="col-12 col-md-8">
        <q-card>
          <q-card-section>
            <div class="text-h6">Sales Overview</div>
          </q-card-section>
          <q-card-section class="q-pt-none" style="height: 300px; padding: 0">
            <div id="sales-chart" ref="salesChartRef" style="height: 100%; width: 100%"></div>
          </q-card-section>
        </q-card>
      </div>

      <div class="col-12 col-md-4">
        <q-card>
          <q-card-section>
            <div class="text-h6">Inventory Status</div>
          </q-card-section>
          <q-card-section class="q-pt-none">
            <q-list bordered separator>
              <q-item v-for="item in inventoryStatus" :key="item.egg_type">
                <q-item-section avatar>
                  <q-icon :name="item.icon" :color="item.color" />
                </q-item-section>
                <q-item-section>
                  <q-item-label>{{ item.egg_type }}</q-item-label>
                  <q-item-label caption>{{ item.available }} crates available</q-item-label>
                </q-item-section>
                <q-item-section side>
                  <q-badge :color="item.badgeColor" :label="item.alert || ''" />
                </q-item-section>
              </q-item>
            </q-list>
          </q-card-section>
        </q-card>
      </div>

      <!-- Recent Sales -->
      <div class="col-12">
        <q-card>
          <q-card-section>
            <div class="text-h6">Recent Sales</div>
          </q-card-section>
          <q-card-section class="q-pt-none">
            <div class="text-center text-grey">
              <q-icon name="history" size="48px" />
              <p class="q-mt-md">Recent sales will appear here</p>
            </div>
          </q-card-section>
        </q-card>
      </div>
    </div>
  </q-page>
</template>

<script>
import { ref, onMounted, onUnmounted, watch, computed } from 'vue'
import { useQuasar } from 'quasar'
import ApexCharts from 'apexcharts'
import { api } from 'boot/axios'

export default {
  name: 'DashboardPage',

  setup() {
    const $q = useQuasar()
    const salesChartRef = ref(null)
    let salesChart = null
    const loading = ref(false)

    // ==================== DATE HANDLING ====================
    const selectedDate = ref(new Date().toISOString().split('T')[0])

    // Computed: Display date in readable format (e.g., "Monday, February 16, 2026")
    const formattedDate = computed(() => {
      const date = new Date(selectedDate.value + 'T00:00:00')
      return date.toLocaleDateString('en-US', {
        weekday: 'long',
        year: 'numeric',
        month: 'long',
        day: 'numeric',
      })
    })

    // Computed: Short label for cards ("Today's" or date)
    const dateLabel = computed(() => {
      const today = new Date().toISOString().split('T')[0]
      return selectedDate.value === today ? "Today's" : formattedDate.value.split(',')[0] + "'s"
    })

    // Handle date change from picker
    const onDateChange = () => {
      console.log('📅 Date changed to:', selectedDate.value)
      loadDashboardData()
      renderSalesChart() // Optional: refresh chart for new date range
    }

    // Watch for programmatic date changes
    watch(selectedDate, () => {
      loadDashboardData()
    })

    // ==================== HELPER FUNCTIONS ====================
    const formatNumber = (value) => {
      if (value === null || value === undefined) return '0.00'
      return Number(value).toLocaleString('en-US', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
      })
    }

    // ==================== DASHBOARD DATA ====================
    const dashboardData = ref({
      revenue: 0,
      expenses: 0,
      profit: 0,
      profit_margin: 0,
      total_sales: 0,
      total_expenses: 0,
    })

    const loadDashboardData = async () => {
      loading.value = true
      try {
        console.log('🔍 Fetching dashboard data for:', selectedDate.value)
        const response = await api.get('/reports/dashboard-summary/', {
          params: { date: selectedDate.value },
        })
        dashboardData.value = response.data
        console.log('✅ Dashboard data loaded:', response.data)
      } catch (error) {
        console.error('❌ Error loading dashboard data:', error)
        $q.notify({
          type: 'negative',
          message: 'Failed to load dashboard data',
          caption: error.response?.data?.detail || 'Please try again',
          icon: 'error',
        })
      } finally {
        loading.value = false
      }
    }

    // ==================== INVENTORY STATUS ====================
    const inventoryStatus = ref([
      { egg_type: 'Broken', available: 0, icon: 'egg', color: 'grey', badgeColor: 'grey' },
      { egg_type: 'Small', available: 0, icon: 'egg', color: 'blue', badgeColor: 'blue' },
      { egg_type: 'Medium', available: 0, icon: 'egg', color: 'orange', badgeColor: 'orange' },
      { egg_type: 'Big', available: 0, icon: 'egg', color: 'green', badgeColor: 'green' },
    ])

    const loadInventoryStatus = async () => {
      try {
        const response = await api.get('/reports/inventory-status/')
        const data = response.data

        inventoryStatus.value = [
          {
            egg_type: 'Broken',
            available: data.broken_available,
            icon: 'egg',
            color: data.broken_available === 0 ? 'grey' : 'grey',
            badgeColor:
              data.broken_available === 0 ? 'red' : data.broken_available < 5 ? 'orange' : 'grey',
            alert:
              data.broken_available === 0
                ? 'Out of stock'
                : data.broken_available < 5
                  ? 'Low stock'
                  : '',
          },
          {
            egg_type: 'Small',
            available: data.small_available,
            icon: 'egg',
            color: data.small_available === 0 ? 'grey' : 'blue',
            badgeColor:
              data.small_available === 0 ? 'red' : data.small_available < 10 ? 'orange' : 'blue',
            alert:
              data.small_available === 0
                ? 'Out of stock'
                : data.small_available < 10
                  ? 'Low stock'
                  : '',
          },
          {
            egg_type: 'Medium',
            available: data.medium_available,
            icon: 'egg',
            color: data.medium_available === 0 ? 'grey' : 'orange',
            badgeColor:
              data.medium_available === 0 ? 'red' : data.medium_available < 10 ? 'orange' : 'green',
            alert:
              data.medium_available === 0
                ? 'Out of stock'
                : data.medium_available < 10
                  ? 'Low stock'
                  : '',
          },
          {
            egg_type: 'Big',
            available: data.big_available,
            icon: 'egg',
            color: data.big_available === 0 ? 'grey' : 'green',
            badgeColor:
              data.big_available === 0 ? 'red' : data.big_available < 10 ? 'orange' : 'green',
            alert:
              data.big_available === 0
                ? 'Out of stock'
                : data.big_available < 10
                  ? 'Low stock'
                  : '',
          },
        ]
      } catch (error) {
        console.error('❌ Error loading inventory status:', error)
        $q.notify({
          type: 'warning',
          message: 'Could not load inventory status',
          icon: 'warning',
        })
      }
    }

    // ==================== SALES CHART ====================
    const renderSalesChart = async () => {
      if (salesChart) salesChart.destroy()

      let chartData = {
        categories: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
        values: [45, 32, 55, 48, 60, 52, 65],
      }

      try {
        const response = await api.get('/reports/sales-trend/', {
          params: {
            days: 7,
            end_date: selectedDate.value, // ← Pass selected date for context
          },
        })
        chartData = {
          categories: response.data.categories.map((dateStr) => {
            const d = new Date(dateStr)
            return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
          }),
          values: response.data.values.map((val) => parseFloat(val) || 0),
        }
      } catch (error) {
        console.error('⚠️ Chart using mock data (API error):', error)
      }

      const options = {
        chart: {
          type: 'bar',
          height: 300,
          toolbar: { show: false },
        },
        series: [{ name: 'Revenue', data: chartData.values }],
        xaxis: { categories: chartData.categories },
        colors: ['#26a69a'],
        plotOptions: {
          bar: {
            borderRadius: 4,
            dataLabels: { position: 'top' },
          },
        },
        dataLabels: { enabled: false },
        title: {
          text: 'Daily Revenue (Last 7 Days)',
          align: 'left',
          style: { fontSize: '16px', fontWeight: 600 },
        },
        tooltip: {
          y: {
            formatter: (value) => {
              const num = Number(value)
              return isNaN(num) ? '₵0.00' : `₵${num.toFixed(2)}`
            },
          },
        },
        yaxis: {
          labels: {
            formatter: (value) => `₵${value}`,
          },
        },
      }

      salesChart = new ApexCharts(salesChartRef.value, options)
      salesChart.render()
    }

    // ==================== LIFECYCLE ====================
    onMounted(() => {
      console.log('📊 Dashboard mounted')
      loadDashboardData()
      loadInventoryStatus()
      if (salesChartRef.value) renderSalesChart()
    })

    onUnmounted(() => {
      if (salesChart) salesChart.destroy()
    })

    return {
      selectedDate,
      formattedDate,
      dateLabel,
      dashboardData,
      inventoryStatus,
      salesChartRef,
      loading,
      onDateChange,
      formatNumber,
    }
  },
}
</script>
