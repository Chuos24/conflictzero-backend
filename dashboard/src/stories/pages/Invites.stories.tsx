// @ts-nocheck
import { PageWrapper } from '../PageWrapper'
import Invites from '../src/pages/Invites'

/**
 * Invites Page - Gestión de invitaciones
 */
export default {
  title: 'Pages/Invites',
  component: Invites,
  parameters: {
    layout: 'fullscreen',
    docs: {
      description: {
        component: 'Página de gestión de invitaciones a proveedores para unirse a la red.',
      },
    },
  },
}

export const Default = {
  render: () => (
    <PageWrapper initialEntry="/invites">
      <Invites />
    </PageWrapper>
  ),
}
