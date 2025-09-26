import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import App from './App';
import { initializeExtensionErrorHandler } from './utils/extensionErrorHandler';

// Initialize extension error handler to suppress browser extension errors
initializeExtensionErrorHandler();

const root = ReactDOM.createRoot(
  document.getElementById('root') as HTMLElement
);
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);