<template>
  <q-page class="q-pa-md">
    <div class="row q-col-gutter-md">
      <!-- Header -->
      <div class="col-12">
        <div class="row items-center justify-between">
          <div>
            <h4 class="q-my-none">Expenses Management</h4>
            <p class="text-grey-7 q-my-xs">Track business costs and recurring expenses</p>
          </div>
          <div class="col-auto">
            <q-btn
              color="primary"
              icon="add"
              label="New Expense"
              @click="showExpenseDialog = true"
            />
          </div>
        </div>
      </div>

      <!-- Expenses Summary Cards -->
      <div class="col-12 col-md-4">
        <q-card class="bg-red text-white">
          <q-card-section>
            <div class="text-h6">Today's Expenses</div>
            <div class="text-h3 q-mt-md">₵{{ expenseSummary.total_amount }}</div>
            <div class="row items-center q-mt-sm">
              <q-icon name="receipt_long" size="sm" class="q-mr-xs" />
              <span>{{ expenseSummary.total_expenses }} expenses logged</span>
            </div>
          </q-card-section>
        </q-card>
      </div>

      <div class="col-12 col-md-4">
        <q-card>
          <q-card-section>
            <div class="text-h6">This Month</div>
            <div class="text-h3 q-mt-md">₵{{ monthlyExpenses }}</div>
            <div class="row items-center q-mt-sm">
              <q-icon name="calendar_month" size="sm" class="q-mr-xs" />
              <span>{{ monthlyCount }} expenses</span>
            </div>
          </q-card-section>
        </q-card>
      </div>

      <div class="col-12 col-md-4">
        <q-card class="bg-purple text-white">
          <q-card-section>
            <div class="text-h6">Recurring Expenses</div>
            <div class="text-h3 q-mt-md">{{ recurringCount }}</div>
            <div class="row items-center q-mt-sm">
              <q-icon name="repeat" size="sm" class="q-mr-xs" />
              <span>Active subscriptions</span>
            </div>
          </q-card-section>
        </q-card>
      </div>

      <!-- Category Breakdown Chart -->
      <div class="col-12 col-md-8">
        <q-card>
          <q-card-section>
            <div class="text-h6">Category Breakdown</div>
          </q-card-section>
          <q-card-section class="q-pt-none">
            <div v-if="categoryBreakdown.length > 0">
              <div
                v-for="category in categoryBreakdown"
                :key="category.category__name"
                class="q-mb-md"
              >
                <div class="row items-center q-mb-xs">
                  <div class="col">{{ category.category__name }}</div>
                  <div class="col-auto text-weight-medium">₵{{ category.total }}</div>
                </div>
                <q-linear-progress
                  :value="category.total / maxCategoryAmount"
                  color="primary"
                  class="q-mt-xs"
                />
              </div>
            </div>
            <div v-else class="text-center text-grey q-py-md">
              <q-icon name="info" size="24px" class="q-mb-sm" />
              <p>No expenses recorded yet</p>
            </div>
          </q-card-section>
        </q-card>
      </div>

      <!-- Recent Expenses Table -->
      <div class="col-12">
        <q-card>
          <q-card-section>
            <div class="text-h6">Recent Expenses</div>
          </q-card-section>
          <q-card-section class="q-pt-none">
            <q-table
              :rows="expensesList"
              :columns="expensesColumns"
              row-key="id"
              :loading="loadingExpenses"
              :pagination="{ rowsPerPage: 10 }"
              :filter="searchExpenses"
            >
              <template v-slot:top-right>
                <q-input
                  v-model="searchExpenses"
                  dense
                  outlined
                  placeholder="Search..."
                  class="q-mb-xs"
                >
                  <template v-slot:prepend>
                    <q-icon name="search" />
                  </template>
                </q-input>
              </template>
            </q-table>
          </q-card-section>
        </q-card>
      </div>
    </div>

    <!-- New Expense Dialog -->
    <q-dialog v-model="showExpenseDialog" persistent>
      <q-card style="min-width: 600px">
        <q-card-section>
          <div class="text-h6">Record New Expense</div>
        </q-card-section>

        <q-card-section class="q-pt-none">
          <q-form @submit="submitExpense">
            <!-- Date -->
            <q-input
              v-model="expenseForm.date"
              type="date"
              label="Date"
              outlined
              lazy-rules
              :rules="[(val) => !!val || 'Date is required']"
            />

            <!-- Category -->
            <q-select
              v-model="expenseForm.category"
              :options="categoryOptions"
              label="Category"
              outlined
              emit-value
              map-options
              lazy-rules
              :rules="[(val) => !!val || 'Category is required']"
            />

            <!-- Description -->
            <q-input
              v-model="expenseForm.description"
              type="text"
              label="Description"
              outlined
              lazy-rules
              :rules="[(val) => !!val || 'Description is required']"
            />

            <!-- Amount -->
            <q-input
              v-model.number="expenseForm.amount"
              type="number"
              label="Amount (₵)"
              outlined
              lazy-rules
              :rules="[
                (val) => !!val || 'Amount is required',
                (val) => val > 0 || 'Amount must be greater than 0',
              ]"
            />

            <!-- Payment Method -->
            <q-select
              v-model="expenseForm.payment_method"
              :options="paymentMethodOptions"
              label="Payment Method"
              outlined
              emit-value
              map-options
              lazy-rules
            />

            <!-- Receipt File (Optional) -->
            <q-file
              v-model="expenseForm.receipt_file"
              label="Receipt (Optional)"
              outlined
              accept=".jpg,.jpeg,.png,.pdf"
              class="q-mt-md"
            >
              <template v-slot:prepend>
                <q-icon name="attach_file" />
              </template>
            </q-file>

            <!-- Recurring Toggle -->
            <q-toggle
              v-model="expenseForm.is_recurring"
              label="Recurring Expense"
              class="q-mt-md"
            />

            <!-- Recurring Settings (Conditional) -->
            <div v-if="expenseForm.is_recurring" class="q-mt-md">
              <q-select
                v-model="expenseForm.recurrence_pattern"
                :options="recurrenceOptions"
                label="Recurrence Pattern"
                outlined
                emit-value
                map-options
                lazy-rules
                :rules="[(val) => !!val || 'Pattern is required for recurring expenses']"
              />

              <q-input
                v-model="expenseForm.recurrence_end_date"
                type="date"
                label="End Date (Optional)"
                outlined
                class="q-mt-md"
              />
            </div>

            <!-- Notes -->
            <q-input
              v-model="expenseForm.notes"
              type="textarea"
              label="Notes"
              outlined
              class="q-mt-md"
            />

            <!-- Buttons -->
            <div class="row q-mt-md">
              <q-space />
              <q-btn
                label="Cancel"
                color="grey"
                flat
                @click="showExpenseDialog = false"
                class="q-mr-sm"
              />
              <q-btn label="Save Expense" type="submit" color="primary" />
            </div>
          </q-form>
        </q-card-section>
      </q-card>
    </q-dialog>
  </q-page>
