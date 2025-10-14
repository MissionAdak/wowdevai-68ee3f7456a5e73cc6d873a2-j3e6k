export function initializeNavigation() {
  const mobileMenuBtn = document.querySelector('[data-id="mobile-menu-btn"]');
  const mobileMenu = document.querySelector('[data-id="mobile-menu"]');
  
  if (mobileMenuBtn && mobileMenu) {
    mobileMenuBtn.addEventListener('click', () => {
      mobileMenu.classList.toggle('hidden');
      
      const icon = mobileMenuBtn.querySelector('i');
      if (mobileMenu.classList.contains('hidden')) {
        icon.setAttribute('data-lucide', 'menu');
      } else {
        icon.setAttribute('data-lucide', 'x');
      }
      lucide.createIcons();
    });
  }
}