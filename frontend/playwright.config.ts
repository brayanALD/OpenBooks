import { defineConfig } from "@playwright/test";

/**
 * Tests E2E. Levantan SU PROPIO backend (8300, datos nuevos en frontend/.e2e) y SU PROPIO frontend (3300),
 * así que no dependen de tus servidores de desarrollo ni tocan backend/data.
 *
 * Antes de lanzarlos hay que compilar el frontend: `npm run build`.
 * Navegador: por defecto el Google Chrome instalado en el equipo (no hay que descargar nada).
 * Para usar el Chromium propio de Playwright (`npx playwright install chromium`): PW_CHANNEL=chromium-bundled npm run test:e2e
 */
const WEB = "http://localhost:3300";
const API_HEALTH = "http://localhost:8300/api/v1/health";

export default defineConfig({
  testDir: "./e2e",
  // Un solo backend con estado compartido: los archivos se ejecutan en orden y uno tras otro.
  fullyParallel: false,
  workers: 1,
  timeout: 60_000,
  expect: { timeout: 10_000 },
  reporter: [["list"], ["html", { open: "never" }]],
  use: {
    baseURL: WEB,
    channel: process.env.PW_CHANNEL === "chromium-bundled" ? undefined : process.env.PW_CHANNEL || "chrome",
    locale: "es-CO",
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
  },
  webServer: [
    {
      command: "node e2e/start-backend.mjs",
      url: API_HEALTH,
      reuseExistingServer: false,
      timeout: 120_000,
      stdout: "ignore",
    },
    {
      command: "npx next start -p 3300",
      url: WEB,
      reuseExistingServer: false,
      timeout: 120_000,
      env: { API_URL: "http://localhost:8300/api/v1", SITE_URL: WEB },
    },
  ],
});
