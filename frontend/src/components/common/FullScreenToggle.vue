<template>
  <button class="fs-toggle" @click="toggle">
    全屏
  </button>
</template>

<script setup lang="ts">
import { ref } from 'vue'

const isFull = ref(false)
function toggle() {
  if (!document.fullscreenElement) {
    document.documentElement.requestFullscreen?.()
    isFull.value = true
  } else {
    document.exitFullscreen?.()
    isFull.value = false
  }
}
</script>

<style scoped>
.fs-toggle {
  background: transparent;
  border: none;
  color: var(--n-text-color);
  padding: 4px 8px;
  cursor: pointer;
}
</style>
