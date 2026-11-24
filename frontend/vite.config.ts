import { defineConfig, loadEnv } from "vite";
import vue from "@vitejs/plugin-vue";
import ui from "@nuxt/ui/vite";

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, ".", "");
  const backend = env.VITE_BACKEND_PROXY || "http://localhost:8000";

  return {
    plugins: [
      vue(),
      ui({
        icon: {
          clientBundle: {
            scan: true,
          },
        },
        experimental: {
          componentDetection: true,
        },
        ui: {
          colors: {
            error: "red",
            info: "cyan",
            neutral: "mist",
            secondary: "zinc",
            success: "emerald",
            primary: "blue",
            warning: "amber",
          },
        },
      }),
    ],
    build: {
      emptyOutDir: true,
      outDir: "../backend/app/static",
    },
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
