<template>
  <q-page class="q-pa-md">
    <div class="row q-col-gutter-md">
      <!-- Header -->
      <div class="col-12">
        <div class="row items-center justify-between">
          <div>
            <h4 class="q-my-none">Customer Management</h4>
            <p class="text-grey-7 q-my-xs">Manage wholesale customers and custom pricing</p>
          </div>
          <div class="col-auto">
            <q-btn
              color="primary"
              icon="add"
              label="New Customer"
              @click="showCustomerDialog = true"
            />
          </div>
        </div>
      </div>

      <!-- Stats Cards -->
      <div class="col-12 col-md-4">
        <q-card class="bg-primary text-white">
          <q-card-section>
            <div class="text-h6">Total Customers</div>
            <div class="text-h3 q-mt-md">{{ totalCustomers }}</div>
            <div class="row items-center q-mt-sm">
              <q-icon name="people" size="sm" class="q-mr-xs" />
              <span>{{ activeCustomers }} active</span>
            </div>
          </q-card-section>
        </q-card>
      </div>

      <div class="col-12 col-md-4">
        <q-card>
          <q-card-section>
            <div class="text-h6">Recent Sales</div>
            <div class="text-h3 q-mt-md">{{ recentSales }}</div>
            <div class="row items-center q-mt-sm">
              <q-icon name="shopping_cart" size="sm" class="q-mr-xs" />
              <span>from customers</span>
            </div>
          </q-card-section>
        </q-card>
      </div>

      <div class="col-12 col-md-4">
        <q-card class="bg-green text-white">
          <q-card-section>
            <div class="text-h6">Customer Revenue</div>
            <div class="text-h3 q-mt-md">₵{{ customerRevenue }}</div>
            <div class="row items-center q-mt-sm">
              <q-icon name="trending_up" size="sm" class="q-mr-xs" />
              <span>wholesale sales</span>
            </div>
          </q-card-section>
        </q-card>
      </div>

      <!-- Customers Table -->
      <div class="col-12">
        <q-card>
          <q-card-section>
            <div class="text-h6">Wholesale Customers</div>
          </q-card-section>
          <q-card-section class="q-pt-none">
            <q-table
              :rows="customersList"
              :columns="customersColumns"
              row-key="id"
              :loading="loadingCustomers"
              :pagination="{ rowsPerPage: 10 }"
              :filter="searchCustomers"
            >
              <template v-slot:top-right>
                <q-input
                  v-model="searchCustomers"
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

              <template v-slot:body-cell-actions="props">
                <q-td :props="props">
                  <q-btn
                    flat
                    dense
                    icon="edit"
                    color="primary"
                    size="sm"
                    @click="editCustomer(props.row)"
                    class="q-mr-xs"
                  />
                  <q-btn
                    flat
                    dense
                    icon="price_check"
                    color="green"
                    size="sm"
                    @click="managePricing(props.row)"
                    class="q-mr-xs"
                  />
                  <q-btn
                    flat
                    dense
                    icon="delete"
                    color="red"
                    size="sm"
                    @click="deleteCustomer(props.row)"
                  />
                </q-td>
              </template>
            </q-table>
          </q-card-section>
        </q-card>
      </div>
    </div>

    <!-- New/Edit Customer Dialog -->
    <q-dialog v-model="showCustomerDialog" persistent>
      <q-card style="min-width: 500px">
        <q-card-section>
          <div class="text-h6">{{ isEditing ? 'Edit Customer' : 'New Customer' }}</div>
        </q-card-section>

        <q-card-section class="q-pt-none">
          <q-form @submit="submitCustomer">
            <q-input
              v-model="customerForm.name"
              type="text"
              label="Customer Name"
              outlined
              lazy-rules
              :rules="[(val) => !!val || 'Name is required']"
            />

            <q-input
              v-model="customerForm.contact_person"
              type="text"
              label="Contact Person"
              outlined
              class="q-mt-md"
            />

            <q-input
              v-model="customerForm.phone"
              type="text"
              label="Phone Number"
              outlined
              class="q-mt-md"
            />

            <q-input
              v-model="customerForm.email"
              type="email"
              label="Email"
              outlined
              class="q-mt-md"
            />

            <q-input
              v-model="customerForm.address"
              type="textarea"
              label="Address"
              outlined
              class="q-mt-md"
            />

            <q-toggle v-model="customerForm.is_active" label="Active Customer" class="q-mt-md" />

            <div class="row q-mt-md">
              <q-space />
              <q-btn
                label="Cancel"
                color="grey"
                flat
                @click="showCustomerDialog = false"
                class="q-mr-sm"
              />
              <q-btn :label="isEditing ? 'Update' : 'Save'" type="submit" color="primary" />
            </div>
          </q-form>
        </q-card-section>
      </q-card>
    </q-dialog>

    <!-- Pricing Override Dialog -->
    <q-dialog v-model="showPricingDialog" persistent>
      <q-card style="min-width: 600px">
        <q-card-section>
          <div class="text-h6">Custom Pricing for {{ selectedCustomer?.name }}</div>
        </q-card-section>

        <q-card-section class="q-pt-none">
          <div
            v-for="eggType in eggTypes"
            :key="eggType.id"
            class="q-mb-md q-pa-md bg-grey-2 rounded-borders"
          >
            <div class="row items-center">
              <div class="col">
                <div class="text-subtitle2">{{ eggType.name }}</div>
              </div>
              <div class="col-auto">
                <q-input
                  v-model.number="pricingOverrides[eggType.id]"
                  type="number"
                  label="Price per Crate (₵)"
                  dense
                  outlined
                  placeholder="Use default"
                  @blur="savePricingOverride(eggType)"
                >
                  <template v-slot:append>
                    <q-btn
                      flat
                      dense
                      icon="delete"
                      color="red"
                      size="sm"
                      @click="removePricingOverride(eggType)"
                      :disable="!pricingOverrides[eggType.id]"
                    />
                  </template>
                </q-input>
              </div>
            </div>
          </div>

          <div class="row q-mt-md">
            <q-space />
            <q-btn label="Close" color="grey" flat @click="showPricingDialog = false" />
          </div>
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
  name: 'CustomersPage',

  setup() {
    const $q = useQuasar()
    const showCustomerDialog = ref(false)
    const showPricingDialog = ref(false)
    const loadingCustomers = ref(false)
    const searchCustomers = ref('')
    const customersList = ref([])
    const eggTypes = ref([])
    const selectedCustomer = ref(null)
    const isEditing = ref(false)

    const customersColumns = [
      { name: 'name', label: 'Customer Name', field: 'name', align: 'left', sortable: true },
      { name: 'contact_person', label: 'Contact Person', field: 'contact_person', align: 'left' },
      { name: 'phone', label: 'Phone', field: 'phone', align: 'left' },
      { name: 'email', label: 'Email', field: 'email', align: 'left' },
      {
        name: 'is_active',
        label: 'Status',
        field: 'is_active',
        align: 'center',
        format: (val) => (val ? 'Active' : 'Inactive'),
      },
      { name: 'actions', label: 'Actions', align: 'center' },
    ]

    const customerForm = ref({
      name: '',
      contact_person: '',
      phone: '',
      email: '',
      address: '',
      is_active: true,
    })

    const pricingOverrides = ref({})

    const totalCustomers = computed(() => {
      return customersList.value.length
    })

    const activeCustomers = computed(() => {
      return customersList.value.filter((c) => c.is_active).length
    })

    const recentSales = computed(() => {
      // This would come from sales API
      return 0
    })

    const customerRevenue = computed(() => {
      // This would come from sales API
      return 0
    })

    const loadCustomersList = async () => {
      loadingCustomers.value = true
      try {
        const response = await api.get('/customers/customers/')
        customersList.value = response.data
      } catch (error) {
        console.error('Error loading customers:', error)
        $q.notify({
          color: 'negative',
          message: 'Failed to load customers',
          icon: 'warning',
        })
      } finally {
        loadingCustomers.value = false
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

    const loadCustomerPricing = async (customerId) => {
      try {
        const response = await api.get('/customers/customer-price-overrides/', {
          params: { customer: customerId },
        })

        // Reset pricing overrides
        pricingOverrides.value = {}

        // Populate with existing overrides
        response.data.forEach((override) => {
          pricingOverrides.value[override.egg_type] = override.price_per_crate
        })
      } catch (error) {
        console.error('Error loading customer pricing:', error)
      }
    }

    const submitCustomer = async () => {
      try {
        if (isEditing.value && selectedCustomer.value) {
          await api.put(
            `/api/customers/customers/${selectedCustomer.value.id}/`,
            customerForm.value,
          )
          $q.notify({
            color: 'positive',
            message: 'Customer updated successfully!',
            icon: 'check',
          })
        } else {
          await api.post('/api/customers/customers/', customerForm.value)
          $q.notify({
            color: 'positive',
            message: 'Customer created successfully!',
            icon: 'check',
          })
        }

        showCustomerDialog.value = false
        resetCustomerForm()
        loadCustomersList()
      } catch (error) {
        console.error('Error saving customer:', error)
        const errorMessage =
          error.response?.data?.detail ||
          error.response?.data?.non_field_errors?.[0] ||
          'Failed to save customer'
        $q.notify({
          color: 'negative',
          message: errorMessage,
          icon: 'warning',
        })
      }
    }

    const editCustomer = (customer) => {
      isEditing.value = true
      selectedCustomer.value = customer
      customerForm.value = {
        name: customer.name,
        contact_person: customer.contact_person,
        phone: customer.phone,
        email: customer.email,
        address: customer.address,
        is_active: customer.is_active,
      }
      showCustomerDialog.value = true
    }

    const managePricing = async (customer) => {
      selectedCustomer.value = customer
      await loadCustomerPricing(customer.id)
      showPricingDialog.value = true
    }

    const savePricingOverride = async (eggType) => {
      try {
        const price = pricingOverrides.value[eggType.id]

        // Check if override already exists
        const existingOverride = await api.get('/customers/customer-price-overrides/', {
          params: {
            customer: selectedCustomer.value.id,
            egg_type: eggType.id,
          },
        })

        const payload = {
          customer: selectedCustomer.value.id,
          egg_type: eggType.id,
          price_per_crate: price,
          effective_date: new Date().toISOString().split('T')[0],
        }

        if (existingOverride.data.length > 0) {
          // Update existing
          await api.put(
            `/api/customers/customer-price-overrides/${existingOverride.data[0].id}/`,
            payload,
          )
        } else {
          // Create new
          await api.post('/api/customers/customer-price-overrides/', payload)
        }

        $q.notify({
          color: 'positive',
          message: `Pricing updated for ${eggType.name}`,
          icon: 'check',
        })
      } catch (error) {
        console.error('Error saving pricing override:', error)
        $q.notify({
          color: 'negative',
          message: 'Failed to save pricing',
          icon: 'warning',
        })
      }
    }

    const removePricingOverride = async (eggType) => {
      try {
        const response = await api.get('/customers/customer-price-overrides/', {
          params: {
            customer: selectedCustomer.value.id,
            egg_type: eggType.id,
          },
        })

        if (response.data.length > 0) {
          await api.delete(`/api/customers/customer-price-overrides/${response.data[0].id}/`)
          pricingOverrides.value[eggType.id] = null

          $q.notify({
            color: 'positive',
            message: `Pricing override removed for ${eggType.name}`,
            icon: 'check',
          })
        }
      } catch (error) {
        console.error('Error removing pricing override:', error)
        $q.notify({
          color: 'negative',
          message: 'Failed to remove pricing',
          icon: 'warning',
        })
      }
    }

    const deleteCustomer = (customer) => {
      $q.dialog({
        title: 'Confirm Delete',
        message: `Are you sure you want to delete ${customer.name}?`,
        cancel: true,
        persistent: true,
      }).onOk(async () => {
        try {
          await api.delete(`/api/customers/customers/${customer.id}/`)
          $q.notify({
            color: 'positive',
            message: 'Customer deleted successfully!',
            icon: 'check',
          })
          loadCustomersList()
        } catch (error) {
          console.error('Error deleting customer:', error)
          $q.notify({
            color: 'negative',
            message: 'Failed to delete customer',
            icon: 'warning',
          })
        }
      })
    }

    const resetCustomerForm = () => {
      customerForm.value = {
        name: '',
        contact_person: '',
        phone: '',
        email: '',
        address: '',
        is_active: true,
      }
      isEditing.value = false
      selectedCustomer.value = null
    }

    onMounted(() => {
      loadCustomersList()
      loadEggTypes()
    })

    return {
      showCustomerDialog,
      showPricingDialog,
      loadingCustomers,
      searchCustomers,
      customersList,
      eggTypes,
      selectedCustomer,
      isEditing,
      customersColumns,
      customerForm,
      pricingOverrides,
      totalCustomers,
      activeCustomers,
      recentSales,
      customerRevenue,
      submitCustomer,
      editCustomer,
      managePricing,
      savePricingOverride,
      removePricingOverride,
      deleteCustomer,
    }
  },
}
</script>
