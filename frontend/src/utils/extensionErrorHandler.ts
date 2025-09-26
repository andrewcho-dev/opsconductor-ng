/**
 * Extension Error Handler
 * Handles and suppresses errors from browser extensions that shouldn't affect the application
 */

// List of known extension-related error patterns to suppress
const EXTENSION_ERROR_PATTERNS = [
  /MetaMask/i,
  /ethereum/i,
  /web3/i,
  /inpage\.js/i,
  /extension.*not found/i,
  /Failed to connect to MetaMask/i
];

// Store original console.error to avoid infinite loops
const originalConsoleError = console.error;

/**
 * Initialize extension error handler
 * This will suppress known extension-related errors from appearing in console
 */
export const initializeExtensionErrorHandler = () => {
  // Override console.error to filter out extension errors
  console.error = (...args: any[]) => {
    const errorMessage = args.join(' ');
    
    // Check if this is a known extension error
    const isExtensionError = EXTENSION_ERROR_PATTERNS.some(pattern => 
      pattern.test(errorMessage)
    );
    
    // Only log non-extension errors
    if (!isExtensionError) {
      originalConsoleError.apply(console, args);
    }
  };

  // Handle unhandled promise rejections from extensions
  window.addEventListener('unhandledrejection', (event) => {
    const errorMessage = event.reason?.message || event.reason?.toString() || '';
    
    // Check if this is a known extension error
    const isExtensionError = EXTENSION_ERROR_PATTERNS.some(pattern => 
      pattern.test(errorMessage)
    );
    
    if (isExtensionError) {
      // Prevent the error from being logged
      event.preventDefault();
    }
  });

  // Handle general errors from extensions
  window.addEventListener('error', (event) => {
    const errorMessage = event.message || '';
    const filename = event.filename || '';
    
    // Check if this is a known extension error
    const isExtensionError = EXTENSION_ERROR_PATTERNS.some(pattern => 
      pattern.test(errorMessage) || pattern.test(filename)
    );
    
    if (isExtensionError) {
      // Prevent the error from being logged
      event.preventDefault();
    }
  });
};

/**
 * Cleanup function to restore original error handling
 */
export const cleanupExtensionErrorHandler = () => {
  console.error = originalConsoleError;
};