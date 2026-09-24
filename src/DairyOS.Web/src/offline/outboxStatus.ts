import { useEffect, useState } from 'react';
import { OUTBOX_CHANGED, listPendingMutations } from './outbox';
import type { QueuedMutation } from './outbox';

export function usePendingMutations(): QueuedMutation[] {
  const [items, setItems] = useState<QueuedMutation[]>([]);
  useEffect(() => {
    const refresh = () => { void listPendingMutations().then(setItems).catch((error) => {
      console.error('DairyOS could not inspect locally stored unsent entries:', error);
    }); };
    refresh();
    window.addEventListener(OUTBOX_CHANGED, refresh);
    return () => window.removeEventListener(OUTBOX_CHANGED, refresh);
  }, []);
  return items;
}
