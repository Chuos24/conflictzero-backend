// @ts-nocheck
import { PageWrapper } from '../PageWrapper'
import Monitoring from '../src/pages/Monitoring'

/**
 * Monitoring Page - Monitoreo continuo de proveedores
 */
export default {
  title: 'Pages/Monitoring',
  component: Monitoring,
  parameters: {
    layout: 'fullscreen',
    docs: {
      description: {
        component: 'Página de monitoreo continuo con alertas y estado de proveedores.',
      },
    },
  },
}

export const Default = {
  render: () => (
    <PageWrapper initialEntry="/monitoring">
      <Monitoring />
    </PageWrapper>
  ),
}
