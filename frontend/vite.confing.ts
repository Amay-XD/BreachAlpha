import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, ".", "");
  const backendUrl = env.VITE_API_BASE_URL || "http://127.0.0.1:5000";

  return {
    plugins: [react()],
    server: {
      port: 3000,
      proxy: {
        "/backend": {
          target: backendUrl,
          changeOrigin: true,
          rewrite: (path) => path.replace(/^\/backend/, ""),
        },
      },
    },
  };
});
