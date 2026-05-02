// @ts-nocheck
import { PageWrapper } from '../PageWrapper'
import Compare from '../src/pages/Compare'

/**
 * Compare Page - Comparación de hasta 10 RUCs
 *
 * Referencia: GitHub compare view
 */
export default {
  title: 'Pages/Compare',
  component: Compare,
  parameters: {
    layout: 'fullscreen',
    docs: {
      description: {
        component: 'Página de comparación de proveedores. Permite comparar hasta 10 RUCs simultáneamente.',
      },
    },
  },
}

export const Default = {
  render: () => (
    <PageWrapper initialEntry="/compare">
      <Compare />
    </PageWrapper>
  ),
}
