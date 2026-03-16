import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useSnackbarStore = defineStore('snackbar', () => {
  const show = ref(false)
  const message = ref('')
  const color = ref('success') // success, error, warning, info

  function notify(msg: string, type: 'success' | 'error' | 'warning' | 'info' = 'success') {
    message.value = msg
    color.value = type
    show.value = true
  }

  return { show, message, color, notify }
})
