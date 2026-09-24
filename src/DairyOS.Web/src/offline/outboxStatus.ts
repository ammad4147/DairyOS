import { useEffect, useState } from 'react';
import { OUTBOX_CHANGED, pendingMutationCount } from './outbox';

export function usePendingMutationCount(): number {
  const [count, setCount] = useState(0);
  useEffect(() => {
    const refresh = () => { void pendingMutationCount().then(setCount); };
    refresh();
    window.addEventListener(OUTBOX_CHANGED, refresh);
    return () => window.removeEventListener(OUTBOX_CHANGED, refresh);
  }, []);
  return count;
}
