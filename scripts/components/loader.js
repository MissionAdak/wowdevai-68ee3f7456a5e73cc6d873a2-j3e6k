export async function loadComponent(selector, filePath = null) {
  const container = document.querySelector(selector);
  if (!container) return;

  const source = filePath || container.dataset.source;
  if (!source) return;

  try {
    const response = await fetch(source);
    const html = await response.text();
    container.innerHTML = html;
    
    // Initialize navigation after loading navbar
    if (source.includes('navbar.html')) {
      const { initializeNavigation } = await import('./navigation.js');
      initializeNavigation();
    }
  } catch (error) {
    console.error('Error loading component:', error);
  }
}