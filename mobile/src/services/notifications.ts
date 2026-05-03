/**
 * Conflict Zero Mobile - Push Notifications Service
 * Fase 2 - Notificaciones push para alertas de monitoreo
 * 
 * Usa Expo Notifications para recibir alertas cuando cambia
 * el estado de un proveedor en la red.
 */

import * as Notifications from 'expo-notifications';
import * as Device from 'expo-device';
import { Platform } from 'react-native';

Notifications.setNotificationHandler({
  handleNotification: async () => ({
    shouldShowAlert: true,
    shouldPlaySound: true,
    shouldSetBadge: true,
  }),
});

export interface PushToken {
  token: string;
  platform: string;
}

export class NotificationService {
  private static token: string | null = null;

  /**
   * Solicita permisos de notificación y retorna el push token.
   */
  static async registerForPushNotifications(): Promise<PushToken | null> {
    if (!Device.isDevice) {
      console.log('Push notifications solo disponibles en dispositivo físico');
      return null;
    }

    const { status: existingStatus } = await Notifications.getPermissionsAsync();
    let finalStatus = existingStatus;

    if (existingStatus !== 'granted') {
      const { status } = await Notifications.requestPermissionsAsync();
      finalStatus = status;
    }

    if (finalStatus !== 'granted') {
      console.log('Permiso de notificaciones denegado');
      return null;
    }

    const token = (await Notifications.getExpoPushTokenAsync()).data;
    this.token = token;

    if (Platform.OS === 'android') {
      await Notifications.setNotificationChannelAsync('default', {
        name: 'default',
        importance: Notifications.AndroidImportance.MAX,
        vibrationPattern: [0, 250, 250, 250],
        lightColor: '#e94560',
      });
    }

    return { token, platform: Platform.OS };
  }

  /**
   * Envía el push token al backend para asociarlo al usuario.
   */
  static async syncTokenWithBackend(
    token: string,
    authToken: string
  ): Promise<boolean> {
    try {
      const response = await fetch(
        'https://api.conflictzero.com/v1/notifications/push-token',
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${authToken}`,
          },
          body: JSON.stringify({
            push_token: token,
            platform: Platform.OS,
            device_id: Device.deviceId || null,
          }),
        }
      );
      return response.ok;
    } catch (error) {
      console.error('Error sincronizando push token:', error);
      return false;
    }
  }

  /**
   * Escucha notificaciones recibidas mientras la app está abierta.
   */
  static onNotificationReceived(
    callback: (notification: Notifications.Notification) => void
  ): Notifications.Subscription {
    return Notifications.addNotificationReceivedListener(callback);
  }

  /**
   * Escucha cuando el usuario toca una notificación.
   */
  static onNotificationTapped(
    callback: (response: Notifications.NotificationResponse) => void
  ): Notifications.Subscription {
    return Notifications.addNotificationResponseReceivedListener(callback);
  }

  /**
   * Programa una notificación local (para testing o recordatorios).
   */
  static async scheduleLocalNotification(
    title: string,
    body: string,
    data?: Record<string, any>,
    delaySeconds: number = 1
  ): Promise<string> {
    const id = await Notifications.scheduleNotificationAsync({
      content: {
        title,
        body,
        data: data || {},
        sound: 'default',
      },
      trigger: { seconds: delaySeconds },
    });
    return id;
  }

  /**
   * Cancela una notificación local programada.
   */
  static async cancelScheduledNotification(id: string): Promise<void> {
    await Notifications.cancelScheduledNotificationAsync(id);
  }

  /**
   * Limpia el badge de notificaciones.
   */
  static async clearBadge(): Promise<void> {
    await Notifications.setBadgeCountAsync(0);
  }

  /**
   * Obtiene el token actual.
   */
  static getCurrentToken(): string | null {
    return this.token;
  }

  /**
   * Elimina los listeners de notificaciones.
   */
  static removeListener(subscription: Notifications.Subscription): void {
    Notifications.removeNotificationSubscription(subscription);
  }
}
