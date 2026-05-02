// @ts-nocheck
import { PageWrapper } from '../PageWrapper'
import Network from '../src/pages/Network'

/**
 * Network Page - Red de proveedores
 */
export default {
  title: 'Pages/Network',
  component: Network,
  parameters: {
    layout: 'fullscreen',
    docs: {
      description: {
        component: 'Página de red de proveedores (Mi Red) con visualización de conexiones.',
      },
    },
  },
}

export const Default = {
  render: () => (
    <PageWrapper initialEntry="/network">
      <Network />
    </PageWrapper>
  ),
}
