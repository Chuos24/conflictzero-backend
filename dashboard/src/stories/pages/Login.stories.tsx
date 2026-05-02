// @ts-nocheck
import { PageWrapper } from '../PageWrapper'
import Login from '../src/pages/Login'

/**
 * Login Page - Autenticación de usuarios
 *
 * Referencia: Vercel login page
 */
export default {
  title: 'Pages/Login',
  component: Login,
  parameters: {
    layout: 'fullscreen',
    docs: {
      description: {
        component: 'Página de login con RUC y contraseña. Incluye validación con Zod.',
      },
    },
  },
}

export const Default = {
  render: () => (
    <PageWrapper initialEntry="/login">
      <Login />
    </PageWrapper>
  ),
}
