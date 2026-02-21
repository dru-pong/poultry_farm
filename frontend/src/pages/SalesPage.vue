<template>
  <q-page class="q-pa-md">
    <div class="row q-col-gutter-md">
      <!-- Header -->
      <div class="col-12">
        <div class="row items-center justify-between">
          <div>
            <h4 class="q-my-none">Sales Management</h4>
            <p class="text-grey-7 q-my-xs">Record and track egg sales</p>
          </div>
          <div class="col-auto">
            <q-btn
              color="primary"
              icon="add_shopping_cart"
              label="New Sale"
              @click="showSaleDialog = true"
            />
          </div>
        </div>
      </div>

      <!-- Sales Summary Cards -->
      <div class="col-12 col-md-4">
        <q-card>
          <q-card-section>
            <div class="text-h6">Today's Revenue</div>
            <div class="text-h3 q-mt-md">₵{{ salesSummary.total_revenue }}</div>
            <div class="row items-center q-mt-sm">
              <q-icon name="trending_up" size="sm" class="q-mr-xs" color="green" />
              <span>{{ salesSummary.total_sales }} sales today</span>
            </div>
          </q-card-section>
        </q-card>
      </div>

      <div class="col-12 col-md-4">
        <q-card>
          <q-card-section>
            <div class="text-h6">Retail Sales</div>
            <div class="text-h3 q-mt-md">₵{{ salesSummary.retail_revenue }}</div>
            <div class="row items-center q-mt-sm">
              <q-icon name="store" size="sm" class="q-mr-xs" />
              <span>{{ salesSummary.retail_count }} transactions</span>
            </div>
          </q-card-section>
        </q-card>
      </div>

      <div class="col-12 col-md-4">
        <q-card>
          <q-card-section>
            <div class="text-h6">Wholesale Sales</div>
            <div class="text-h3 q-mt-md">₵{{ salesSummary.wholesale_revenue }}</div>
            <div class="row items-center q-mt-sm">
              <q-icon name="business" size="sm" class="q-mr-xs" />
              <span>{{ salesSummary.wholesale_count }} transactions</span>
            </div>
          </q-card-section>
        </q-card>
      </div>

      <!-- Sales Table -->
      <div class="col-12">
        <q-card>
          <q-card-section>
            <div class="text-h6">Recent Sales</div>
          </q-card-section>
          <q-card-section class="q-pt-none">
            <q-table
              :rows="salesList"
              :columns="salesColumns"
              row-key="id"
              :loading="loadingSales"
              :pagination="{ rowsPerPage: 10 }"
              :filter="searchSales"
            >
              <template v-slot:top-right>
                <q-input
                  v-model="searchSales"
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

    <!-- New Sale Dialog -->
    <q-dialog v-model="showSaleDialog" persistent>
      <q-card style="min-width: 600px">
        <q-card-section>
          <div class="text-h6">Record New Sale</div>
        </q-card-section>

        <q-card-section class="q-pt-none">
          <q-form @submit="submitSale">
            <!-- Sale Type -->
            <q-select
              v-model="saleForm.sale_type"
              :options="saleTypeOptions"
              label="Sale Type"
              outlined
              emit-value
              map-options
              lazy-rules
              :rules="[(val) => !!val || 'Sale type is required']"
              @update:model-value="onSaleTypeChange"
            />

            <!-- Customer (only for wholesale) -->
            <q-select
              v-if="saleForm.sale_type === 'wholesale'"
              v-model="saleForm.customer"
              :options="customerOptions"
              label="Customer"
              outlined
              emit-value
              map-options
              lazy-rules
              :rules="[(val) => !!val || 'Customer is required for wholesale']"
            />

            <!-- Sale Date/Time -->
            <q-input
              v-model="saleForm.sale_datetime"
              type="datetime-local"
              label="Sale Date & Time"
              outlined
              lazy-rules
              :rules="[(val) => !!val || 'Date is required']"
            />

            <!-- Quantities -->
            <div class="row q-col-gutter-md q-mt-md">
              <div class="col-12">
                <div class="text-subtitle2 q-mb-sm">Quantities (in crates)</div>
              </div>

              <div class="col-6 col-md-3">
                <q-input
                  v-model.number="saleForm.broken_quantity"
                  type="number"
                  label="Broken"
                  outlined
                  lazy-rules
                  :rules="[(val) => val >= 0 || 'Must be 0 or greater']"
                />
              </div>
              <div class="col-6 col-md-3">
                <q-input
                  v-model.number="saleForm.small_quantity"
                  type="number"
                  label="Small"
                  outlined
                  lazy-rules
                  :rules="[(val) => val >= 0 || 'Must be 0 or greater']"
                />
              </div>
              <div class="col-6 col-md-3">
                <q-input
                  v-model.number="saleForm.medium_quantity"
                  type="number"
                  label="Medium"
                  outlined
                  lazy-rules
                  :rules="[(val) => val >= 0 || 'Must be 0 or greater']"
                />
              </div>
              <div class="col-6 col-md-3">
                <q-input
                  v-model.number="saleForm.big_quantity"
                  type="number"
                  label="Big"
                  outlined
                  lazy-rules
                  :rules="[(val) => val >= 0 || 'Must be 0 or greater']"
                />
              </div>
            </div>

            <!-- Total Amount (auto-calculated) -->
            <div class="row q-mt-md q-pa-md bg-grey-2 rounded-borders">
              <div class="col">
                <div class="text-subtitle1">Total Amount</div>
              </div>
              <div class="col-auto">
                <div class="text-h5 text-primary">₵{{ totalAmount }}</div>
              </div>
            </div>

            <!-- Notes -->
            <q-input
              v-model="saleForm.notes"
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
                @click="showSaleDialog = false"
                class="q-mr-sm"
              />
              <q-btn label="Save Sale" type="submit" color="primary" />
            </div>
          </q-form>
        </q-card-section>
      </q-card>
    </q-dialog>
  </q-page>
