import React from 'react';
import { StatusBar } from 'expo-status-bar';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { NavigationContainer } from '@react-navigation/native';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { createStackNavigator } from '@react-navigation/stack';
import { Ionicons } from '@expo/vector-icons';

import { AuthProvider } from './src/context/AuthContext';
import { ThemeProvider } from './src/context/ThemeContext';
import { VerifyScreen } from './src/screens/VerifyScreen';
import { NetworkScreen } from './src/screens/NetworkScreen';
import { AlertsScreen } from './src/screens/AlertsScreen';
import { ProfileScreen } from './src/screens/ProfileScreen';
import { ScanScreen } from './src/screens/ScanScreen';
import { CompanyDetailScreen } from './src/screens/CompanyDetailScreen';
import { LoginScreen } from './src/screens/LoginScreen';

const Tab = createBottomTabNavigator();
const Stack = createStackNavigator();

function MainTabs() {
  return (
    <Tab.Navigator
      screenOptions={({ route }) => ({
        tabBarIcon: ({ focused, color, size }) => {
          let iconName: string;
          switch (route.name) {
            case 'Verify':
              iconName = focused ? 'search' : 'search-outline';
              break;
            case 'Network':
              iconName = focused ? 'people' : 'people-outline';
              break;
            case 'Scan':
              iconName = focused ? 'scan' : 'scan-outline';
              break;
            case 'Alerts':
              iconName = focused ? 'notifications' : 'notifications-outline';
              break;
            case 'Profile':
              iconName = focused ? 'person' : 'person-outline';
              break;
            default:
              iconName = 'help-outline';
          }
          return <Ionicons name={iconName as any} size={size} color={color} />;
        },
        tabBarActiveTintColor: '#e94560',
        tabBarInactiveTintColor: '#8b9bb4',
        headerShown: false,
      })}
    >
      <Tab.Screen name="Verify" component={VerifyScreen} />
      <Tab.Screen name="Network" component={NetworkScreen} />
      <Tab.Screen name="Scan" component={ScanScreen} />
      <Tab.Screen name="Alerts" component={AlertsScreen} />
      <Tab.Screen name="Profile" component={ProfileScreen} />
    </Tab.Navigator>
  );
}

export default function App() {
  return (
    <SafeAreaProvider>
      <ThemeProvider>
        <AuthProvider>
          <NavigationContainer>
            <Stack.Navigator screenOptions={{ headerShown: false }}>
              <Stack.Screen name="Login" component={LoginScreen} />
              <Stack.Screen name="Main" component={MainTabs} />
              <Stack.Screen 
                name="CompanyDetail" 
                component={CompanyDetailScreen}
                options={{ 
                  headerShown: true,
                  headerStyle: { backgroundColor: '#1a1a2e' },
                  headerTintColor: '#fff',
                  headerTitle: 'Detalle de Empresa'
                }}
              />
            </Stack.Navigator>
          </NavigationContainer>
          <StatusBar style="light" />
        </AuthProvider>
      </ThemeProvider>
    </SafeAreaProvider>
  );
}
