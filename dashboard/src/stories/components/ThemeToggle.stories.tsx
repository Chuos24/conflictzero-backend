// @ts-nocheck
import ThemeToggle from '../src/components/ThemeToggle'
import { ThemeProvider } from '../src/context/ThemeContext'

/**
 * ThemeToggle - Botón para cambiar entre modo claro y oscuro
 */
export default {
  title: 'Components/ThemeToggle',
  component: ThemeToggle,
  tags: ['autodocs'],
  decorators: [
    (Story) => (
      <ThemeProvider>
        <Story />
      </ThemeProvider>
    ),
  ],
}

export const Default = {
  args: {},
}