</template>
<script>
import { ref, computed, onMounted, watch } from 'vue'
import { api } from 'boot/axios'
import { useQuasar } from 'quasar'

export default {
  name: 'ExpensesPage',

  setup() {
    const $q = useQuasar()
    const showExpenseDialog = ref(false)
    const loadingExpenses = ref(false)
    const searchExpenses = ref('')
    const expensesList = ref([])
    const expenseCategories = ref([])
    const expenseSummary = ref({
      total_amount: 0,
      total_expenses: 0,
      category_breakdown: [],
    })

    const expensesColumns = [
      { name: 'date', label: 'Date', field: 'date', align: 'left', sortable: true },
      {
        name: 'category',
        label: 'Category',
        field: 'category_name',
        align: 'left',
        sortable: true,
      },
      { name: 'description', label: 'Description', field: 'description', align: 'left' },
      {
        name: 'amount',
        label: 'Amount',
        field: 'amount',
        align: 'right',
        format: (val) => `₵${val}`,
        sortable: true,
      },
      { name: 'payment_method', label: 'Payment', field: 'payment_method', align: 'center' },
      {
        name: 'recurring',
        label: 'Recurring',
        field: 'is_recurring',
        align: 'center',
        format: (val) => (val ? '✓' : ''),
      },
    ]

    const paymentMethodOptions = [
      { label: 'Cash', value: 'cash' },
      { label: 'Bank Transfer', value: 'bank_transfer' },
      { label: 'Mobile Money', value: 'mobile_money' },
      { label: 'Credit', value: 'credit' },
      { label: 'Other', value: 'other' },
    ]

    const recurrenceOptions = [
      { label: 'Daily', value: 'daily' },
      { label: 'Weekly', value: 'weekly' },
      { label: 'Monthly', value: 'monthly' },
      { label: 'Yearly', value: 'yearly' },
    ]

    const categoryOptions = computed(() => {
      return expenseCategories.value.map((category) => ({
        label: category.name,
        value: category.id,
      }))
    })

    const categoryBreakdown = computed(() => {
      return expenseSummary.value.category_breakdown || []
    })

    const maxCategoryAmount = computed(() => {
      if (categoryBreakdown.value.length === 0) return 100
      return Math.max(...categoryBreakdown.value.map((c) => c.total)) * 1.1
    })

    const monthlyExpenses = computed(() => {
      const monthlyTotal = expensesList.value
        .filter((exp) => {
          const expDate = new Date(exp.date)
          const today = new Date()
          return (
            expDate.getMonth() === today.getMonth() && expDate.getFullYear() === today.getFullYear()
          )
        })
        .reduce((sum, exp) => sum + parseFloat(exp.amount), 0)
      return monthlyTotal.toFixed(2)
    })

    const monthlyCount = computed(() => {
      const today = new Date()
      return expensesList.value.filter((exp) => {
        const expDate = new Date(exp.date)
        return (
          expDate.getMonth() === today.getMonth() && expDate.getFullYear() === today.getFullYear()
        )
      }).length
    })

    const recurringCount = computed(() => {
      return expensesList.value.filter((exp) => exp.is_recurring).length
    })

    const expenseForm = ref({
      date: new Date().toISOString().split('T')[0],
      category: null,
      description: '',
      amount: null,
      payment_method: 'cash',
      receipt_file: null,
      is_recurring: false,
      recurrence_pattern: null,
      recurrence_end_date: '',
      notes: '',
    })

    // DELETED: loadExpenseSummary function - no longer needed

    const loadExpensesList = async () => {
      loadingExpenses.value = true
      try {
        const response = await api.get('/expenses/expenses/')
        expensesList.value = response.data
      } catch (error) {
        console.error('Error loading expenses:', error)
        $q.notify({
          color: 'negative',
          message: 'Failed to load expenses',
          icon: 'warning',
        })
      } finally {
        loadingExpenses.value = false
      }
    }

    const loadExpenseCategories = async () => {
      try {
        const response = await api.get('/expenses/expense-categories/?is_active=true')
        expenseCategories.value = response.data
      } catch (error) {
        console.error('Error loading expense categories:', error)
      }
    }

    const submitExpense = async () => {
      try {
        const formData = new FormData()

        // Append all form fields
        Object.keys(expenseForm.value).forEach((key) => {
          const value = expenseForm.value[key]
          if (value !== null && value !== '') {
            formData.append(key, value)
          }
        })

        await api.post('/expenses/expenses/', formData, {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        })

        $q.notify({
          color: 'positive',
          message: 'Expense recorded successfully!',
          icon: 'check',
        })

        showExpenseDialog.value = false
        expenseForm.value = {
          date: new Date().toISOString().split('T')[0],
          category: null,
          description: '',
          amount: null,
          payment_method: 'cash',
          receipt_file: null,
          is_recurring: false,
          recurrence_pattern: null,
          recurrence_end_date: '',
          notes: '',
        }

        loadExpensesList() // Only need to reload the list
      } catch (error) {
        console.error('Error recording expense:', error)
        const errorMessage =
          error.response?.data?.detail ||
          error.response?.data?.non_field_errors?.[0] ||
          'Failed to record expense'
        $q.notify({
          color: 'negative',
          message: errorMessage,
          icon: 'warning',
        })
      }
    }

    // ADDED: Watcher to calculate today's summary from expensesList
    watch(
      expensesList,
      () => {
        const today = new Date().toISOString().split('T')[0]

        const todayExpenses = expensesList.value.filter((exp) => exp.date === today)

        const totalAmount = todayExpenses.reduce((sum, exp) => sum + parseFloat(exp.amount), 0)

        // Calculate category breakdown
        const categoryBreakdown = {}
        todayExpenses.forEach((exp) => {
          const category = exp.category_name || 'Uncategorized'
          categoryBreakdown[category] = (categoryBreakdown[category] || 0) + parseFloat(exp.amount)
        })

        expenseSummary.value = {
          total_amount: totalAmount.toFixed(2),
          total_expenses: todayExpenses.length,
          category_breakdown: Object.entries(categoryBreakdown).map(([name, total]) => ({
            category__name: name,
            total: total.toFixed(2),
          })),
        }
      },
      { immediate: true },
    )

    onMounted(() => {
      loadExpensesList()
      loadExpenseCategories()
    })

    return {
      showExpenseDialog,
      loadingExpenses,
      searchExpenses,
      expensesList,
      expenseSummary,
      expenseCategories,
      expensesColumns,
      paymentMethodOptions,
      recurrenceOptions,
      categoryOptions,
      categoryBreakdown,
      maxCategoryAmount,
      monthlyExpenses,
      monthlyCount,
      recurringCount,
      expenseForm,
      submitExpense,
    }
  },
}
</script>
