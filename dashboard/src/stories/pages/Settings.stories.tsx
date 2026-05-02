// @ts-nocheck
import { PageWrapper } from '../PageWrapper'
import Settings from '../src/pages/Settings'

/**
 * Settings Page - Configuración de cuenta
 */
export default {
  title: 'Pages/Settings',
  component: Settings,
  parameters: {
    layout: 'fullscreen',
    docs: {
      description: {
        component: 'Página de configuración de cuenta, notificaciones y preferencias.',
      },
    },
  },
}

export const Default = {
  render: () => (
    <PageWrapper initialEntry="/settings">
      <Settings />
    </PageWrapper>
  ),
}
