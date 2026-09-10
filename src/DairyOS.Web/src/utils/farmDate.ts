import { useCallback, useEffect, useRef, useState } from 'react';

export const SYSTEM_TIMEZONE = 'SYSTEM';

let configuredFarmTimezone = SYSTEM_TIMEZONE;
const TIMEZONE_CHANGED_EVENT = 'dairyos-timezone-changed';

export const setFarmTimezone = (timezone?: string | null) => {
  const normalized = String(timezone || SYSTEM_TIMEZONE).trim();
  const next = normalized || SYSTEM_TIMEZONE;
  if (configuredFarmTimezone === next) return;
  configuredFarmTimezone = next;
  if (typeof window !== 'undefined') {
    window.dispatchEvent(new Event(TIMEZONE_CHANGED_EVENT));
  }
};

export const getFarmTimezone = () => configuredFarmTimezone;

const formatterOptions = (): Intl.DateTimeFormatOptions => {
  const options: Intl.DateTimeFormatOptions = {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
  };
  if (configuredFarmTimezone !== SYSTEM_TIMEZONE) {
    options.timeZone = configuredFarmTimezone;
  }
  return options;
};

export const formatFarmDate = (value: Date) => {
  try {
    return new Intl.DateTimeFormat('en-CA', formatterOptions()).format(value);
  } catch {
    // A stale or unavailable override must never stop date entry. The
    // browser/Windows local clock remains the safe fallback.
    return new Intl.DateTimeFormat('en-CA', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
    }).format(value);
  }
};

export const formatFarmDateTime = (value: Date) => {
  const options: Intl.DateTimeFormatOptions = {
    dateStyle: 'full',
    timeStyle: 'medium',
  };
  if (configuredFarmTimezone !== SYSTEM_TIMEZONE) {
    options.timeZone = configuredFarmTimezone;
  }
  try {
    return new Intl.DateTimeFormat('en-PK', options).format(value);
  } catch {
    delete options.timeZone;
    return new Intl.DateTimeFormat('en-PK', options).format(value);
  }
};

export const farmToday = () => formatFarmDate(new Date());

export const shiftFarmDate = (iso: string, days: number) => {
  const [year, month, day] = iso.split('-').map(Number);
  const value = new Date(Date.UTC(year, month - 1, day + days, 12));
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
      const previousAutomatic = lastAutomaticDate.current;
      lastAutomaticDate.current = next;
      setValue(current => current === previousAutomatic ? next : current);
    };

    sync();
    const timer = window.setInterval(sync, 60_000);
    window.addEventListener(TIMEZONE_CHANGED_EVENT, sync);
    return () => {
      window.clearInterval(timer);
      window.removeEventListener(TIMEZONE_CHANGED_EVENT, sync);
    };
  }, []);

  const resetToToday = useCallback(() => {
    const next = farmToday();
    lastAutomaticDate.current = next;
    setValue(next);
  }, []);

  return [value, setValue, resetToToday] as const;
};
