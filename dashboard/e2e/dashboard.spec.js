import { test, expect } from '@playwright/test';

test.describe('Dashboard', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/login');
    await page.fill('input[type="email"]', 'test@conflictzero.com');
    await page.fill('input[type="password"]', 'testpassword');
    await page.click('button[type="submit"]');
    await page.waitForURL('/dashboard');
  });

  test('should display dashboard metrics', async ({ page }) => {
    await expect(page.locator('text=Verificaciones Realizadas')).toBeVisible();
    await expect(page.locator('text=Score Promedio')).toBeVisible();
    await expect(page.locator('text=Proveedores en Red')).toBeVisible();
  });

  test('should toggle dark mode', async ({ page }) => {
    const toggle = page.locator('[data-testid="theme-toggle"]').first();
    if (await toggle.isVisible()) {
      await toggle.click();
      await expect(page.locator('html')).toHaveAttribute('data-theme', 'dark');
    }
  });
});

test.describe('Verifications', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/login');
    await page.fill('input[type="email"]', 'test@conflictzero.com');
    await page.fill('input[type="password"]', 'testpassword');
    await page.click('button[type="submit"]');
    await page.waitForURL('/dashboard');
    await page.click('text=Verificaciones');
    await page.waitForURL(/.*verifications/);
  });

  test('should search for RUC', async ({ page }) => {
    await page.fill('input[placeholder*="RUC"]', '20100154387');
    await page.click('text=Verificar');
    await expect(page.locator('text=Resultado')).toBeVisible({ timeout: 10000 });
  });
});
