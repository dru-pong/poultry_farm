// Configuration for your app
import { defineConfig } from '#q-app/wrappers'

export default defineConfig((ctx) => {
  return {
    boot: ['axios'],
    css: ['app.scss'],
    extras: ['roboto-font', 'material-icons'],

    build: {
      env: {
        // CRITICAL: Set the actual backend URL for production
        API_BASE_URL: ctx.dev ? '/api' : 'https://poultry-farm-lzio.onrender.com/api/',
      },
      target: {
        browser: ['es2022', 'firefox115', 'chrome115', 'safari14'],
        node: 'node20',
      },
      vueRouterMode: 'hash',

      vitePlugins: [
        [
          'vite-plugin-checker',
          {
            eslint: {
              lintCommand: 'eslint -c ./eslint.config.js "./src*/**/*.{js,mjs,cjs,vue}"',
              useFlatConfig: true,
            },
          },
          { server: false },
        ],
      ],
    },

    devServer: {
      open: true,
      proxy: {
        '/api': {
          target: 'http://127.0.0.1:8000',
          changeOrigin: true,
          secure: false,
          ws: true,
        },
      },
    },

    framework: {
      config: {},
      plugins: ['Notify', 'Dialog'],
    },
    animations: [],

    // Keep the rest of your config unchanged...
    ssr: {
      prodPort: 3000,
      middlewares: ['render'],
      pwa: false,
    },
    pwa: {
      workboxMode: 'GenerateSW',
    },
    cordova: {},
    capacitor: {
      hideSplashscreen: true,
    },
    electron: {
      preloadScripts: ['electron-preload'],
      inspectPort: 5858,
      bundler: 'packager',
      packager: {},
      builder: {
        appId: 'poultry-ai-frontend',
      },
    },
    bex: {
      extraScripts: [],
    },
  }
})
