/**
 * Conflict Zero - Deep Linking Service
 * Maneja deep links para navegación desde push notifications
 */

import { Linking } from 'react-native';
import * as Notifications from 'expo-notifications';
import { NavigationContainerRef } from '@react-navigation/native';

export interface DeepLinkData {
  screen: string;
  params?: Record<string, any>;
  notificationId?: string;
}

class DeepLinkingService {
  private navigationRef: NavigationContainerRef<any> | null = null;
  private pendingDeepLink: DeepLinkData | null = null;

  /**
   * Inicializa el servicio de deep linking
   */
  initialize(navigationRef: NavigationContainerRef<any>) {
    this.navigationRef = navigationRef;

    // Manejar deep links cuando la app está cerrada
    Linking.getInitialURL().then((url) => {
      if (url) {
        this.handleDeepLink(url);
      }
    });

    // Manejar deep links cuando la app está abierta
    Linking.addEventListener('url', ({ url }) => {
      this.handleDeepLink(url);
    });

    // Manejar notificaciones cuando la app está cerrada
    Notifications.getLastNotificationResponseAsync().then((response) => {
      if (response?.notification.request.content.data) {
        this.handleNotificationData(response.notification.request.content.data);
      }
    });

    // Listener para notificaciones en foreground
    this.setupNotificationListener();

    // Procesar pending deep link si existe
    if (this.pendingDeepLink) {
      this.navigate(this.pendingDeepLink);
      this.pendingDeepLink = null;
    }
  }

  /**
   * Configura listener para notificaciones en foreground
   */
  private setupNotificationListener() {
    Notifications.addNotificationResponseReceivedListener((response) => {
      const data = response.notification.request.content.data;
      this.handleNotificationData(data);
    });
  }

  /**
   * Parsea una URL y extrae la ruta y parámetros
   */
  parseUrl(url: string): DeepLinkData | null {
    // Formatos soportados:
    // conflictzero://company/12345678901
    // conflictzero://verify?ruc=12345678901
    // conflictzero://network
    // conflictzero://alerts/alert-id-123

    const parsed = new URL(url);
    
    if (parsed.protocol !== 'conflictzero:') {
      return null;
    }

    const pathParts = parsed.pathname.split('/').filter(Boolean);
    const screen = pathParts[0];
    const id = pathParts[1];

    // Extraer query params
    const params: Record<string, any> = {};
    parsed.searchParams.forEach((value, key) => {
      params[key] = value;
    });

    if (id) {
      params.id = id;
    }

    return { screen, params };
  }

  /**
   * Maneja una URL de deep link
   */
  handleDeepLink(url: string) {
    const deepLink = this.parseUrl(url);
    if (deepLink) {
      this.navigate(deepLink);
    }
  }

  /**
   * Maneja datos de notificación push
   */
  handleNotificationData(data: any) {
    if (!data || !data.screen) return;

    const deepLink: DeepLinkData = {
      screen: data.screen,
      params: data.params || {},
      notificationId: data.notificationId,
    };

    this.navigate(deepLink);
  }

  /**
   * Navega a una pantalla basada en deep link data
   */
  private navigate(deepLink: DeepLinkData) {
    if (!this.navigationRef?.isReady()) {
      // Guardar para cuando la navegación esté lista
      this.pendingDeepLink = deepLink;
      return;
    }

    const { screen, params } = deepLink;

    // Mapeo de screens a rutas de navegación
    const screenMap: Record<string, string> = {
      company: 'CompanyDetail',
      verify: 'Verify',
      network: 'Network',
      alerts: 'Alerts',
      profile: 'Profile',
      scan: 'Scan',
      login: 'Login',
    };

    const targetScreen = screenMap[screen] || screen;

    try {
      this.navigationRef.navigate(targetScreen, params);
    } catch (error) {
      console.error('Deep link navigation error:', error);
      // Fallback a pantalla principal
      this.navigationRef.navigate('Network');
    }
  }

  /**
   * Genera una URL de deep link para compartir
   */
  generateUrl(screen: string, params?: Record<string, string>): string {
    const baseUrl = `conflictzero://${screen}`;
    
    if (!params || Object.keys(params).length === 0) {
      return baseUrl;
    }

    const queryParams = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      queryParams.append(key, value);
    });

    return `${baseUrl}?${queryParams.toString()}`;
  }

  /**
   * Limpia el pending deep link
   */
  clearPending() {
    this.pendingDeepLink = null;
  }
}

export const deepLinkingService = new DeepLinkingService();
export default deepLinkingService;
