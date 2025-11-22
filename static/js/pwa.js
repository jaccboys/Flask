// PWA Installation and Service Worker Registration

let deferredPrompt;
const installButton = document.getElementById('install-button');

// Register service worker
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/static/sw.js')
      .then((registration) => {
        console.log('Service Worker registered successfully:', registration.scope);
        
        // Check for updates periodically
        setInterval(() => {
          registration.update();
        }, 60000); // Check every minute
      })
      .catch((error) => {
        console.error('Service Worker registration failed:', error);
      });
  });
}

// Listen for beforeinstallprompt event
window.addEventListener('beforeinstallprompt', (e) => {
  console.log('beforeinstallprompt event fired');
  e.preventDefault();
  deferredPrompt = e;
  
  // Show install button if it exists
  if (installButton) {
    installButton.style.display = 'inline-block';
  }
});

// Handle install button click
if (installButton) {
  installButton.addEventListener('click', async () => {
    if (!deferredPrompt) {
      return;
    }
    
    deferredPrompt.prompt();
    const { outcome } = await deferredPrompt.userChoice;
    console.log(`User response to install prompt: ${outcome}`);
    
    deferredPrompt = null;
    installButton.style.display = 'none';
  });
}

// Detect if app is installed
window.addEventListener('appinstalled', () => {
  console.log('PWA installed successfully');
  if (installButton) {
    installButton.style.display = 'none';
  }
});

// Check if running as PWA
function isPWA() {
  return window.matchMedia('(display-mode: standalone)').matches ||
         window.navigator.standalone === true;
}

// Add PWA-specific styling
if (isPWA()) {
  document.body.classList.add('pwa-mode');
}

// Network status monitoring
window.addEventListener('online', () => {
  console.log('Back online');
  document.body.classList.remove('offline');
  showNotification('Connection restored', 'success');
});

window.addEventListener('offline', () => {
  console.log('Gone offline');
  document.body.classList.add('offline');
  showNotification('You are offline. Some features may be limited.', 'warning');
});

// Simple notification helper
function showNotification(message, type = 'info') {
  const notification = document.createElement('div');
  notification.className = `pwa-notification pwa-notification-${type}`;
  notification.textContent = message;
  notification.style.cssText = `
    position: fixed;
    top: 80px;
    right: 20px;
    padding: 15px 20px;
    background: ${type === 'success' ? '#4caf50' : type === 'warning' ? '#ff9800' : '#2196f3'};
    color: white;
    border-radius: 8px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.3);
    z-index: 10000;
    animation: slideIn 0.3s ease;
  `;
  
  document.body.appendChild(notification);
  
  setTimeout(() => {
    notification.style.animation = 'slideOut 0.3s ease';
    setTimeout(() => notification.remove(), 300);
  }, 3000);
}

// Add CSS for notifications
const style = document.createElement('style');
style.textContent = `
  @keyframes slideIn {
    from {
      transform: translateX(400px);
      opacity: 0;
    }
    to {
      transform: translateX(0);
      opacity: 1;
    }
  }
  
  @keyframes slideOut {
    from {
      transform: translateX(0);
      opacity: 1;
    }
    to {
      transform: translateX(400px);
      opacity: 0;
    }
  }
  
  .offline .nav {
    border-bottom: 2px solid #ff9800;
  }
  
  .pwa-mode {
    padding-top: env(safe-area-inset-top);
    padding-bottom: env(safe-area-inset-bottom);
  }
`;
document.head.appendChild(style);