import { defineConfig } from "@playwright/test";
export default defineConfig({
  testDir: "./tests",
  use: {
    baseURL: process.env.WEB_URL || "http://localhost:3100",
    headless: true,
  },
  timeout: 60000,
  workers: 1,
  reporter: "list",
});
