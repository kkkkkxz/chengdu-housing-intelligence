<template>
  <button class="refresh-btn" @click="$emit('refresh')">刷新</button>
</template>

<script setup lang="ts">
// Placeholder refresh button
</script>

<style scoped>
.refresh-btn{background:transparent;border:none;color:var(--n-text-color);padding:4px 8px;cursor:pointer}
</style>
