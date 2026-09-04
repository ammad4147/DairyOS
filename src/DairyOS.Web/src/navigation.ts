export const NAVIGATION_TABS = [
  { id: 'dashboard', label: 'Dashboard' },
  { id: 'animals', label: 'Animals' },
  { id: 'milk', label: 'Milk' },
  { id: 'feed', label: 'Feed' },
  { id: 'finance', label: 'Finance' },
  { id: 'breeding', label: 'Breeding' },
  { id: 'health', label: 'Health' },
  { id: 'vaccination', label: 'Vaccination' },
  { id: 'cop', label: 'COP' },
] as const;

export type NavigationTabId = (typeof NAVIGATION_TABS)[number]['id'];

const NAVIGATION_TAB_IDS = new Set<string>(NAVIGATION_TABS.map(tab => tab.id));

export function normalizeHiddenNavigationTabs(value: unknown): NavigationTabId[] {
  if (!Array.isArray(value)) return [];
  const requested = new Set(value.map(item => String(item)));
  return NAVIGATION_TABS
    .map(tab => tab.id)
    .filter(tabId => requested.has(tabId) && NAVIGATION_TAB_IDS.has(tabId));
}
