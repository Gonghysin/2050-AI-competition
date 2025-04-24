/* eslint-disable */
import { createApp } from 'vue'
import App from './App.vue'
import './assets/main.css'
import store from './store'  // 引入store目录中的store实例

// 创建应用实例
const app = createApp(App)
app.use(store)  // 使用Vuex store
app.mount('#app') 