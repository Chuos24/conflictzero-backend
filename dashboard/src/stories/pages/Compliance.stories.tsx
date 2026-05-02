// @ts-nocheck
import { PageWrapper } from '../PageWrapper'
import Compliance from '../src/pages/Compliance'

/**
 * Compliance Page - Cumplimiento normativo
 */
export default {
  title: 'Pages/Compliance',
  component: Compliance,
  parameters: {
    layout: 'fullscreen',
    docs: {
      description: {
        component: 'Página de compliance y cumplimiento normativo para el programa Founder.',
      },
    },
  },
}

export const Default = {
  render: () => (
    <PageWrapper initialEntry="/compliance">
      <Compliance />
    </PageWrapper>
  ),
}
