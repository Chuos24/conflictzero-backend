// Conflict Zero - Landing Page Scripts

document.addEventListener('DOMContentLoaded', function() {
  // Initialize all components
  initSmoothScroll();
  initNavbar();
  initAnimations();
  initCounters();
  initMobileMenu();
});

// Smooth scroll for anchor links
function initSmoothScroll() {
  document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function(e) {
      e.preventDefault();
      const target = document.querySelector(this.getAttribute('href'));
      if (target) {
        const offset = 80; // Account for fixed navbar
        const targetPosition = target.getBoundingClientRect().top + window.pageYOffset - offset;
        window.scrollTo({
          top: targetPosition,
          behavior: 'smooth'
        });
      }
    });
  });
}

// Navbar scroll effect
function initNavbar() {
  const navbar = document.querySelector('.navbar');
  let lastScroll = 0;
  
  window.addEventListener('scroll', () => {
    const currentScroll = window.pageYOffset;
    
    // Add/remove scrolled class for background
    if (currentScroll > 50) {
      navbar.style.background = 'rgba(15, 23, 42, 0.98)';
    } else {
      navbar.style.background = 'rgba(15, 23, 42, 0.95)';
    }
    
    // Hide/show on scroll direction
    if (currentScroll > lastScroll && currentScroll > 100) {
      navbar.style.transform = 'translateY(-100%)';
    } else {
      navbar.style.transform = 'translateY(0)';
    }
    
    lastScroll = currentScroll;
  });
  
  // Smooth transition for navbar
  navbar.style.transition = 'transform 0.3s ease, background 0.3s ease';
}

// Intersection Observer for animations
function initAnimations() {
  const observerOptions = {
    root: null,
    rootMargin: '0px',
    threshold: 0.1
  };
  
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('animate-in');
        observer.unobserve(entry.target);
      }
    });
  }, observerOptions);
  
  // Observe elements for animation
  document.querySelectorAll('.feature-card, .pricing-card, .step').forEach(el => {
    el.style.opacity = '0';
    el.style.transform = 'translateY(30px)';
    el.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
    observer.observe(el);
  });
}

// Add animation class styles dynamically
const style = document.createElement('style');
style.textContent = `
  .animate-in {
    opacity: 1 !important;
    transform: translateY(0) !important;
  }
`;
document.head.appendChild(style);

// Animated counters for stats
function initCounters() {
  const counters = document.querySelectorAll('.stat-value');
  
  const counterObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        const target = entry.target;
        const value = target.textContent;
        animateCounter(target, value);
        counterObserver.unobserve(target);
      }
    });
  }, { threshold: 0.5 });
  
  counters.forEach(counter => counterObserver.observe(counter));
}

function animateCounter(element, finalValue) {
  // Extract number and suffix
  const numMatch = finalValue.match(/([0-9,.]+)(.*)/);
  if (!numMatch) return;
  
  const finalNum = parseFloat(numMatch[1].replace(/,/g, ''));
  const suffix = numMatch[2];
  const duration = 2000;
  const start = 0;
  const startTime = performance.now();
  
  function updateCounter(currentTime) {
    const elapsed = currentTime - startTime;
    const progress = Math.min(elapsed / duration, 1);
    
    // Easing function
    const easeOutQuart = 1 - Math.pow(1 - progress, 4);
    const current = start + (finalNum - start) * easeOutQuart;
    
    // Format number
    if (finalNum >= 1000000) {
      element.textContent = (current / 1000000).toFixed(1) + 'M+' + suffix;
    } else if (finalNum >= 1000) {
      element.textContent = Math.floor(current).toLocaleString() + '+' + suffix;
    } else {
      element.textContent = Math.floor(current) + suffix;
    }
    
    if (progress < 1) {
      requestAnimationFrame(updateCounter);
    } else {
      element.textContent = finalValue;
    }
  }
  
  requestAnimationFrame(updateCounter);
}

// Mobile menu toggle
function initMobileMenu() {
  // Create mobile menu button
  const navbarContent = document.querySelector('.navbar-content');
  const mobileBtn = document.createElement('button');
  mobileBtn.className = 'mobile-menu-btn';
  mobileBtn.innerHTML = '☰';
  mobileBtn.style.cssText = `
    display: none;
    background: none;
    border: none;
    color: var(--text-primary);
    font-size: 24px;
    cursor: pointer;
    padding: 8px;
  `;
  
  // Insert before nav-links
  const navLinks = document.querySelector('.nav-links');
  if (navLinks) {
    navbarContent.insertBefore(mobileBtn, navLinks);
  }
  
  // Toggle menu
  let isOpen = false;
  mobileBtn.addEventListener('click', () => {
    isOpen = !isOpen;
    navLinks.style.display = isOpen ? 'flex' : 'none';
    navLinks.style.position = 'absolute';
    navLinks.style.top = '72px';
    navLinks.style.left = '0';
    navLinks.style.right = '0';
    navLinks.style.flexDirection = 'column';
    navLinks.style.background = 'var(--bg-card)';
    navLinks.style.padding = '24px';
    navLinks.style.gap = '16px';
    navLinks.style.borderBottom = '1px solid var(--border)';
    mobileBtn.innerHTML = isOpen ? '✕' : '☰';
  });
  
  // Show mobile button on small screens
  const mediaQuery = window.matchMedia('(max-width: 768px)');
  function handleMediaChange(e) {
    if (e.matches) {
      mobileBtn.style.display = 'block';
      navLinks.style.display = 'none';
    } else {
      mobileBtn.style.display = 'none';
      navLinks.style.display = 'flex';
      navLinks.style.position = '';
      navLinks.style.top = '';
      navLinks.style.left = '';
      navLinks.style.right = '';
      navLinks.style.flexDirection = '';
      navLinks.style.background = '';
      navLinks.style.padding = '';
      navLinks.style.gap = '';
      navLinks.style.borderBottom = '';
    }
  }
  mediaQuery.addListener(handleMediaChange);
  handleMediaChange(mediaQuery);
}

