<template>
  <q-page class="q-pa-md">
    <div class="row q-col-gutter-md">
      <!-- Header -->
      <div class="col-12">
        <div class="row items-center justify-between">
          <div>
            <h4 class="q-my-none">Reports & Analytics</h4>
            <p class="text-grey-7 q-my-xs">Generate detailed business reports and insights</p>
          </div>
          <div class="col-auto">
            <q-btn-dropdown
              color="primary"
              icon="download"
              label="Export Report"
              split
              @click="exportReport"
            >
              <q-list>
                <q-item clickable v-close-popup @click="exportPDF">
                  <q-item-section avatar>
                    <q-icon name="picture_as_pdf" />
                  </q-item-section>
                  <q-item-section>
                    <q-item-label>Export as PDF</q-item-label>
                  </q-item-section>
                </q-item>
                <q-item clickable v-close-popup @click="exportExcel">
                  <q-item-section avatar>
                    <q-icon name="table_chart" />
                  </q-item-section>
                  <q-item-section>
                    <q-item-label>Export as Excel</q-item-label>
                  </q-item-section>
                </q-item>
                <q-item clickable v-close-popup @click="exportCSV">
                  <q-item-section avatar>
                    <q-icon name="description" />
                  </q-item-section>
                  <q-item-section>
                    <q-item-label>Export as CSV</q-item-label>
                  </q-item-section>
                </q-item>
              </q-list>
            </q-btn-dropdown>
          </div>
        </div>
      </div>

      <!-- Date Range Selector -->
      <div class="col-12">
        <q-card>
          <q-card-section>
            <div class="row items-center q-col-gutter-md">
              <div class="col-12 col-md-4">
                <q-select
                  v-model="selectedReportType"
                  :options="reportTypeOptions"
                  label="Report Type"
                  outlined
                  emit-value
                  map-options
                />
              </div>
              <div class="col-12 col-md-3">
                <q-input v-model="dateRange.start" type="date" label="Start Date" outlined />
              </div>
              <div class="col-12 col-md-3">
                <q-input v-model="dateRange.end" type="date" label="End Date" outlined />
              </div>
              <div class="col-12 col-md-2">
                <q-btn
                  color="primary"
                  label="Generate"
                  icon="refresh"
                  @click="generateReport"
                  class="full-width"
                />
              </div>
            </div>
          </q-card-section>
        </q-card>
      </div>

      <!-- Profit & Loss Summary -->
      <div class="col-12" v-if="showPnLReport">
        <q-card>
          <q-card-section>
            <div class="text-h6">Profit & Loss Statement</div>
            <div class="text-caption text-grey">
              Period: {{ dateRange.start }} to {{ dateRange.end }}
            </div>
          </q-card-section>
          <q-card-section class="q-pt-none">
            <div class="row q-col-gutter-md">
              <div class="col-12 col-md-6">
                <div class="text-subtitle1 q-mb-sm">Revenue</div>
                <q-separator class="q-mb-md" />

                <div class="row items-center q-mb-sm">
                  <div class="col">Retail Sales</div>
                  <div class="col-auto text-weight-medium">
                    ₵{{ plData.revenue_breakdown?.retail || 0 }}
                  </div>
                </div>

                <div class="row items-center q-mb-sm">
                  <div class="col">Wholesale Sales</div>
                  <div class="col-auto text-weight-medium">
                    ₵{{ plData.revenue_breakdown?.wholesale || 0 }}
                  </div>
                </div>

                <q-separator class="q-my-md" />

                <div class="row items-center">
                  <div class="col text-h6">Total Revenue</div>
                  <div class="col-auto text-h6 text-primary">₵{{ plData.total_revenue || 0 }}</div>
                </div>
              </div>

              <div class="col-12 col-md-6">
                <div class="text-subtitle1 q-mb-sm">Expenses</div>
                <q-separator class="q-mb-md" />

                <div
                  v-for="expense in plData.expense_breakdown || []"
                  :key="expense.category__name"
                  class="row items-center q-mb-sm"
                >
                  <div class="col">{{ expense.category__name }}</div>
                  <div class="col-auto text-weight-medium">₵{{ expense.total }}</div>
                </div>

                <q-separator class="q-my-md" />

                <div class="row items-center">
                  <div class="col text-h6">Total Expenses</div>
                  <div class="col-auto text-h6 text-red">₵{{ plData.total_expenses || 0 }}</div>
                </div>
              </div>

              <div class="col-12">
                <q-separator class="q-my-md" />

                <div class="row items-center">
                  <div class="col">
                    <div class="text-h5">Net Profit</div>
                    <div class="text-caption text-grey">
                      Profit Margin: {{ plData.profit_margin || 0 }}%
                    </div>
                  </div>
                  <div class="col-auto">
                    <div
                      class="text-h4"
                      :class="plData.net_profit >= 0 ? 'text-green' : 'text-red'"
                    >
                      ₵{{ plData.net_profit || 0 }}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </q-card-section>
        </q-card>
      </div>

      <!-- Sales Report -->
      <div class="col-12" v-if="showSalesReport">
        <q-card>
          <q-card-section>
            <div class="text-h6">Sales Report</div>
            <div class="text-caption text-grey">
              Period: {{ dateRange.start }} to {{ dateRange.end }}
            </div>
          </q-card-section>
          <q-card-section class="q-pt-none">
            <div class="row q-col-gutter-md">
              <div class="col-12 col-md-3">
                <q-card class="bg-primary text-white">
                  <q-card-section>
                    <div class="text-h6">Total Sales</div>
                    <div class="text-h3 q-mt-md">{{ salesReportData.total_sales || 0 }}</div>
                    <div class="row items-center q-mt-sm">
                      <q-icon name="shopping_cart" size="sm" class="q-mr-xs" />
                      <span>transactions</span>
                    </div>
                  </q-card-section>
                </q-card>
              </div>

              <div class="col-12 col-md-3">
                <q-card class="bg-green text-white">
                  <q-card-section>
                    <div class="text-h6">Total Revenue</div>
                    <div class="text-h3 q-mt-md">₵{{ salesReportData.total_revenue || 0 }}</div>
                    <div class="row items-center q-mt-sm">
                      <q-icon name="attach_money" size="sm" class="q-mr-xs" />
                      <span>earned</span>
                    </div>
                  </q-card-section>
                </q-card>
              </div>

              <div class="col-12 col-md-3">
                <q-card>
                  <q-card-section>
                    <div class="text-h6">Retail Sales</div>
                    <div class="text-h3 q-mt-md">{{ salesReportData.retail_count || 0 }}</div>
                    <div class="row items-center q-mt-sm">
                      <q-icon name="store" size="sm" class="q-mr-xs" />
                      <span>₵{{ salesReportData.retail_revenue || 0 }}</span>
                    </div>
                  </q-card-section>
                </q-card>
              </div>

              <div class="col-12 col-md-3">
                <q-card>
                  <q-card-section>
                    <div class="text-h6">Wholesale Sales</div>
                    <div class="text-h3 q-mt-md">{{ salesReportData.wholesale_count || 0 }}</div>
                    <div class="row items-center q-mt-sm">
                      <q-icon name="business" size="sm" class="q-mr-xs" />
                      <span>₵{{ salesReportData.wholesale_revenue || 0 }}</span>
                    </div>
                  </q-card-section>
                </q-card>
              </div>

              <!-- Quantity Breakdown -->
              <div class="col-12">
                <q-card>
                  <q-card-section>
                    <div class="text-h6">Quantity Breakdown</div>
                  </q-card-section>
                  <q-card-section class="q-pt-none">
                    <div class="row q-col-gutter-md">
                      <div class="col-12 col-md-3">
                        <div class="text-center">
                          <q-badge color="grey" label="Broken" class="q-mb-sm" />
                          <div class="text-h4">{{ salesReportData.quantities?.broken || 0 }}</div>
                          <div class="text-caption">crates</div>
                        </div>
                      </div>
                      <div class="col-12 col-md-3">
                        <div class="text-center">
                          <q-badge color="blue" label="Small" class="q-mb-sm" />
                          <div class="text-h4">{{ salesReportData.quantities?.small || 0 }}</div>
                          <div class="text-caption">crates</div>
                        </div>
                      </div>
                      <div class="col-12 col-md-3">
                        <div class="text-center">
                          <q-badge color="orange" label="Medium" class="q-mb-sm" />
                          <div class="text-h4">{{ salesReportData.quantities?.medium || 0 }}</div>
                          <div class="text-caption">crates</div>
                        </div>
                      </div>
                      <div class="col-12 col-md-3">
                        <div class="text-center">
                          <q-badge color="green" label="Big" class="q-mb-sm" />
                          <div class="text-h4">{{ salesReportData.quantities?.big || 0 }}</div>
                          <div class="text-caption">crates</div>
                        </div>
                      </div>
                    </div>
                  </q-card-section>
                </q-card>
              </div>
            </div>
          </q-card-section>
        </q-card>
      </div>

      <!-- Expense Report -->
      <div class="col-12" v-if="showExpenseReport">
        <q-card>
          <q-card-section>
            <div class="text-h6">Expense Report</div>
            <div class="text-caption text-grey">
              Period: {{ dateRange.start }} to {{ dateRange.end }}
            </div>
          </q-card-section>
          <q-card-section class="q-pt-none">
            <div class="row q-col-gutter-md">
              <div class="col-12 col-md-4">
                <q-card class="bg-red text-white">
                  <q-card-section>
                    <div class="text-h6">Total Expenses</div>
                    <div class="text-h3 q-mt-md">{{ expenseReportData.total_expenses || 0 }}</div>
                    <div class="row items-center q-mt-sm">
                      <q-icon name="receipt_long" size="sm" class="q-mr-xs" />
                      <span>records</span>
                    </div>
                  </q-card-section>
                </q-card>
              </div>

              <div class="col-12 col-md-4">
                <q-card class="bg-purple text-white">
                  <q-card-section>
                    <div class="text-h6">Total Amount</div>
                    <div class="text-h3 q-mt-md">₵{{ expenseReportData.total_amount || 0 }}</div>
                    <div class="row items-center q-mt-sm">
                      <q-icon name="attach_money" size="sm" class="q-mr-xs" />
                      <span>spent</span>
                    </div>
                  </q-card-section>
                </q-card>
              </div>

              <div class="col-12 col-md-4">
                <q-card>
                  <q-card-section>
                    <div class="text-h6">Avg. Expense</div>
                    <div class="text-h3 q-mt-md">
                      ₵{{
                        (
                          expenseReportData.total_amount / expenseReportData.total_expenses || 0
                        ).toFixed(2)
                      }}
                    </div>
                    <div class="row items-center q-mt-sm">
                      <q-icon name="trending_up" size="sm" class="q-mr-xs" />
                      <span>per transaction</span>
                    </div>
                  </q-card-section>
                </q-card>
              </div>

              <!-- Category Breakdown -->
              <div class="col-12">
                <q-card>
                  <q-card-section>
                    <div class="text-h6">Category Breakdown</div>
                  </q-card-section>
                  <q-card-section class="q-pt-none">
                    <div v-if="expenseReportData.category_breakdown?.length > 0">
                      <div
                        v-for="category in expenseReportData.category_breakdown"
                        :key="category.category__name"
                        class="q-mb-md"
                      >
                        <div class="row items-center q-mb-xs">
                          <div class="col">
                            <q-badge :color="getCategoryColor(category.category__name)">
                              {{ category.category__name }}
                            </q-badge>
                          </div>
                          <div class="col-auto text-weight-medium">
                            ₵{{ category.total }} ({{ category.count }} items)
                          </div>
                        </div>
                        <q-linear-progress
                          :value="category.total / maxExpenseCategory"
                          color="primary"
                          class="q-mt-xs"
                        />
                      </div>
                    </div>
                    <div v-else class="text-center text-grey q-py-md">
                      <q-icon name="info" size="24px" class="q-mb-sm" />
                      <p>No expense data for selected period</p>
                    </div>
                  </q-card-section>
                </q-card>
              </div>
            </div>
          </q-card-section>
        </q-card>
      </div>

      <!-- Loading State -->
      <div class="col-12" v-if="loadingReport">
        <q-card>
          <q-card-section class="text-center">
            <q-spinner size="48px" color="primary" class="q-mb-md" />
            <p>Generating report...</p>
          </q-card-section>
        </q-card>
      </div>
    </div>
  </q-page>
