<template>
  <button class="theme-toggle" @click="$emit('toggle')">主题</button>
</template>

<script setup lang="ts">
// Placeholder theme toggle
</script>

<style scoped>
.theme-toggle{background:transparent;border:none;color:var(--n-text-color);padding:4px 8px;cursor:pointer}
</style>
