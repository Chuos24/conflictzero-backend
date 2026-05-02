// @ts-nocheck
import { PageWrapper } from '../PageWrapper'
import Profile from '../src/pages/Profile'

/**
 * Profile Page - Perfil de empresa
 */
export default {
  title: 'Pages/Profile',
  component: Profile,
  parameters: {
    layout: 'fullscreen',
    docs: {
      description: {
        component: 'Página de perfil de empresa con datos de contacto y configuración.',
      },
    },
  },
}

export const Default = {
  render: () => (
    <PageWrapper initialEntry="/profile">
      <Profile />
    </PageWrapper>
  ),
}
