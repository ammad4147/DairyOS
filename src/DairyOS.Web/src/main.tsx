import React from 'react';
import ReactDOM from 'react-dom/client';
import HumanAccessGate from './components/HumanAccessGate';
import { AnimalProvider } from './context/AnimalContext';
import { AlertAuditProvider } from './context/AlertAuditContext';
import { installDesktopSession } from './config/desktopSession';

installDesktopSession();

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <AlertAuditProvider>
      <AnimalProvider>
        <HumanAccessGate />
      </AnimalProvider>
    </AlertAuditProvider>
  </React.StrictMode>,
);
