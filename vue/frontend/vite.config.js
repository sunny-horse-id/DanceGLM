import { fileURLToPath, URL } from 'node:url'

import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

//ElementPlus按需导入
import AutoImport from 'unplugin-auto-import/vite'
import Components from 'unplugin-vue-components/vite'
import { ElementPlusResolver } from 'unplugin-vue-components/resolvers'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [
    vue(),
    AutoImport({
      resolvers: [ElementPlusResolver()],
    }),
    Components({
      resolvers: [ElementPlusResolver()],
    }),
  ],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    }
  },
  server: {
    proxy: {
      //拦截所有包含/api的链接
      '/api': {
        //转换的目标链接将5173转为5017，由前端发送
        target: 'http://192.168.0.100:5017',
        //是否换源，true则转化
        changeOrigin: true,
        //使得转换后的链接中的/api变成空字符串
        rewrite: (path) => path.replace(/^\/api/, '')
      }
    }
  }
})