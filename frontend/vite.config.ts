import { defineConfig } from 'vite';
import vue from '@vitejs/plugin-vue'; 
import { resolve } from 'path';
import process from 'node:process';
import Icons from 'unplugin-icons/vite';
import Components from 'unplugin-vue-components/vite';
import { NaiveUiResolver } from 'unplugin-vue-components/resolvers';
import IconsResolver from 'unplugin-icons/resolver';
import { FileSystemIconLoader } from 'unplugin-icons/loaders';
import UnoCSS from '@unocss/vite';

const localIconPath = resolve(__dirname, 'src/assets/svg-icons');

export default defineConfig({
  plugins: [
    vue({
      script: {
        defineModel: true,
        propsDestructure: true
      }
    }),
    UnoCSS(),
    Icons({
      compiler: 'vue3',
      customCollections: {
       'local': FileSystemIconLoader(localIconPath, svg =>
          // Ensure inserted width/height are valid CSS lengths (use 1em so icons scale with font)
          svg.replace(/<svg\s/, '<svg width="1em" height="1em" ')
        )
      },
      scale: 1,
      defaultClass: 'inline-block'
    }),
    Components({
      dts: 'src/typings/components.d.ts',
      types: [{ from: 'vue-router', names: ['RouterLink', 'RouterView'] }],
      resolvers: [
        NaiveUiResolver(),
        IconsResolver({ customCollections: ['local'], componentPrefix: 'icon' })
      ]
    })
  ],

  resolve: {
    alias: {
      '@': resolve(__dirname, 'src'),
      '@sa': resolve(__dirname, 'src/sa'),
      '@stores': resolve(__dirname, 'src/stores'),
      '@styles': resolve(__dirname, 'src/styles/css'),
      '@api': resolve(__dirname, 'src/api')
    }
  },

  server: {
    port: 5137,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        secure: false,
      },
      '/media': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        secure: false,
      }
    }
  }
})