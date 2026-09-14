import { useCallback, useEffect, useRef, useState } from 'react';

export const SYSTEM_TIMEZONE = 'SYSTEM';

export const setFarmTimezone = (_timezone?: string | null) => {
  // Compatibility no-op. DairyOS operational date/time always follows the
  // host browser/Windows local clock and does not maintain an independent
  // timezone override.
};

export const getFarmTimezone = () => SYSTEM_TIMEZONE;

const localDateOptions = (): Intl.DateTimeFormatOptions => ({
  year: 'numeric',
  month: '2-digit',
  day: '2-digit',
});

export const formatFarmDate = (value: Date) =>
  new Intl.DateTimeFormat(
    'en-CA',
    localDateOptions(),
  ).format(value);

export const formatFarmDateTime = (value: Date) =>
  new Intl.DateTimeFormat('en-PK', {
    dateStyle: 'full',
    timeStyle: 'medium',
  }).format(value);

export const farmToday = () =>
  formatFarmDate(new Date());

export const shiftFarmDate = (iso: string, days: number) => {
  const [year, month, day] = iso.split('-').map(Number);
  const value = new Date(
    Date.UTC(year, month - 1, day + days, 12),
  );
  return value.toISOString().slice(0, 10);
};

export const useFarmDateField = () => {
  const initial = farmToday();
  const [value, setValue] = useState(initial);
  const lastAutomaticDate = useRef(initial);

  useEffect(() => {
    const sync = () => {
      const next = farmToday();
      if (next === lastAutomaticDate.current) return;

      const previousAutomatic =
        lastAutomaticDate.current;

      lastAutomaticDate.current = next;

      setValue(current =>
        current === previousAutomatic
          ? next
          : current,
      );
    };

    sync();

    const timer =
      window.setInterval(sync, 60_000);

    return () => {
      window.clearInterval(timer);
    };
  }, []);

  const resetToToday = useCallback(() => {
    const next = farmToday();
    lastAutomaticDate.current = next;
    setValue(next);
  }, []);

  return [value, setValue, resetToToday] as const;
};