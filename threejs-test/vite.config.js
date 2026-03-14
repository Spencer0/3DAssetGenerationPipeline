import { defineConfig } from "vite";
import { resolve } from "path";

export default defineConfig({
  root: resolve(__dirname),
  publicDir: resolve(__dirname, "assets"),
  server: {
    port: 5173,
    open: false
  },
  build: {
    outDir: resolve(__dirname, "..", "docs"),
    emptyOutDir: true
  }
});
