import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import { AnimalProvider } from './context/AnimalContext';
import { AlertAuditProvider } from './context/AlertAuditContext';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <AlertAuditProvider>
      <AnimalProvider>
        <App />
      </AnimalProvider>
    </AlertAuditProvider>
  </React.StrictMode>,
);
