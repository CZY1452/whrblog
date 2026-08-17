import { defineConfig } from 'vite';
import path from 'path';
import vue from '@vitejs/plugin-vue';

// 开发代理目标，可用环境变量 API_PROXY_TARGET 覆盖（默认本地 Django:8000）
const API_TARGET = process.env.API_PROXY_TARGET || 'http://127.0.0.1:8000';

export default defineConfig({
  plugins: [vue()],
  // 构建配置
  build: {
    // 输出目录 - 独立前端产物，由 nginx 托管（纯 SPA 架构）
    outDir: 'dist',
    // 清空输出目录
    emptyOutDir: true,
    // 生成manifest文件，方便外部引用
    manifest: true,
    // 压缩配置 - 最高级别
    minify: 'terser',
    terserOptions: {
      compress: {
        // 移除 console 和 debugger
        drop_console: true,
        drop_debugger: true,
        // 移除未使用的代码
        pure_funcs: ['console.log', 'console.info', 'console.debug', 'console.warn'],
        // 移除死代码
        dead_code: true,
        // 使用更激进的优化
        passes: 3,
        // 移除未使用的函数参数
        keep_fargs: false,
        // 移除未使用的函数名
        keep_fnames: false,
        // 移除未使用的类名
        keep_classnames: false,
        // 内联函数
        inline: 3,
        // 移除不可达代码
        conditionals: true,
        // 优化布尔表达式
        booleans: true,
        // 优化循环
        loops: true,
        // 合并变量声明
        join_vars: true,
        // 移除未使用的变量
        unused: true,
        // 折叠常量
        evaluate: true,
        // 优化 if 语句
        if_return: true,
        // 移除空语句
        sequences: true,
        // 压缩属性访问
        properties: true,
      },
      mangle: {
        // 混淆变量名
        toplevel: true,
        // 混淆属性名（谨慎使用）
        properties: false,
        // 保留类名（避免 Alpine.js 等框架问题）
        keep_classnames: false,
        keep_fnames: false,
        // Safari 10 兼容
        safari10: true,
      },
      format: {
        // 移除注释
        comments: false,
        // 使用 ASCII 输出
        ascii_only: true,
        // 紧凑输出
        beautify: false,
        // 压缩到极致
        ecma: 2020,
      },
    },
    // 启用 CSS 压缩
    cssMinify: true,
    // 代码分割阈值（字节）
    chunkSizeWarningLimit: 500,
    // 报告压缩后的大小
    reportCompressedSize: true,
    // Rollup 优化配置（合并后）
    rollupOptions: {
      input: {
        main: path.resolve(__dirname, 'index.html'),
      },
      output: {
        // 资源文件命名
        entryFileNames: 'js/[name]-[hash].js',
        chunkFileNames: 'js/[name]-[hash].js',
        assetFileNames: (assetInfo) => {
          // CSS文件放在css目录
          if (assetInfo.name.endsWith('.css')) {
            return 'css/[name]-[hash][extname]';
          }
          // 其他资源放在assets目录
          return 'assets/[name]-[hash][extname]';
        },
        // Vue/组件代码作为依赖合并进 main bundle，减少 RTT
        // 最小化输出
        compact: true,
        // 不生成 sourcemap
        sourcemap: false,
      },
    },
  },

  // 开发服务器配置
  server: {
    port: 5173,
    host: true,
    // 将 /api /media /admin /sitemap.xml /health 代理到 Django（开发态同域，Cookie 顺畅）
    proxy: {
      '/api': {
        target: API_TARGET,
        changeOrigin: true,
      },
      '/media': {
        target: API_TARGET,
        changeOrigin: true,
      },
      '/static': {
        target: API_TARGET,
        changeOrigin: true,
      },
      '/admin': {
        target: API_TARGET,
        changeOrigin: true,
      },
      '/sitemap.xml': {
        target: API_TARGET,
        changeOrigin: true,
      },
      '/health': {
        target: API_TARGET,
        changeOrigin: true,
      },
    },
    // CORS配置，允许Django访问
    cors: true,
    // HMR配置
    hmr: {
      overlay: true,
    },
  },

  // 路径解析
  resolve: {
    alias: {
      '@': path.resolve(__dirname, 'src'),
      '@components': path.resolve(__dirname, 'src/components'),
      '@styles': path.resolve(__dirname, 'src/styles'),
    },
  },

  // CSS配置
  css: {
    postcss: './postcss.config.js',
  },
});