</template>

<script>
import { ref, computed, onMounted } from 'vue'
import { api } from 'boot/axios'
import { useQuasar } from 'quasar'

export default {
  name: 'SalesPage',

  setup() {
    const $q = useQuasar()
    const showSaleDialog = ref(false)
    const loadingSales = ref(false)
    const searchSales = ref('')
    const salesList = ref([])
    const salesSummary = ref({
      total_revenue: 0,
      total_sales: 0,
      retail_revenue: 0,
      wholesale_revenue: 0,
      retail_count: 0,
      wholesale_count: 0,
    })
    const customers = ref([])
    const eggTypes = ref([])
    const priceTiers = ref([])

    const salesColumns = [
      {
        name: 'sale_datetime',
        label: 'Date & Time',
        field: 'sale_datetime',
        align: 'left',
        sortable: true,
      },
      {
        name: 'sale_type',
        label: 'Type',
        field: 'sale_type',
        align: 'center',
        sortable: true,
        format: (val) => (val === 'retail' ? 'Retail' : 'Wholesale'),
      },
      {
        name: 'customer',
        label: 'Customer',
        field: (row) => row.customer_name || 'N/A',
        align: 'left',
      },
      { name: 'broken', label: 'Broken', field: 'broken_quantity', align: 'center' },
      { name: 'small', label: 'Small', field: 'small_quantity', align: 'center' },
      { name: 'medium', label: 'Medium', field: 'medium_quantity', align: 'center' },
      { name: 'big', label: 'Big', field: 'big_quantity', align: 'center' },
      {
        name: 'total',
        label: 'Total',
        field: 'total_amount',
        align: 'right',
        format: (val) => `₵${val}`,
      },
    ]

    const saleTypeOptions = [
      { label: 'Retail (Single Sales)', value: 'retail' },
      { label: 'Wholesale', value: 'wholesale' },
    ]

    const customerOptions = computed(() => {
      return customers.value.map((customer) => ({
        label: customer.name,
        value: customer.id,
      }))
    })

    const saleForm = ref({
      sale_type: 'retail',
      customer: null,
      sale_datetime: new Date().toISOString().slice(0, 16),
      broken_quantity: 0,
      small_quantity: 0,
      medium_quantity: 0,
      big_quantity: 0,
      notes: '',
    })

    // Calculate total amount based on quantities and pricing
    const totalAmount = computed(() => {
      let total = 0

      // Get prices based on sale type
      const tier = saleForm.value.sale_type === 'retail' ? 'retail' : 'wholesale_base'

      // Helper to get price for an egg type
      const getPrice = (eggTypeName) => {
        const priceTier = priceTiers.value.find(
          (p) => p.egg_type_name === eggTypeName && p.tier === tier && p.is_active,
        )
        return priceTier ? priceTier.price_per_crate : 0
      }

      // Calculate for each egg type
      const brokenPrice = getPrice('Broken')
      const smallPrice = getPrice('Small')
      const mediumPrice = getPrice('Medium')
      const bigPrice = getPrice('Big')

      total += saleForm.value.broken_quantity * brokenPrice
      total += saleForm.value.small_quantity * smallPrice
      total += saleForm.value.medium_quantity * mediumPrice
      total += saleForm.value.big_quantity * bigPrice

      return total.toFixed(2)
    })

    const onSaleTypeChange = (value) => {
      if (value === 'retail') {
        saleForm.value.customer = null
      }
    }

    const loadSalesSummary = async () => {
      try {
        const today = new Date().toISOString().split('T')[0]
        const response = await api.get('/sales/sales/daily-summary/', {
          params: { date: today },
        })
        salesSummary.value = response.data
      } catch (error) {
        console.error('Error loading sales summary:', error)
      }
    }

    const loadSalesList = async () => {
      loadingSales.value = true
      try {
        const response = await api.get('/sales/sales/')
        salesList.value = response.data
      } catch (error) {
        console.error('Error loading sales:', error)
        $q.notify({
          color: 'negative',
          message: 'Failed to load sales',
          icon: 'warning',
        })
      } finally {
        loadingSales.value = false
      }
    }

    const loadCustomers = async () => {
      try {
        const response = await api.get('/customers/customers/?is_active=true')
        customers.value = response.data
      } catch (error) {
        console.error('Error loading customers:', error)
      }
    }

    const loadEggTypes = async () => {
      try {
        const response = await api.get('/inventory/egg-types/')
        eggTypes.value = response.data
      } catch (error) {
        console.error('Error loading egg types:', error)
      }
    }

    const loadPriceTiers = async () => {
      try {
        const response = await api.get('/inventory/price-tiers/')
        priceTiers.value = response.data
      } catch (error) {
        console.error('Error loading price tiers:', error)
      }
    }

    const submitSale = async () => {
      try {
        // Format datetime properly for Django
        const payload = {
          ...saleForm.value,
          sale_datetime: saleForm.value.sale_datetime + ':00', // Add seconds
        }

        await api.post('/sales/sales/', payload)
        $q.notify({
          color: 'positive',
          message: 'Sale recorded successfully!',
          icon: 'check',
        })
        showSaleDialog.value = false
        saleForm.value = {
          sale_type: 'retail',
          customer: null,
          sale_datetime: new Date().toISOString().slice(0, 16),
          broken_quantity: 0,
          small_quantity: 0,
          medium_quantity: 0,
          big_quantity: 0,
          notes: '',
        }
        loadSalesList()
        loadSalesSummary()
      } catch (error) {
        console.error('Error recording sale:', error)
        const errorMessage =
          error.response?.data?.detail ||
          error.response?.data?.non_field_errors?.[0] ||
          'Failed to record sale'
        $q.notify({
          color: 'negative',
          message: errorMessage,
          icon: 'warning',
        })
      }
    }

    onMounted(() => {
      loadSalesSummary()
      loadSalesList()
      loadCustomers()
      loadEggTypes()
      loadPriceTiers()
    })

    return {
      showSaleDialog,
      loadingSales,
      searchSales,
      salesList,
      salesSummary,
      salesColumns,
      saleTypeOptions,
      customerOptions,
      saleForm,
      eggTypes,
      totalAmount,
      onSaleTypeChange,
      submitSale,
    }
  },
}
</script>
