import { useState, useEffect } from 'react'

/**
 * Hook para obtener dimensiones de la ventana
 * Útil para responsive design, breakpoints, ajustes de layout
 * 
 * @returns {Object} { width, height, isMobile, isTablet, isDesktop }
 * 
 * @example
 * const { width, isMobile } = useWindowSize()
 * 
 * return (
 *   <div className={isMobile ? 'mobile-layout' : 'desktop-layout'}>
 *     Width: {width}px
 *   </div>
 * )
 */
export function useWindowSize() {
  const [windowSize, setWindowSize] = useState({
    width: window.innerWidth,
    height: window.innerHeight,
  })

  useEffect(() => {
    const handleResize = () => {
      setWindowSize({
        width: window.innerWidth,
        height: window.innerHeight,
      })
    }

    // Set initial size
    handleResize()

    window.addEventListener('resize', handleResize)

    return () => {
      window.removeEventListener('resize', handleResize)
    }
  }, [])

  // Breakpoint helpers
  const isMobile = windowSize.width < 768
  const isTablet = windowSize.width >= 768 && windowSize.width < 1024
  const isDesktop = windowSize.width >= 1024
  const isWide = windowSize.width >= 1440

  return {
    ...windowSize,
    isMobile,
    isTablet,
    isDesktop,
    isWide,
  }
}

export default useWindowSize
