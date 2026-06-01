import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { VitePWA } from "vite-plugin-pwa";

// Shared so `vite preview` (which serves the SW-active production build) hits
// the same backend proxy as `vite dev` — required for E2E against the redeem
// counter and resolve endpoints.
const proxy = {
  "/api": { target: "http://localhost:8000", changeOrigin: true },
};

export default defineConfig({
  plugins: [
    react(),
    VitePWA({
      registerType: "autoUpdate",
      // Ported from the (now deleted) static public/manifest.webmanifest — the
      // plugin generates dist/manifest.webmanifest from these values.
      manifest: {
        name: "QoverwRap Demo",
        short_name: "QoverwRap",
        description: "3-layer QR + 내장 서명 + 발급자 라우팅 시연",
        lang: "ko",
        start_url: "/",
        scope: "/",
        display: "standalone",
        orientation: "portrait",
        background_color: "#f8fafc",
        theme_color: "#0f172a",
        icons: [
          {
            src: "/icon.svg",
            sizes: "any",
            type: "image/svg+xml",
            purpose: "any maskable",
          },
        ],
      },
      workbox: {
        globPatterns: ["**/*.{js,css,html,svg,png,woff2}"],
        // CRITICAL: /api must never be cached — the redeem counter and resolve
        // results are live data. NetworkOnly + denylist keep them off the SW.
        runtimeCaching: [{ urlPattern: /\/api\//, handler: "NetworkOnly" }],
        navigateFallbackDenylist: [/^\/api\//],
      },
    }),
  ],
  server: {
    host: true,
    allowedHosts: [".trycloudflare.com", ".cfargotunnel.com"],
    proxy,
  },
  preview: {
    proxy,
  },
});
