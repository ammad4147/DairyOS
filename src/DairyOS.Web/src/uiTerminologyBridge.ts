const PRODUCTION_COST_LABEL = 'Cost of Production/Liter';

function textNodes(root: Node): Text[] {
  const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
  const nodes: Text[] = [];
  let node: Node | null;
  while ((node = walker.nextNode())) nodes.push(node as Text);
  return nodes;
}

function updateDashboardText() {
  const root = document.querySelector('.cmd-dash-wrapper');
  if (!root) return;

  for (const text of textNodes(root)) {
    const raw = text.nodeValue ?? '';
    if (!raw.trim()) continue;

    let value = raw;
    if (value.includes('COML')) {
      value = value.replaceAll('COML', PRODUCTION_COST_LABEL);
    }
    value = value.replace(
      `${PRODUCTION_COST_LABEL} · `,
      `${PRODUCTION_COST_LABEL} (`
    );
    if (value.endsWith('Current Month)')) {
      value = '';
    }

    if (value !== raw) text.nodeValue = value;
  }

  const costCard = Array.from(root.querySelectorAll<HTMLElement>('div')).find((element) => {
    const text = element.textContent?.trim() ?? '';
    return text.includes('No official Cost of Production/Liter');
  });
  if (costCard) costCard.textContent = '';

  const dropRows = Array.from(root.querySelectorAll<HTMLElement>('div')).filter(
    (element) => element.textContent?.trim() === 'Drop'
  );
  for (const row of dropRows) {
    const parent = row.parentElement;
    const grandparent = parent?.parentElement;
    const context = grandparent?.textContent ?? parent?.textContent ?? '';
    if (context.includes('#TD-004')) row.textContent = '32% Drop';
    else if (context.includes('#TD-003')) row.textContent = '23% Drop';
  }
}

function installDashboardContainment() {
  const styleId = 'dairyos-dashboard-refinement-style';
  if (document.getElementById(styleId)) return;

  const style = document.createElement('style');
  style.id = styleId;
  style.textContent = `
    .cmd-dash-wrapper .cmd-content-grid,
    .cmd-dash-wrapper .cmd-col,
    .cmd-dash-wrapper .cmd-card { min-width: 0; box-sizing: border-box; }
    .cmd-dash-wrapper .cmd-card button { flex: 0 0 auto; min-height: 36px; box-sizing: border-box; }
    .cmd-dash-wrapper .cmd-card { overflow: hidden; }
  `;
  document.head.appendChild(style);
}

export function installUiTerminologyBridge() {
  if (typeof document === 'undefined') return;

  installDashboardContainment();
  updateDashboardText();

  const observer = new MutationObserver(() => updateDashboardText());
  observer.observe(document.body, { childList: true, subtree: true, characterData: true });

  return () => observer.disconnect();
}