</template>

<script>
import { ref, computed, onMounted } from 'vue'
import { api } from 'boot/axios'
import { useQuasar } from 'quasar'

export default {
  name: 'ReportsPage',

  setup() {
    const $q = useQuasar()
    const loadingReport = ref(false)
    const selectedReportType = ref('profit_loss')
    const dateRange = ref({
      start: new Date(new Date().setDate(new Date().getDate() - 30)).toISOString().split('T')[0],
      end: new Date().toISOString().split('T')[0],
    })

    const plData = ref({})
    const salesReportData = ref({})
    const expenseReportData = ref({})

    const reportTypeOptions = [
      { label: 'Profit & Loss', value: 'profit_loss' },
      { label: 'Sales Report', value: 'sales' },
      { label: 'Expense Report', value: 'expense' },
    ]

    const showPnLReport = computed(() => selectedReportType.value === 'profit_loss')
    const showSalesReport = computed(() => selectedReportType.value === 'sales')
    const showExpenseReport = computed(() => selectedReportType.value === 'expense')

    const maxExpenseCategory = computed(() => {
      if (!expenseReportData.value.category_breakdown) return 100
      const amounts = expenseReportData.value.category_breakdown.map((c) => c.total)
      return Math.max(...amounts) * 1.1 || 100
    })

    const getCategoryColor = (categoryName) => {
      const colors = {
        Feed: 'brown',
        Labor: 'blue',
        Utilities: 'orange',
        Maintenance: 'purple',
        Transportation: 'teal',
        Veterinary: 'red',
        Packaging: 'green',
        Miscellaneous: 'grey',
      }
      return colors[categoryName] || 'grey'
    }

    const generateReport = async () => {
      loadingReport.value = true

      try {
        switch (selectedReportType.value) {
          case 'profit_loss':
            await loadProfitLossReport()
            break
          case 'sales':
            await loadSalesReport()
            break
          case 'expense':
            await loadExpenseReport()
            break
        }
      } catch (error) {
        console.error('Error generating report:', error)
        $q.notify({
          color: 'negative',
          message: 'Failed to generate report',
          icon: 'warning',
        })
      } finally {
        loadingReport.value = false
      }
    }

    const loadProfitLossReport = async () => {
      try {
        const response = await api.get('/reports/profit-loss/', {
          params: {
            start_date: dateRange.value.start,
            end_date: dateRange.value.end,
          },
        })
        plData.value = response.data
      } catch (error) {
        console.error('Error loading P&L report:', error)
        throw error
      }
    }

    const loadSalesReport = async () => {
      try {
        const response = await api.get('/reports/sales-report/', {
          params: {
            start_date: dateRange.value.start,
            end_date: dateRange.value.end,
          },
        })
        salesReportData.value = response.data
      } catch (error) {
        console.error('Error loading sales report:', error)
        throw error
      }
    }

    const loadExpenseReport = async () => {
      try {
        const response = await api.get('/reports/expense-report/', {
          params: {
            start_date: dateRange.value.start,
            end_date: dateRange.value.end,
          },
        })
        expenseReportData.value = response.data
      } catch (error) {
        console.error('Error loading expense report:', error)
        throw error
      }
    }

    const exportReport = () => {
      $q.notify({
        color: 'info',
        message: 'Select export format from dropdown',
        icon: 'info',
      })
    }

    const exportPDF = () => {
      $q.notify({
        color: 'warning',
        message: 'PDF export feature coming soon',
        icon: 'construction',
      })
    }

    const exportExcel = () => {
      $q.notify({
        color: 'warning',
        message: 'Excel export feature coming soon',
        icon: 'construction',
      })
    }

    const exportCSV = () => {
      $q.notify({
        color: 'warning',
        message: 'CSV export feature coming soon',
        icon: 'construction',
      })
    }

    onMounted(() => {
      // Load default report (last 30 days)
      generateReport()
    })

    return {
      loadingReport,
      selectedReportType,
      dateRange,
      reportTypeOptions,
      showPnLReport,
      showSalesReport,
      showExpenseReport,
      plData,
      salesReportData,
      expenseReportData,
      maxExpenseCategory,
      getCategoryColor,
      generateReport,
      exportReport,
      exportPDF,
      exportExcel,
      exportCSV,
    }
  },
}
</script>
