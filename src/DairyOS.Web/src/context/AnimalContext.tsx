import React, { createContext, useContext, useState, useCallback, ReactNode } from 'react';
import { apiUrl } from '../config/api';

interface TimelineEvent {
  id: string;
  category: string;
  status?: string;
  severity?: string;
  date?: string;
  title?: string;
  details?: string;
  [key: string]: any;
}

interface AnimalContextValue {
  selectedAnimalId: string | null;
  setSelectedAnimalId: (id: string | null) => void;
  animalTimeline: TimelineEvent[];
  isLoadingTimeline: boolean;
  refreshTimeline: () => void;
}

const AnimalContext = createContext<AnimalContextValue | null>(null);

export function AnimalProvider({ children }: { children: ReactNode }) {
  const [selectedAnimalId, setSelectedAnimalId] = useState<string | null>(null);
  const [animalTimeline, setAnimalTimeline] = useState<TimelineEvent[]>([]);
  const [isLoadingTimeline, setIsLoadingTimeline] = useState(false);

  const refreshTimeline = useCallback(() => {
    if (!selectedAnimalId) {
      setAnimalTimeline([]);
      return;
    }
    setIsLoadingTimeline(true);
    fetch(apiUrl(`/api/v2/animals/${encodeURIComponent(selectedAnimalId)}/timeline`))
      .then(r => (r.ok ? r.json() : { events: [] }))
      .then(data => {
        const events = Array.isArray(data?.events) ? data.events : Array.isArray(data) ? data : [];
        setAnimalTimeline(events);
      })
      .catch(() => setAnimalTimeline([]))
      .finally(() => setIsLoadingTimeline(false));
  }, [selectedAnimalId]);

  return (
    <AnimalContext.Provider
      value={{
        selectedAnimalId,
        setSelectedAnimalId,
        animalTimeline,
        isLoadingTimeline,
        refreshTimeline,
      }}
    >
      {children}
    </AnimalContext.Provider>
  );
}

// Alias so both names work (App.tsx may import either)
export const AnimalContextProvider = AnimalProvider;

export function useAnimalContext(): AnimalContextValue {
  const ctx = useContext(AnimalContext);
  if (!ctx) {
    return {
      selectedAnimalId: null,
      setSelectedAnimalId: () => {},
      animalTimeline: [],
      isLoadingTimeline: false,
      refreshTimeline: () => {},
    };
  }
  return ctx;
}