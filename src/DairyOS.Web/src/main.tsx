import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import { AlertAuditProvider } from './context/AlertAuditContext';
import { installAuthenticatedFetch } from './auth';

installAuthenticatedFetch();

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <AlertAuditProvider>
      <App />
    </AlertAuditProvider>
  </React.StrictMode>,
);
