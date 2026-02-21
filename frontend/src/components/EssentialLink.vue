<template>
  <q-item clickable :to="link" :class="isActive ? 'bg-primary text-white' : ''">
    <q-item-section v-if="icon" avatar>
      <q-icon :name="icon" />
    </q-item-section>

    <q-item-section>
      <q-item-label>{{ title }}</q-item-label>
      <q-item-label caption>
        {{ caption }}
      </q-item-label>
    </q-item-section>
  </q-item>
</template>

<script>
import { computed } from 'vue'
import { useRoute } from 'vue-router'

export default {
  name: 'EssentialLink',

  props: {
    title: {
      type: String,
      required: true,
    },
    caption: {
      type: String,
      default: '',
    },
    link: {
      type: String,
      default: '#',
    },
    icon: {
      type: String,
      default: '',
    },
  },

  setup(props) {
    const route = useRoute()

    const isActive = computed(() => {
      return route.path === props.link
    })

    return {
      isActive,
    }
  },
}
</script>

<style scoped>
.bg-primary {
  border-left: 4px solid #1976d2;
}
</style>
