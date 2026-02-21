<template>
  <q-page class="q-pa-md">
    <div class="row q-col-gutter-md">
      <!-- Header -->
      <div class="col-12">
        <div class="row items-center justify-between">
          <div>
            <h4 class="q-my-none">Inventory Management</h4>
            <p class="text-grey-7 q-my-xs">Track egg stock levels and manage intake</p>
          </div>
          <div class="col-auto">
            <q-btn color="primary" icon="add" label="Log Intake" @click="openIntakeDialog" />
          </div>
        </div>
      </div>

      <!-- Intake Logs Table -->
      <div class="col-12">
        <q-card>
          <q-card-section>
            <div class="text-h6">Intake Logs</div>
          </q-card-section>
          <q-card-section class="q-pt-none">
            <q-table
              :rows="intakeLogs"
              :columns="intakeColumns"
              row-key="id"
              :loading="loadingIntake"
              :pagination="{ rowsPerPage: 10 }"
            >
              <template v-slot:top-right>
                <q-input
                  v-model="searchIntake"
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

    <!-- Log Intake Dialog - FIXED: Removed @hide="resetForm" -->
    <q-dialog v-model="showIntakeDialog">
      <q-card style="min-width: 500px">
        <q-card-section>
          <div class="text-h6">Log Daily Intake</div>
        </q-card-section>

        <q-card-section class="q-pt-none">
          <q-input v-model="intakeForm.recorded_date" type="date" label="Date" outlined />

          <div class="row q-col-gutter-md q-mt-md">
            <div class="col-6">
              <q-input
                v-model.number="intakeForm.broken_crates"
                type="number"
                label="Broken Crates"
                outlined
                min="0"
              />
            </div>
            <div class="col-6">
              <q-input
                v-model.number="intakeForm.small_crates"
                type="number"
                label="Small Crates"
                outlined
                min="0"
              />
            </div>
            <div class="col-6">
              <q-input
                v-model.number="intakeForm.medium_crates"
                type="number"
                label="Medium Crates"
                outlined
                min="0"
              />
            </div>
            <div class="col-6">
              <q-input
                v-model.number="intakeForm.big_crates"
                type="number"
                label="Big Crates"
                outlined
                min="0"
              />
            </div>
          </div>

          <q-input
            v-model="intakeForm.notes"
            type="textarea"
            label="Notes"
            outlined
            class="q-mt-md"
          />

          <div class="row q-mt-md">
            <q-space />
            <q-btn
              label="Cancel"
              color="grey"
              flat
              @click="closeDialog"
              class="q-mr-sm"
              :disable="isSubmitting"
            />
            <q-btn
              label="Save"
              color="primary"
              @click="submitIntake"
              :loading="isSubmitting"
              :disable="isSubmitting"
            />
          </div>
        </q-card-section>
      </q-card>
    </q-dialog>
  </q-page>
</template>

<script>
import { ref, onMounted } from 'vue'
import { api } from 'boot/axios'
import { useQuasar } from 'quasar'

export default {
  name: 'InventoryPage',

  setup() {
    console.log('✅ InventoryPage mounted!')
    const $q = useQuasar()
    const showIntakeDialog = ref(false)
    const loadingIntake = ref(false)
    const searchIntake = ref('')
    const intakeLogs = ref([])
    const isSubmitting = ref(false)

    const intakeColumns = [
      {
        name: 'recorded_date',
        label: 'Date',
        field: 'recorded_date',
        align: 'left',
        sortable: true,
      },
      { name: 'broken_crates', label: 'Broken', field: 'broken_crates', align: 'center' },
      { name: 'small_crates', label: 'Small', field: 'small_crates', align: 'center' },
      { name: 'medium_crates', label: 'Medium', field: 'medium_crates', align: 'center' },
      { name: 'big_crates', label: 'Big', field: 'big_crates', align: 'center' },
      {
        name: 'total_crates',
        label: 'Total',
        field: (row) => row.broken_crates + row.small_crates + row.medium_crates + row.big_crates,
        align: 'center',
      },
      { name: 'notes', label: 'Notes', field: 'notes', align: 'left' },
    ]

    const intakeForm = ref({
      recorded_date: new Date().toISOString().split('T')[0],
      broken_crates: 0,
      small_crates: 0,
      medium_crates: 0,
      big_crates: 0,
      notes: '',
    })

    const resetForm = () => {
      intakeForm.value = {
        recorded_date: new Date().toISOString().split('T')[0],
        broken_crates: 0,
        small_crates: 0,
        medium_crates: 0,
        big_crates: 0,
        notes: '',
      }
    }

    const openIntakeDialog = () => {
      resetForm()
      showIntakeDialog.value = true
    }

    // FIXED: Reset form BEFORE closing dialog on cancel
    const closeDialog = () => {
      resetForm()
      showIntakeDialog.value = false
    }

    const loadIntakeLogs = async () => {
      loadingIntake.value = true
      try {
        const response = await api.get('/inventory/intake-logs/')
        intakeLogs.value = response.data
      } catch (error) {
        console.error('Error loading intake logs:', error)
        $q.notify({
          color: 'negative',
          message: 'Failed to load intake logs',
          icon: 'warning',
        })
      } finally {
        loadingIntake.value = false
      }
    }

    const submitIntake = async () => {
      if (isSubmitting.value) return
      isSubmitting.value = true

      try {
        const response = await api.post('/inventory/intake-logs/', intakeForm.value)
        console.log('✅ Intake logged successfully:', response.data)

        // FIXED: Show confirmation FIRST
        $q.notify({
          color: 'positive',
          message: 'Intake logged successfully!',
          icon: 'check',
          timeout: 2000,
        })

        // FIXED: Close dialog AFTER notification but BEFORE refresh
        showIntakeDialog.value = false

        // FIXED: Refresh data immediately after closing dialog
        await loadIntakeLogs()

        // Reset form state (safe since dialog is closed; openIntakeDialog will reset again on next open)
        resetForm()
      } catch (error) {
        console.error('❌ Error logging intake:', error)
        console.error('Error response:', error.response?.data)

        $q.notify({
          color: 'negative',
          message: error.response?.data?.detail || 'Failed to log intake',
          icon: 'warning',
          timeout: 3000,
        })
      } finally {
        isSubmitting.value = false
      }
    }

    onMounted(() => {
      console.log('✅ InventoryPage onMounted() triggered')
      loadIntakeLogs()
    })

    return {
      showIntakeDialog,
      loadingIntake,
      searchIntake,
      intakeLogs,
      intakeColumns,
      intakeForm,
      submitIntake,
      isSubmitting,
      openIntakeDialog,
      closeDialog,
      resetForm,
    }
  },
}
</script>
