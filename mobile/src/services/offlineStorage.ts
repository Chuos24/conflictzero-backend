/**
 * Conflict Zero Mobile - Offline Storage Service
 * Fase 2 - Modo offline con sincronización
 * 
 * Usa AsyncStorage para cachear verificaciones y datos de red
 * cuando no hay conexión a internet.
 */

import AsyncStorage from '@react-native-async-storage/async-storage';

const CACHE_PREFIX = 'cz_offline_';
const CACHE_TTL = 24 * 60 * 60 * 1000; // 24 horas

export interface CachedVerification {
  ruc: string;
  data: any;
  cachedAt: number;
}

export interface PendingSync {
  id: string;
  type: 'verification' | 'alert_read' | 'profile_update';
  payload: any;
  createdAt: number;
  retries: number;
}

export class OfflineStorage {
  /**
   * Guarda una verificación en cache para uso offline.
   */
  static async cacheVerification(ruc: string, data: any): Promise<void> {
    const key = `${CACHE_PREFIX}verify_${ruc}`;
    const cached: CachedVerification = {
      ruc,
      data,
      cachedAt: Date.now(),
    };
    await AsyncStorage.setItem(key, JSON.stringify(cached));
  }

  /**
   * Obtiene una verificación cacheada si existe y no expiró.
   */
  static async getCachedVerification(ruc: string): Promise<any | null> {
    const key = `${CACHE_PREFIX}verify_${ruc}`;
    const raw = await AsyncStorage.getItem(key);
    if (!raw) return null;

    try {
      const cached: CachedVerification = JSON.parse(raw);
      if (Date.now() - cached.cachedAt > CACHE_TTL) {
        await AsyncStorage.removeItem(key);
        return null;
      }
      return cached.data;
    } catch {
      return null;
    }
  }

  /**
   * Guarda la red de proveedores en cache.
   */
  static async cacheNetwork(suppliers: any[]): Promise<void> {
    const key = `${CACHE_PREFIX}network`;
    await AsyncStorage.setItem(
      key,
      JSON.stringify({ suppliers, cachedAt: Date.now() })
    );
  }

  /**
   * Obtiene la red de proveedores cacheada.
   */
  static async getCachedNetwork(): Promise<any[] | null> {
    const key = `${CACHE_PREFIX}network`;
    const raw = await AsyncStorage.getItem(key);
    if (!raw) return null;

    try {
      const cached = JSON.parse(raw);
      if (Date.now() - cached.cachedAt > CACHE_TTL) {
        await AsyncStorage.removeItem(key);
        return null;
      }
      return cached.suppliers;
    } catch {
      return null;
    }
  }

  /**
   * Guarda las alertas en cache.
   */
  static async cacheAlerts(alerts: any[]): Promise<void> {
    const key = `${CACHE_PREFIX}alerts`;
    await AsyncStorage.setItem(
      key,
      JSON.stringify({ alerts, cachedAt: Date.now() })
    );
  }

  /**
   * Obtiene las alertas cacheadas.
   */
  static async getCachedAlerts(): Promise<any[] | null> {
    const key = `${CACHE_PREFIX}alerts`;
    const raw = await AsyncStorage.getItem(key);
    if (!raw) return null;

    try {
      const cached = JSON.parse(raw);
      if (Date.now() - cached.cachedAt > CACHE_TTL) {
        await AsyncStorage.removeItem(key);
        return null;
      }
      return cached.alerts;
    } catch {
      return null;
    }
  }

  /**
   * Agrega una operación pendiente de sincronización.
   */
  static async addPendingSync(pending: Omit<PendingSync, 'retries'>): Promise<void> {
    const key = `${CACHE_PREFIX}pending_sync`;
    const existing = await AsyncStorage.getItem(key);
    const queue: PendingSync[] = existing ? JSON.parse(existing) : [];
    queue.push({ ...pending, retries: 0 });
    await AsyncStorage.setItem(key, JSON.stringify(queue));
  }

  /**
   * Obtiene todas las operaciones pendientes.
   */
  static async getPendingSyncs(): Promise<PendingSync[]> {
    const key = `${CACHE_PREFIX}pending_sync`;
    const raw = await AsyncStorage.getItem(key);
    if (!raw) return [];
    try {
      return JSON.parse(raw);
    } catch {
      return [];
    }
  }

  /**
   * Marca una operación como completada (la elimina).
   */
  static async removePendingSync(id: string): Promise<void> {
    const key = `${CACHE_PREFIX}pending_sync`;
    const existing = await AsyncStorage.getItem(key);
    if (!existing) return;
    const queue: PendingSync[] = JSON.parse(existing);
    const filtered = queue.filter((item) => item.id !== id);
    await AsyncStorage.setItem(key, JSON.stringify(filtered));
  }

  /**
   * Incrementa el contador de reintentos.
   */
  static async incrementRetry(id: string): Promise<void> {
    const key = `${CACHE_PREFIX}pending_sync`;
    const existing = await AsyncStorage.getItem(key);
    if (!existing) return;
    const queue: PendingSync[] = JSON.parse(existing);
    const item = queue.find((q) => q.id === id);
    if (item) {
      item.retries += 1;
      await AsyncStorage.setItem(key, JSON.stringify(queue));
    }
  }

  /**
   * Limpia todo el cache offline.
   */
  static async clearAll(): Promise<void> {
    const keys = await AsyncStorage.getAllKeys();
    const offlineKeys = keys.filter((k) => k.startsWith(CACHE_PREFIX));
    await AsyncStorage.multiRemove(offlineKeys);
  }

  /**
   * Obtiene estadísticas del cache.
   */
  static async getStats(): Promise<{
    verifications: number;
    network: boolean;
    alerts: boolean;
    pendingSyncs: number;
  }> {
    const keys = await AsyncStorage.getAllKeys();
    const offlineKeys = keys.filter((k) => k.startsWith(CACHE_PREFIX));

    const verifications = offlineKeys.filter((k) =>
      k.startsWith(`${CACHE_PREFIX}verify_`)
    ).length;
    const network = offlineKeys.includes(`${CACHE_PREFIX}network`);
    const alerts = offlineKeys.includes(`${CACHE_PREFIX}alerts`);

    const pendingRaw = await AsyncStorage.getItem(`${CACHE_PREFIX}pending_sync`);
    const pendingSyncs = pendingRaw ? JSON.parse(pendingRaw).length : 0;

    return { verifications, network, alerts, pendingSyncs };
  }
}