// Utility: Throttle function
function throttle(func, limit) {
  let inThrottle;
  return function(...args) {
    if (!inThrottle) {
      func.apply(this, args);
      inThrottle = true;
      setTimeout(() => inThrottle = false, limit);
    }
  };
}

// Utility: Debounce function
function debounce(func, wait) {
  let timeout;
  return function(...args) {
    clearTimeout(timeout);
    timeout = setTimeout(() => func.apply(this, args), wait);
  };
}

// Newsletter form handling
document.addEventListener('DOMContentLoaded', function() {
  const newsletterForms = document.querySelectorAll('.newsletter-form');
  
  newsletterForms.forEach(form => {
    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      const email = form.querySelector('input[type="email"]').value;
      const button = form.querySelector('button');
      const originalText = button.textContent;
      
      // Validate email
      if (!isValidEmail(email)) {
        showToast('Por favor ingresa un email válido', 'error');
        return;
      }
      
      // Simulate API call
      button.disabled = true;
      button.textContent = 'Enviando...';
      
      try {
        // In production, this would be an actual API call
        await new Promise(resolve => setTimeout(resolve, 1500));
        showToast('¡Gracias por suscribirte!', 'success');
        form.reset();
      } catch (error) {
        showToast('Error al suscribirse. Intenta de nuevo.', 'error');
      } finally {
        button.disabled = false;
        button.textContent = originalText;
      }
    });
  });
});

function isValidEmail(email) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
}

// Toast notification system
function showToast(message, type = 'info') {
  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  toast.textContent = message;
  toast.style.cssText = `
    position: fixed;
    bottom: 24px;
    right: 24px;
    padding: 16px 24px;
    border-radius: 8px;
    color: white;
    font-weight: 500;
    z-index: 9999;
    transform: translateX(100%);
    transition: transform 0.3s ease;
  `;
  
  // Set color based on type
  const colors = {
    success: '#10b981',
    error: '#ef4444',
    warning: '#f59e0b',
    info: '#2563eb'
  };
  toast.style.background = colors[type] || colors.info;
  
  document.body.appendChild(toast);
  
  // Animate in
  requestAnimationFrame(() => {
    toast.style.transform = 'translateX(0)';
  });
  
  // Remove after delay
  setTimeout(() => {
    toast.style.transform = 'translateX(100%)';
    setTimeout(() => toast.remove(), 300);
  }, 4000);
}

// Pricing toggle (monthly/yearly)
document.addEventListener('DOMContentLoaded', function() {
  const pricingToggle = document.querySelector('.pricing-toggle');
  if (pricingToggle) {
    const monthlyPrices = document.querySelectorAll('.price-monthly');
    const yearlyPrices = document.querySelectorAll('.price-yearly');
    
    pricingToggle.addEventListener('change', (e) => {
      const isYearly = e.target.checked;
      
      monthlyPrices.forEach(price => {
        price.style.display = isYearly ? 'none' : 'block';
      });
      
      yearlyPrices.forEach(price => {
        price.style.display = isYearly ? 'block' : 'none';
      });
    });
  }
});

// Feature cards hover effect enhancement
document.addEventListener('DOMContentLoaded', function() {
  const cards = document.querySelectorAll('.feature-card');
  
  cards.forEach(card => {
    card.addEventListener('mouseenter', function() {
      this.style.boxShadow = '0 20px 40px rgba(37, 99, 235, 0.15)';
    });
    
    card.addEventListener('mouseleave', function() {
      this.style.boxShadow = '';
    });
  });
});

// Parallax effect for hero section
window.addEventListener('scroll', throttle(() => {
  const hero = document.querySelector('.hero');
  const scrolled = window.pageYOffset;
  const rate = scrolled * 0.3;
  
  if (hero && scrolled < window.innerHeight) {
    hero.style.backgroundPositionY = `${rate}px`;
  }
}, 16));

// Easter egg: Konami code
let konamiCode = [];
const konamiSequence = ['ArrowUp', 'ArrowUp', 'ArrowDown', 'ArrowDown', 'ArrowLeft', 'ArrowRight', 'ArrowLeft', 'ArrowRight', 'b', 'a'];

document.addEventListener('keydown', (e) => {
  konamiCode.push(e.key);
  konamiCode = konamiCode.slice(-10);
  
  if (konamiCode.join(',') === konamiSequence.join(',')) {
    activateEasterEgg();
  }
});

function activateEasterEgg() {
  document.body.style.animation = 'rainbow 2s linear infinite';
  
  const style = document.createElement('style');
  style.textContent = `
    @keyframes rainbow {
      0% { filter: hue-rotate(0deg); }
      100% { filter: hue-rotate(360deg); }
    }
  `;
  document.head.appendChild(style);
  
  showToast('🎮 ¡Modo desarrollador activado!', 'success');
  
  setTimeout(() => {
    document.body.style.animation = '';
  }, 5000);
}

// Performance monitoring
if ('performance' in window) {
  window.addEventListener('load', () => {
    setTimeout(() => {
      const perfData = performance.getEntriesByType('navigation')[0];
      if (perfData) {
        console.log(`⚡ Page load time: ${Math.round(perfData.loadEventEnd - perfData.startTime)}ms`);
      }
    }, 0);
  });
}

// Export utilities for global access
window.ConflictZero = {
  showToast,
  throttle,
  debounce,
  isValidEmail
};
