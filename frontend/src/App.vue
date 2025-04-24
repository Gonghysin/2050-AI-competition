<template>
  <div class="app-container">
    <router-view />
  </div>
</template>

<script>
export default {
  name: 'App'
}
</script>

<style>
body {
  margin: 0;
  padding: 0;
  font-family: 'Helvetica Neue', Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  background-color: #f5f7fa;
}

.app-container {
  width: 100%;
  height: 100vh;
  max-width: 100%;
  margin: 0 auto;
}
</style> 