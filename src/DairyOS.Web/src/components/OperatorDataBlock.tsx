import React from 'react';

type Props = {
  value: unknown;
};

const HIDDEN_KEYS = new Set([
  'source',
  'source_detail',
  'payload',
  'entity_type',
  'entity_id',
  'record_id',
  'history_id',
  'source_event_id',
  'source_decision_id',
  'frontend_calculation_authority',
  'synthetic_values',
  'data_status',
]);

const IDENTIFIER_KEYS = new Set([
  'animal_id',
  'legacy_animal_id',
  'dam_id',
  'sire_id',
  'ear_tag',
  'rfid',
]);

const LABELS: Record<string, string> = {
  animal_id: 'Animal ID',
  animal_type: 'Animal type',
  ear_tag: 'Ear tag',
  rfid: 'RFID tag',
  breed: 'Breed',
  sex: 'Sex',
  date_of_birth: 'Date of birth',
  dam_id: 'Mother',
  sire_id: 'Father',
  lifecycle_status: 'Life stage',
  status: 'Status',
  is_currently_milking: 'Currently milking',
  milking_frequency: 'Milking frequency',
  production_group: 'Production group',
  location: 'Location',
  active: 'Active',
  non_milking_directive: 'Milking directive',
  non_milking_reason: 'Reason',
  non_milking_since: 'Not milking since',
  non_milking_until: 'Not milking until',
  lactation_count: 'Lactations',
  lifetime_milk_liters: 'Lifetime milk',
  recorded_milk_days: 'Recorded milk days',
  average_liters_per_recorded_day: 'Average milk per recorded day',
  peak_daily_yield_liters: 'Peak daily yield',
  peak_daily_yield_date: 'Peak yield date',
  latest_milk_date: 'Latest milk date',
  daily_totals_considered: 'Daily totals considered',
  current_status: 'Current reproductive status',
  current_api_status: 'Current status',
  pregnancy_status: 'Pregnancy status',
  lactation_number: 'Lactation number',
  days_in_milk: 'Days in milk',
  last_calving_date: 'Last calving date',
  last_insemination_date: 'Last insemination',
  pregnancy_confirmed_date: 'Pregnancy confirmed',
  expected_calving_date: 'Expected calving',
  eligible_to_breed: 'Eligible for breeding',
  days_open: 'Days open',
  expected_dry_off_date: 'Expected dry-off',
  dry_period_status: 'Dry-period status',
  lifetime_calvings: 'Lifetime calvings',
  lifetime_inseminations: 'Lifetime inseminations',
  pregnancy_confirmations: 'Pregnancy confirmations',
  pregnancy_losses_or_negative_checks: 'Pregnancy losses or negative checks',
  dry_off_events: 'Dry-off events',
  open_case_count: 'Open health cases',
  observation_count: 'Health observations',
  treatment_count: 'Treatments',
  active_withdrawal: 'Milk withdrawal active',
  latest_observation_date: 'Latest observation date',
  latest_observation: 'Latest observation',
  broken_parent_links: 'Broken parent links',
  ancestor_cycles: 'Ancestor cycles',
  descendant_cycles: 'Descendant cycles',
  max_depth: 'Maximum lineage depth',
  known_ancestor_count: 'Known ancestors',
  known_descendant_count: 'Known descendants',
  operational_events: 'Recorded operational events',
  lineage_descendants: 'Linked offspring',
  created_at: 'Recorded on',
  updated_at: 'Last updated',
  administered_date: 'Administered on',
  veterinarian: 'Veterinarian',
  dose: 'Dose',
  vaccine: 'Vaccine',
  medicine: 'Medicine',
  diagnosis: 'Diagnosis',
  milk_withdrawal_days: 'Milk withdrawal period',
  effective_date: 'Effective date',
  buyer_or_counterparty: 'Buyer or counterparty',
  amount: 'Amount',
  reference: 'Reference',
  notes: 'Notes',
};

function labelFor(key: string): string {
  return LABELS[key]
    || key
      .replace(/_/g, ' ')
      .replace(/\b\w/g, char => char.toUpperCase());
}

function formatDate(value: unknown): string {
  const parsed = new Date(String(value));
  if (Number.isNaN(parsed.getTime())) return String(value);
  return parsed.toLocaleString('en-PK', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: undefined,
    minute: undefined,
  });
}

