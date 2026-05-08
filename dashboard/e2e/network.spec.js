import { test, expect } from '@playwright/test';

test.describe('Network - Mi Red', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/login');
    await page.fill('input[type="email"]', 'test@conflictzero.com');
    await page.fill('input[type="password"]', 'testpassword');
    await page.click('button[type="submit"]');
    await page.waitForURL('/dashboard');
    await page.click('text=Mi Red');
    await page.waitForURL(/.*network/);
  });

  test('should display network page', async ({ page }) => {
    await expect(page.locator('text=Mi Red de Proveedores')).toBeVisible();
    await expect(page.locator('text=Proveedores verificados')).toBeVisible();
  });

  test('should open add supplier modal', async ({ page }) => {
    await page.click('text=Agregar Proveedor');
    await expect(page.locator('text=Agregar Proveedor')).toBeVisible();
    await expect(page.locator('input[placeholder*="RUC"]')).toBeVisible();
  });

  test('should show supplier list or empty state', async ({ page }) => {
    const tableOrEmpty = page.locator('table, text=No tienes proveedores');
    await expect(tableOrEmpty.first()).toBeVisible();
  });

  test('should navigate to supplier alerts', async ({ page }) => {
    await page.click('text=Alertas');
    await expect(page.locator('text=Alertas de Proveedores')).toBeVisible();
  });
});

test.describe('Compare', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/login');
    await page.fill('input[type="email"]', 'test@conflictzero.com');
    await page.fill('input[type="password"]', 'testpassword');
    await page.click('button[type="submit"]');
    await page.waitForURL('/dashboard');
    await page.click('text=Comparar');
    await page.waitForURL(/.*compare/);
  });

  test('should display compare page', async ({ page }) => {
    await expect(page.locator('text=Comparar Proveedores')).toBeVisible();
    await expect(page.locator('text=Selecciona hasta 10 RUCs')).toBeVisible();
  });

  test('should add RUCs to comparison', async ({ page }) => {
    await page.fill('input[placeholder*="RUC"]', '20100154387');
    await page.click('text=Agregar');
    await expect(page.locator('text=20100154387')).toBeVisible();
  });

  test('should run comparison with multiple RUCs', async ({ page }) => {
    await page.fill('input[placeholder*="RUC"]', '20100154387');
    await page.click('text=Agregar');
    await page.fill('input[placeholder*="RUC"]', '20100123091');
    await page.click('text=Agregar');
    await page.click('text=Comparar');
    await expect(page.locator('text=Resultado de Comparación')).toBeVisible({ timeout: 15000 });
  });
});
