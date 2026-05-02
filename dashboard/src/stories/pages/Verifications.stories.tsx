// @ts-nocheck
import { PageWrapper } from '../PageWrapper'
import Verifications from '../src/pages/Verifications'

/**
 * Verifications Page - Historial de verificaciones
 */
export default {
  title: 'Pages/Verifications',
  component: Verifications,
  parameters: {
    layout: 'fullscreen',
    docs: {
      description: {
        component: 'Página de historial de verificaciones con filtros y exportación.',
      },
    },
  },
}

export const Default = {
  render: () => (
    <PageWrapper initialEntry="/verifications">
      <Verifications />
    </PageWrapper>
  ),
}