function formatEnum(value: string): string {
  const normalized = value.trim();

  const replacements: Record<string, string> = {
    NONE: 'None',
    ACTIVE: 'Active',
    INACTIVE: 'Inactive',
    HEIFER: 'Heifer',
    LACTATING: 'Milking',
    DRY: 'Dry',
    CALF: 'Calf',
    FEMALE: 'Female',
    MALE: 'Male',
    OPEN: 'Open',
    NOT_PREGNANT: 'Not pregnant',
    PREGNANT: 'Pregnant',
    NOT_PLANNED: 'Not planned',
    TWICE_DAILY: 'Twice daily',
    THREE_TIMES_DAILY: 'Three times daily',
    NON_MILKING: 'Not milking',
  };

  return replacements[normalized]
    || normalized
      .toLowerCase()
      .replace(/_/g, ' ')
      .replace(/\b\w/g, char => char.toUpperCase());
}

function friendlyText(value: string): string {
  const text = value.trim();

  if (!text) return '';

  if (
    /entity_type\s*=|entity_id\s*=|payload\s*=|^\w+\s+entity_type=/i.test(text)
  ) {
    const eventName = text
      .split(/\s+entity_type\s*=/i)[0]
      .trim()
      .toLowerCase();

    const messages: Record<string, string> = {
      animal_created: 'Animal registered in the herd register.',
      animal_updated: 'Animal record updated.',
      animal_activated: 'Animal record activated.',
      animal_deactivated: 'Animal record made inactive.',
      animal_disposition_changed: 'Animal status updated.',
    };

    return messages[eventName]
      || `${eventName
        .replace(/_/g, ' ')
        .replace(/\b\w/g, char => char.toUpperCase())}.`;
  }

  return formatEnum(text);
}

function primitive(value: unknown, key?: string): React.ReactNode {
  if (value === null || value === undefined || value === '') {
    return null;
  }

  if (typeof value === 'boolean') {
    return <span>{value ? 'Yes' : 'No'}</span>;
  }

  if (typeof value === 'number') {
    return <span>{value.toLocaleString('en-PK')}</span>;
  }

  if (key && IDENTIFIER_KEYS.has(key)) {
    return <span>{String(value)}</span>;
  }

  if (key === 'created_at' || key === 'updated_at' || key?.endsWith('_date')) {
    return <span>{formatDate(value)}</span>;
  }

  if (key === 'description') {
    return <span>{friendlyText(String(value))}</span>;
  }

  return <span>{friendlyText(String(value))}</span>;
}

function emptyMessage(): React.ReactNode {
  return null;
}

function renderValue(value: unknown, depth = 0, key?: string): React.ReactNode {
  if (value === null || value === undefined || value === '') {
    return emptyMessage();
  }

  if (typeof value !== 'object') {
    return primitive(value, key);
  }

  if (Array.isArray(value)) {
    if (value.length === 0) return emptyMessage();

    return (
      <div style={{ display: 'grid', gap: 7 }}>
        {value.map((item, index) => (
          <div
            key={`${key || 'record'}-${index}`}
            style={{
              background: '#0f172a',
              border: '1px solid #1f2937',
              borderRadius: 5,
              padding: 8,
            }}
          >
            <div
              style={{
                fontSize: 9,
                color: '#64748b',
                marginBottom: 4,
              }}
            >
              Record {index + 1}
            </div>
            {renderValue(item, depth + 1, key)}
          </div>
        ))}
      </div>
    );
  }

  const entries = Object.entries(value).filter(
    ([entryKey]) => !HIDDEN_KEYS.has(entryKey),
  );

  if (entries.length === 0) {
    return emptyMessage();
  }

  return (
    <div
      style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(2,minmax(0,1fr))',
        gap: 7,
      }}
    >
      {entries.map(([entryKey, entryValue]) => (
        <div
          key={entryKey}
          style={{
            background: depth ? '#0f172a' : '#111827',
            border: '1px solid #1f2937',
            borderRadius: 5,
            padding: 8,
            minWidth: 0,
          }}
        >
          <div
            style={{
              fontSize: 9,
              color: '#64748b',
              fontWeight: 800,
              textTransform: 'uppercase',
              marginBottom: 4,
            }}
          >
            {labelFor(entryKey)}
          </div>

          <div
            style={{
              fontSize: 11,
              color: '#e2e8f0',
              overflowWrap: 'anywhere',
              lineHeight: 1.35,
            }}
          >
            {renderValue(entryValue, depth + 1, entryKey)}
          </div>
        </div>
      ))}
    </div>
  );
}

export default function OperatorDataBlock({ value }: Props) {
  return <>{renderValue(value)}</>;
}
