import { defineConfig, loadEnv } from "vite";
import vue from "@vitejs/plugin-vue";

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, ".", "");
  const backend = env.VITE_BACKEND_PROXY || "http://localhost:8000";

  return {
    plugins: [vue()],
    server: {
      port: 5173,
      proxy: {
        "/screening": { target: backend, changeOrigin: true },
        "/health": { target: backend, changeOrigin: true },
      },
    },
    preview: {
      port: 4173,
      proxy: {
        "/screening": { target: backend, changeOrigin: true },
        "/health": { target: backend, changeOrigin: true },
      },
    },
  };
});
