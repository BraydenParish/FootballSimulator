import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    open: true
  },
  test: {
    globals: true,
    environment: "jsdom",
    setupFiles: "./src/test/setup.ts",
    include: ["src/**/*.test.ts", "src/**/*.test.tsx", "tests/**/*.test.ts"],
    exclude: ["e2e/**", "playwright-report/**", "**/node_modules/**"],
    coverage: {
      reporter: ["text", "lcov"],
      provider: "v8",
      lines: 70,
      branches: 60
    }
  }
});
