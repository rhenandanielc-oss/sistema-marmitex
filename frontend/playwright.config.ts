import { defineConfig } from '@playwright/test'

/**
 * E2E contra o sistema completo (backend + frontend já rodando).
 * Variáveis: E2E_BASE_URL, E2E_EMAIL, E2E_PASSWORD, PLAYWRIGHT_CHROMIUM_PATH (opcional).
 */
export default defineConfig({
  testDir: './e2e',
  timeout: 60_000,
  workers: 1,
  reporter: [['list']],
  use: {
    baseURL: process.env.E2E_BASE_URL ?? 'http://localhost:4173',
    locale: 'pt-BR',
    viewport: { width: 1440, height: 900 },
    launchOptions: process.env.PLAYWRIGHT_CHROMIUM_PATH ? { executablePath: process.env.PLAYWRIGHT_CHROMIUM_PATH } : {},
    trace: 'retain-on-failure',
  },
})
