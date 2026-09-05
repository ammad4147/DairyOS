import { useCallback, useEffect, useRef, useState } from 'react';

const farmDateFormatter = new Intl.DateTimeFormat('en-CA', {
  timeZone: 'Asia/Karachi',
  year: 'numeric',
  month: '2-digit',
  day: '2-digit',
});

export const farmToday = () => farmDateFormatter.format(new Date());

export const useFarmDateField = () => {
  const initial = farmToday();
  const [value, setValue] = useState(initial);
  const lastAutomaticDate = useRef(initial);

  useEffect(() => {
    const sync = () => {
      const next = farmToday();
      if (next === lastAutomaticDate.current) return;
      const previousAutomatic = lastAutomaticDate.current;
      lastAutomaticDate.current = next;
      setValue(current => current === previousAutomatic ? next : current);
    };

    sync();
    const timer = window.setInterval(sync, 60_000);
    return () => window.clearInterval(timer);
  }, []);

  const resetToToday = useCallback(() => {
    const next = farmToday();
    lastAutomaticDate.current = next;
    setValue(next);
  }, []);

  return [value, setValue, resetToToday] as const;
};
