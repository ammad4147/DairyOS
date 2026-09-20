import React, { useEffect, useMemo, useState } from 'react';
import {
  CalendarClock,
  Check,
  CheckCircle2,
  Plus,
  Search,
  ShieldCheck,
  Trash2,
  X,
} from 'lucide-react';
import AnimalPassportModal from './AnimalPassportModal';
import { apiUrl } from '../config/api';
import { postRequest } from '../api/farmEntryClient';
import {
  farmToday,
  formatFarmDate,
  shiftFarmDate,
} from '../utils/farmDate';

interface HerdAnimal {
  id: string;
  category: string;
  breed: string;
  status: string;
}

interface VaccinationOccurrence {
  id: number | null;
  animalId: string;
  vaccine: string;
  dose: string;
  administrator: string;
  scheduledDate: string;
  administeredDate: string;
  category: string;
  scheduleStatus: string;
  status: string;
  sourceEventId: string;
  createdAt: string;
  batchNumber: string;
  notes: string;
}

interface ScheduleDraft {
  vaccine: string;
  dose: string;
  purpose: string;
  administrator: string;
  dates: string[];
}

interface AmendmentDraft {
  vaccine: string;
  dose: string;
  administrator: string;
  scheduledDate: string;
  notes: string;
}

interface Props {
  onOpenPassport?: (id: string) => void;
  herdMasterList?: HerdAnimal[];
  onChanged?: () => void;
}

const VACCINES = [
  'Foot-and-Mouth Disease (FMD)',
  'Hemorrhagic Septicemia (HS)',
  'Black Quarter (BQ)',
  'Lumpy Skin Disease (LSD)',
  'Brucellosis',
  'Anthrax',
  'Bovine Viral Diarrhea (BVD)',
  'IBR / Respiratory complex',
  'Clostridial disease',
  'Calf scours / enteric disease',
  'Other',
];

const field: React.CSSProperties = {
  width: '100%',
  boxSizing: 'border-box',
  background: '#0f172a',
  color: '#fff',
  border: '1px solid #334155',
  padding: '9px 10px',
  borderRadius: 6,
  fontSize: 12,
};

const card: React.CSSProperties = {
  background: '#111827',
  border: '1px solid #1f2937',
  borderRadius: 8,
};

const th: React.CSSProperties = {
  padding: '9px 10px',
  textAlign: 'left',
  fontSize: 10,
  color: '#cbd5e1',
  whiteSpace: 'nowrap',
  verticalAlign: 'top',
};

const td: React.CSSProperties = {
  padding: '9px 10px',
  borderTop: '1px solid #1a2234',
  verticalAlign: 'top',
};

const btn = (background: string): React.CSSProperties => ({
  background,
  color: '#fff',
  border: 0,
  padding: '8px 11px',
  borderRadius: 6,
  fontWeight: 800,
  cursor: 'pointer',
  display: 'inline-flex',
  alignItems: 'center',
  justifyContent: 'center',
  gap: 5,
  fontSize: 11,
});

function dateValue(value: unknown): string {
  if (!value) return '';

  const text = String(value);

  if (/^\d{4}-\d{2}-\d{2}$/.test(text)) {
    return text;
  }

  const parsed = new Date(text);

  return Number.isNaN(parsed.getTime())
    ? text.slice(0, 10)
    : formatFarmDate(parsed);
}

function shortDate(value: string): string {
  if (!value) return '—';

  const parts = value.split('-');

  if (parts.length !== 3) {
    return value;
  }

  const [year, month, day] = parts;
  const monthNumber = Number(month);

  const names = [
    'Jan',
    'Feb',
    'Mar',
    'Apr',
    'May',
    'Jun',
    'Jul',
    'Aug',
    'Sep',
    'Oct',
    'Nov',
    'Dec',
  ];

  if (
    !Number.isInteger(monthNumber) ||
    monthNumber < 1 ||
    monthNumber > 12
  ) {
    return value;
  }

  return `${day}-${names[monthNumber - 1]}-${year.slice(-2)}`;
}

async function api(path: string, body?: unknown) {
  if (body !== undefined) return postRequest(path, body);
  const response = await fetch(
    apiUrl(path),
    body
      ? {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(body),
        }
      : undefined,
  );

  if (!response.ok) {
    let detail = `Request failed: ${response.status}`;

    try {
      const payload = await response.json();

      if (payload?.detail) {
        detail =
          typeof payload.detail === 'string'
            ? payload.detail
            : JSON.stringify(payload.detail);
      }
    } catch {
      // Keep HTTP fallback message.
    }

    throw new Error(detail);
  }

  return response.json();
}

function emptyScheduleDraft(): ScheduleDraft {
  return {
    vaccine: '',
    dose: '',
    purpose: '',
    administrator: '',
    dates: [''],
  };
}

function amendmentDraftFrom(
  row: VaccinationOccurrence,
): AmendmentDraft {
  return {
    vaccine: row.vaccine,
    dose: row.dose,
    administrator: row.administrator,
    scheduledDate: row.scheduledDate,
    notes: row.notes,
  };
}

function occurrenceKey(row: VaccinationOccurrence): string {
  return [
    row.animalId,
    row.vaccine,
    row.id ?? row.sourceEventId ?? row.createdAt,
    row.scheduledDate,
    row.administeredDate,
  ].join('|');
}

export default function VaccinationTab({
  onOpenPassport,
  herdMasterList = [],
  onChanged,
}: Props) {
  const [rows, setRows] =
    useState<VaccinationOccurrence[]>([]);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');
  const [search, setSearch] = useState('');
  const [showSchedule, setShowSchedule] = useState(false);
  const [amending, setAmending] =
    useState<VaccinationOccurrence | null>(null);
  const [amendmentDraft, setAmendmentDraft] =
    useState<AmendmentDraft | null>(null);
  const [showLog, setShowLog] = useState(false);
  const [auditRows, setAuditRows] = useState<any[]>([]);
  const [saving, setSaving] = useState(false);
  const [administeringId, setAdministeringId] =
    useState<number | null>(null);

  const [passport, setPassport] =
    useState<string | null>(null);

  const [animal, setAnimal] = useState('');
  const [scheduleDrafts, setScheduleDrafts] =
    useState<ScheduleDraft[]>([emptyScheduleDraft()]);

  useEffect(() => {
    if (!animal && herdMasterList[0]) {
      setAnimal(herdMasterList[0].id);
    }
  }, [herdMasterList, animal]);

  const load = async () => {
    setLoading(true);
    setError('');

    try {
      const all = await Promise.all(
        herdMasterList.map(async herdAnimal => {
          try {
            const items = await api(
              `/farm/animals/${encodeURIComponent(
                herdAnimal.id,
              )}/vaccinations`,
            );

            return {
              animal: herdAnimal,
              items: Array.isArray(items) ? items : [],
            };
          } catch {
            return {
              animal: herdAnimal,
              items: [],
            };
          }
        }),
      );

      const loaded = all.flatMap(
        ({ animal: herdAnimal, items }) =>
          (items as any[]).map(
            (item): VaccinationOccurrence => ({
              id:
                typeof item.id === 'number'
                  ? item.id
                  : Number.isFinite(Number(item.id))
                    ? Number(item.id)
                    : null,
              animalId: String(
                item.animal_id || herdAnimal.id,
              ),
              vaccine: String(
                item.vaccine ||
                  item.vaccination ||
                  'Vaccination',
              ),
              dose: String(item.dose || ''),
              administrator: String(
                item.veterinarian ||
                  item.operator ||
                  '',
              ),
              scheduledDate: dateValue(
                item.next_due_date ||
                  item.scheduled_date,
              ),
              administeredDate: dateValue(
                item.administered_date,
              ),
              category: herdAnimal.category,
              scheduleStatus: String(
                item.schedule_status || '',
              ),
              status: String(
                item.status || 'COMPLETED',
              ),
              sourceEventId: String(
                item.source_event_id || '',
              ),
              createdAt: String(
                item.created_at ||
                  item.timestamp ||
                  '',
              ),
              batchNumber: String(
                item.batch_number ||
                  item.batch ||
                  '',
              ),
              notes: String(item.notes || ''),
            }),
          ),
      );

      loaded.sort((a, b) => {
        const animalCompare =
          a.animalId.localeCompare(b.animalId);

        if (animalCompare !== 0) {
          return animalCompare;
        }

        const vaccineCompare =
          a.vaccine.localeCompare(b.vaccine);

        if (vaccineCompare !== 0) {
          return vaccineCompare;
        }

        return (
          a.scheduledDate || '9999-99-99'
        ).localeCompare(
          b.scheduledDate || '9999-99-99',
        );
      });

      setRows(loaded);
    } catch (caught) {
      setError(
        caught instanceof Error
          ? caught.message
          : 'Unable to load vaccination schedules',
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void load();
  }, [herdMasterList]);

  const today = farmToday();

  const activeRows = useMemo(
    () =>
      rows.filter(
        row =>
          row.status.toUpperCase() !== 'VOID',
      ),
    [rows],
  );

  const unresolvedRows = useMemo(
    () =>
      activeRows.filter(
        row =>
          !row.administeredDate &&
          Boolean(row.scheduledDate),
      ),
    [activeRows],
  );

  const overdue = useMemo(
    () =>
      unresolvedRows.filter(
        row => row.scheduledDate < today,
      ).length,
    [unresolvedRows, today],
  );

  const due30 = useMemo(() => {
    const end = shiftFarmDate(today, 30);

    return unresolvedRows.filter(
      row =>
        row.scheduledDate > today &&
        row.scheduledDate <= end,
    ).length;
  }, [unresolvedRows, today]);

  const vaccineColumns = useMemo(() => {
    const present = new Set(
      activeRows.map(row => row.vaccine),
    );

    return VACCINES.filter(vaccine =>
      present.has(vaccine),
    ).concat(
      Array.from(present)
        .filter(
          vaccine => !VACCINES.includes(vaccine),
        )
        .sort((a, b) => a.localeCompare(b)),
    );
  }, [activeRows]);

  const filteredAnimals = useMemo(() => {
    const query = search.toLowerCase().trim();

    return herdMasterList.filter(herdAnimal => {
      if (!query) {
        return true;
      }

      const animalRows = activeRows.filter(
        row => row.animalId === herdAnimal.id,
      );

      return [
        herdAnimal.id,
        herdAnimal.category,
        herdAnimal.breed,
        ...animalRows.flatMap(row => [
          row.vaccine,
          row.dose,
          row.administrator,
        ]),
      ]
        .join(' ')
        .toLowerCase()
        .includes(query);
    });
  }, [herdMasterList, activeRows, search]);

  const occurrencesFor = (
    animalId: string,
    vaccine: string,
  ) =>
    activeRows
      .filter(
        row =>
          row.animalId === animalId &&
          row.vaccine === vaccine,
      )
      .sort((a, b) =>
        (
          a.scheduledDate ||
          a.administeredDate ||
          '9999-99-99'
        ).localeCompare(
          b.scheduledDate ||
            b.administeredDate ||
            '9999-99-99',
        ),
      );

  const markGiven = async (
    row: VaccinationOccurrence,
  ) => {
    setError('');
    setMessage('');

    if (row.id == null) {
      setError(
        'This legacy vaccination record has no occurrence ID and cannot be endorsed from the schedule matrix.',
      );
      return;
    }

    if (row.administeredDate) {
      setError(
        'This vaccination occurrence is already marked given.',
      );
      return;
    }

    setAdministeringId(row.id);

    try {
      await api(
        `/farm/animals/${encodeURIComponent(
          row.animalId,
        )}/vaccinations/${row.id}/administer`,
        {
          administered_date: farmToday(),
          operator:
            row.administrator || 'Operator UI',
        },
      );

      setMessage(
        `${row.animalId} — ${row.vaccine} marked GIVEN on ${farmToday()}.`,
      );

      await load();
      onChanged?.();
    } catch (caught) {
      setError(
        caught instanceof Error
          ? caught.message
          : 'Unable to mark vaccination given',
      );
    } finally {
      setAdministeringId(null);
    }
  };

  const openCreateSchedule = () => {
    setAmending(null);
    setAmendmentDraft(null);
    setShowSchedule(true);
  };

  const openAmendSchedule = (
    row: VaccinationOccurrence,
  ) => {
    if (row.id == null) {
      setError(
        'This legacy vaccination record has no occurrence ID and cannot be amended from the schedule matrix.',
      );
      return;
    }

    if (row.administeredDate) {
      setError(
        'Administered vaccination occurrences cannot be amended.',
      );
      return;
    }

    if (row.status.toUpperCase() === 'VOID') {
      setError(
        'VOID vaccination occurrences cannot be amended.',
      );
      return;
    }

    setError('');
    setMessage('');
    setAmending(row);
    setAmendmentDraft(
      amendmentDraftFrom(row),
    );
    setShowSchedule(true);
  };

  const updateDraft = (
    index: number,
    patch: Partial<ScheduleDraft>,
  ) => {
    setScheduleDrafts(current =>
      current.map((draft, draftIndex) =>
        draftIndex === index
          ? { ...draft, ...patch }
          : draft,
      ),
    );
  };

  const addVaccineDraft = () => {
    setScheduleDrafts(current => [
      ...current,
      emptyScheduleDraft(),
    ]);
  };

  const removeVaccineDraft = (index: number) => {
    setScheduleDrafts(current => {
      if (current.length === 1) {
        return [emptyScheduleDraft()];
      }

      return current.filter(
        (_, draftIndex) => draftIndex !== index,
      );
    });
  };

  const addDate = (draftIndex: number) => {
    setScheduleDrafts(current =>
      current.map((draft, index) =>
        index === draftIndex
          ? {
              ...draft,
              dates: [...draft.dates, ''],
            }
          : draft,
      ),
    );
  };

  const updateDate = (
    draftIndex: number,
    dateIndex: number,
    value: string,
  ) => {
    setScheduleDrafts(current =>
      current.map((draft, index) => {
        if (index !== draftIndex) {
          return draft;
        }

        return {
          ...draft,
          dates: draft.dates.map(
            (date, currentDateIndex) =>
              currentDateIndex === dateIndex
                ? value
                : date,
          ),
        };
      }),
    );
  };

  const removeDate = (
    draftIndex: number,
    dateIndex: number,
  ) => {
    setScheduleDrafts(current =>
      current.map((draft, index) => {
        if (index !== draftIndex) {
          return draft;
        }

        const dates = draft.dates.filter(
          (_, currentDateIndex) =>
            currentDateIndex !== dateIndex,
        );

        return {
          ...draft,
          dates: dates.length ? dates : [''],
        };
      }),
    );
  };

  const save = async (
    event: React.FormEvent,
  ) => {
    event.preventDefault();
    setSaving(true);
    setError('');
    setMessage('');

    try {
      if (amending && amendmentDraft) {
        if (!amendmentDraft.vaccine.trim()) {
          throw new Error('Enter a vaccine.');
        }
        if (!amendmentDraft.dose.trim()) {
          throw new Error('Enter a dose.');
        }
        if (!amendmentDraft.scheduledDate) {
          throw new Error(
            'Enter a scheduled date.',
          );
        }

        await api(
          `/farm/animals/${encodeURIComponent(
            amending.animalId,
          )}/vaccinations/${amending.id}/amend`,
          {
            vaccine:
              amendmentDraft.vaccine.trim(),
            dose: amendmentDraft.dose.trim(),
            scheduled_date:
              amendmentDraft.scheduledDate,
            notes:
              amendmentDraft.notes.trim() ||
              null,
            veterinarian:
              amendmentDraft.administrator.trim() ||
              null,
            operator:
              amendmentDraft.administrator.trim() ||
              'Operator UI',
          },
        );

        setShowSchedule(false);
        setAmending(null);
        setAmendmentDraft(null);
        setMessage(
          `${amending.animalId} — ${amendmentDraft.vaccine.trim()} schedule amended.`,
        );
        await load();
        onChanged?.();
        return;
      }

      if (!animal) {
        throw new Error('Select an animal.');
      }

      const occurrences = scheduleDrafts.flatMap(
        draft => {
          const dates = Array.from(
            new Set(
              draft.dates
                .map(date => date.trim())
                .filter(Boolean),
            ),
          ).sort();

          if (!draft.vaccine) {
            throw new Error(
              'Select a vaccine for every schedule entry.',
            );
          }

          if (!draft.dose.trim()) {
            throw new Error(
              `Enter a dose for ${draft.vaccine}.`,
            );
          }

          if (!dates.length) {
            throw new Error(
              `Add at least one scheduled date for ${draft.vaccine}.`,
            );
          }

          return dates.map(date => ({
            draft,
            date,
          }));
        },
      );

      if (!occurrences.length) {
        throw new Error(
          'Add at least one vaccination schedule.',
        );
      }

      await api(
        `/farm/animals/${encodeURIComponent(
          animal,
        )}/vaccinations/schedule-batch`,
        {
          animal_id: animal,
          operator: 'Operator UI',
          occurrences: occurrences.map(
            ({ draft, date }) => ({
              vaccine: draft.vaccine,
              dose: draft.dose.trim(),
              scheduled_date: date,
              notes:
                draft.purpose.trim() || null,
              veterinarian:
                draft.administrator.trim() ||
                null,
            }),
          ),
        },
      );

      setShowSchedule(false);
      setScheduleDrafts([
        emptyScheduleDraft(),
      ]);

      setMessage(
        `${occurrences.length} vaccination schedule occurrence${
          occurrences.length === 1 ? '' : 's'
        } saved for ${animal}.`,
      );

      await load();
      onChanged?.();
    } catch (caught) {
      setError(
        caught instanceof Error
          ? caught.message
          : 'Unable to save vaccination schedule',
      );
    } finally {
      setSaving(false);
    }
  };

  const deleteSchedule = async () => {
    if (!amending || !amendmentDraft) {
      return;
    }

    setSaving(true);
    setError('');
    setMessage('');

    try {
      await api(
        `/farm/animals/${encodeURIComponent(
          amending.animalId,
        )}/vaccinations/${amending.id}/void`,
        {
          notes:
            amendmentDraft.notes.trim() || null,
          operator:
            amendmentDraft.administrator.trim() ||
            'Operator UI',
        },
      );

      setShowSchedule(false);
      setAmending(null);
      setAmendmentDraft(null);
      setMessage(
        `${amending.animalId} — ${amending.vaccine} schedule voided.`,
      );
      await load();
      onChanged?.();
    } catch (caught) {
      setError(
        caught instanceof Error
          ? caught.message
          : 'Unable to delete vaccination schedule',
      );
    } finally {
      setSaving(false);
    }
  };

  const openPassport = (animalId: string) => {
    if (onOpenPassport) {
      onOpenPassport(animalId);
      return;
    }

    setPassport(animalId);
  };

  useEffect(() => {
    if (!showLog) {
      return;
    }

    let cancelled = false;

    const loadAuditHistory = async () => {
      try {
        const rows = await api(
          '/farm/vaccinations/audit-history',
        );

        if (!cancelled) {
          setAuditRows(Array.isArray(rows) ? rows : []);
        }
      } catch (err) {
        if (!cancelled) {
          setError(
            err instanceof Error
              ? err.message
              : 'Unable to load vaccination audit history.',
          );
        }
      }
    };

    void loadAuditHistory();

    return () => {
      cancelled = true;
    };
  }, [showLog]);

  const logRows = useMemo(
    () =>
      [...auditRows].sort((a, b) =>
        String(a.event_timestamp || '').localeCompare(
          String(b.event_timestamp || ''),
        ),
      ),
    [auditRows],
  );

  return (
    <div
      style={{
        padding: 16,
        color: '#fff',
        fontSize: 12,
        height: '100%',
        overflowY: 'auto',
        boxSizing: 'border-box',
      }}
    >
      <header
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          gap: 10,
          alignItems: 'center',
          flexWrap: 'wrap',
          marginBottom: 12,
        }}
      >
        <div>
          <h2
            style={{
              margin: 0,
              color: '#22c55e',
              fontSize: 18,
              display: 'flex',
              gap: 7,
              alignItems: 'center',
            }}
          >
            <ShieldCheck size={20} />
            Vaccination Operations
          </h2>

          <div
            style={{
              fontSize: 12,
              color: '#94a3b8',
            }}
          >
            Animal vaccination schedules. Empty
            boxes remain due; administered
            occurrences retain their scheduled and
            actual dates.
          </div>
        </div>

        <button
          onClick={openCreateSchedule}
          style={btn('#0369a1')}
        >
          <Plus size={14} />
          Add Vaccination Schedule
        </button>
      </header>

      <div
        style={{
          display: 'grid',
          gridTemplateColumns:
            'repeat(2,minmax(0,1fr))',
          gap: 8,
          marginBottom: 12,
        }}
      >
        <Metric
          title="Overdue"
          value={overdue}
        />
        <Metric
          title="Due Next 30 Days"
          value={due30}
        />
      </div>

      {error && (
        <Notice
          error
          text={error}
        />
      )}

      {message && (
        <Notice text={message} />
      )}

      <section
        style={{
          ...card,
          overflowX: 'auto',
        }}
      >
        <div
          style={{
            padding: 12,
            display: 'flex',
            justifyContent: 'space-between',
            gap: 8,
            flexWrap: 'wrap',
          }}
        >
          <strong
            style={{
              display: 'flex',
              gap: 6,
              alignItems: 'center',
            }}
          >
            <CalendarClock size={15} />
            Vaccination Schedule by Animal
          </strong>

          <SearchBox
            value={search}
            set={setSearch}
          />
        </div>

        <table
          style={{
            width: '100%',
            minWidth: Math.max(
              760,
              250 + vaccineColumns.length * 190,
            ),
            borderCollapse: 'collapse',
            fontSize: 10,
          }}
        >
          <thead>
            <tr
              style={{
                background: '#161f30',
              }}
            >
              <th
                style={{
                  ...th,
                  minWidth: 150,
                  position: 'sticky',
                  left: 0,
                  zIndex: 3,
                  background: '#161f30',
                }}
              >
                Animal ID
              </th>

              {vaccineColumns.map(vaccine => (
                <th
                  key={vaccine}
                  style={{
                    ...th,
                    minWidth: 180,
                    maxWidth: 220,
                  }}
                >
                  {vaccine}
                </th>
              ))}
            </tr>
          </thead>

          <tbody>
            {!loading &&
              filteredAnimals.map(herdAnimal => (
                <tr key={herdAnimal.id}>
                  <td
                    style={{
                      ...td,
                      position: 'sticky',
                      left: 0,
                      zIndex: 2,
                      background: '#111827',
                    }}
                  >
                    <button
                      onClick={() =>
                        openPassport(
                          herdAnimal.id,
                        )
                      }
                      style={{
                        background: 'none',
                        border: 0,
                        padding: 0,
                        color: '#7dd3fc',
                        fontWeight: 800,
                        fontSize: 10,
                        cursor: 'pointer',
                        textDecoration:
                          'underline',
                      }}
                    >
                      #{herdAnimal.id}
                    </button>

                    <div
                      style={{
                        marginTop: 3,
                        color: '#94a3b8',
                        fontSize: 9,
                      }}
                    >
                      {herdAnimal.category}
                    </div>
                  </td>

                  {vaccineColumns.map(
                    vaccine => (
                      <td
                        key={`${herdAnimal.id}-${vaccine}`}
                        style={td}
                      >
                        <OccurrenceCell
                          rows={occurrencesFor(
                            herdAnimal.id,
                            vaccine,
                          )}
                          today={today}
                          administeringId={
                            administeringId
                          }
                          markGiven={markGiven}
                          openAmendSchedule={
                            openAmendSchedule
                          }
                        />
                      </td>
                    ),
                  )}
                </tr>
              ))}
          </tbody>
        </table>

        {!loading &&
          filteredAnimals.length === 0 && (
            <div
              style={{
                padding: 18,
                textAlign: 'center',
                color: '#64748b',
                fontSize: 10,
              }}
            >
              No animals match this view.
            </div>
          )}

        {!loading &&
          filteredAnimals.length > 0 &&
          vaccineColumns.length === 0 && (
            <div
              style={{
                padding: 18,
                color: '#94a3b8',
                fontSize: 10,
              }}
            >
              No vaccination schedules have been
              entered yet. Use Add Vaccination
              Schedule to create the first schedule.
            </div>
          )}
      </section>

      <button
        onClick={() =>
          setShowLog(current => !current)
        }
        style={{
          ...btn('#334155'),
          marginTop: 12,
        }}
      >
        {showLog
          ? 'Hide Overall Log'
          : 'Show Overall Log'}
      </button>

      {showLog && (
        <section
          style={{
            ...card,
            marginTop: 8,
            overflowX: 'auto',
          }}
        >
          <div
            style={{
              padding: 12,
              fontWeight: 800,
            }}
          >
            Overall Log
          </div>

          <table
            style={{
              width: '100%',
              minWidth: 980,
              borderCollapse: 'collapse',
              fontSize: 10,
            }}
          >
            <thead>
              <tr>
                {[
                  'Animal ID',
                  'Vaccine',
                  'Action',
                  'Scheduled Date',
                  'Given Date',
                  'Dose',
                  'Administrator',
                  'Operator',
                  'Event Timestamp',
                  'Notes',
                ].map(label => (
                  <th
                    key={label}
                    style={th}
                  >
                    {label}
                  </th>
                ))}
              </tr>
            </thead>

            <tbody>
              {logRows.map(row => (
                <tr key={occurrenceKey(row)}>
                  <td style={td}>
                    <button
                      onClick={() =>
                        openPassport(
                          row.animal_id,
                        )
                      }
                      style={{
                        background: 'none',
                        border: 0,
                        padding: 0,
                        color: '#7dd3fc',
                        fontWeight: 800,
                        fontSize: 10,
                        cursor: 'pointer',
                        textDecoration:
                          'underline',
                      }}
                    >
                      #{row.animal_id}
                    </button>
                  </td>
                  <td style={td}>
                    {row.vaccine}
                  </td>
                  <td style={td}>
                    {row.action || 'LEGACY'}
                  </td>
                  <td style={td}>
                    {row.scheduled_date ||
                      '—'}
                  </td>
                  <td style={td}>
                    {row.administered_date ||
                      '—'}
                  </td>
                  <td style={td}>
                    {row.dose || '—'}
                  </td>
                  <td style={td}>
                    {row.administrator ||
                      '—'}
                  </td>
                  <td style={td}>
                    {row.operator || '—'}
                  </td>
                  <td style={td}>
                    {row.event_timestamp || '—'}
                  </td>
                  <td style={td}>
                    {row.notes || '—'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          {!logRows.length && (
            <div
              style={{
                padding: 14,
                color: '#64748b',
                fontSize: 10,
              }}
            >
              No vaccination history recorded.
            </div>
          )}
        </section>
      )}

      {showSchedule && (
        <Modal
          close={() => {
            setShowSchedule(false);
            setAmending(null);
            setAmendmentDraft(null);
          }}
        >
          <form
            onSubmit={save}
            style={{
              display: 'grid',
              gap: 10,
            }}
          >
            <strong>
              {amending
                ? 'Amend Vaccination Schedule'
                : 'Add Vaccination Schedule'}
            </strong>

            {amending && amendmentDraft ? (
              <>
                <ReadOnlyField
                  label="Animal"
                  value={amending.animalId}
                />
                <ReadOnlyField
                  label="Occurrence ID"
                  value={String(amending.id)}
                />
                <ReadOnlyField
                  label="Created"
                  value={amending.createdAt || '—'}
                />
                <ReadOnlyField
                  label="Administered Date"
                  value={
                    amending.administeredDate || '—'
                  }
                />

                <Field label="Vaccine">
                  <select
                    required
                    value={amendmentDraft.vaccine}
                    onChange={event =>
                      setAmendmentDraft({
                        ...amendmentDraft,
                        vaccine:
                          event.target.value,
                      })
                    }
                    style={field}
                  >
                    <option value="">
                      Select vaccine
                    </option>
                    {VACCINES.map(vaccine => (
                      <option
                        key={vaccine}
                        value={vaccine}
                      >
                        {vaccine}
                      </option>
                    ))}
                  </select>
                </Field>

                <Field label="Dose">
                  <input
                    required
                    value={amendmentDraft.dose}
                    onChange={event =>
                      setAmendmentDraft({
                        ...amendmentDraft,
                        dose: event.target.value,
                      })
                    }
                    style={field}
                  />
                </Field>

                <Field label="Administrator">
                  <input
                    value={
                      amendmentDraft.administrator
                    }
                    onChange={event =>
                      setAmendmentDraft({
                        ...amendmentDraft,
                        administrator:
                          event.target.value,
                      })
                    }
                    style={field}
                  />
                </Field>

                <Field label="Scheduled Date">
                  <input
                    required
                    type="date"
                    value={
                      amendmentDraft.scheduledDate
                    }
                    onChange={event =>
                      setAmendmentDraft({
                        ...amendmentDraft,
                        scheduledDate:
                          event.target.value,
                      })
                    }
                    style={field}
                  />
                </Field>

                <Field label="Notes">
                  <input
                    value={amendmentDraft.notes}
                    onChange={event =>
                      setAmendmentDraft({
                        ...amendmentDraft,
                        notes: event.target.value,
                      })
                    }
                    style={field}
                  />
                </Field>

                <div
                  style={{
                    display: 'flex',
                    gap: 8,
                    flexWrap: 'wrap',
                  }}
                >
                  <button
                    disabled={saving}
                    style={btn('#0369a1')}
                  >
                    {saving
                      ? 'Saving...'
                      : 'Save Changes'}
                  </button>
                  <button
                    type="button"
                    disabled={saving}
                    onClick={() =>
                      void deleteSchedule()
                    }
                    style={btn('#7f1d1d')}
                  >
                    <Trash2 size={12} />
                    Delete Schedule
                  </button>
                  <button
                    type="button"
                    onClick={() => {
                      setShowSchedule(false);
                      setAmending(null);
                      setAmendmentDraft(null);
                    }}
                    style={btn('#334155')}
                  >
                    Cancel
                  </button>
                </div>
              </>
            ) : (
              <>
            <Field label="Animal">
              <select
                required
                value={animal}
                onChange={event =>
                  setAnimal(
                    event.target.value,
                  )
                }
                style={field}
              >
                {herdMasterList.map(
                  herdAnimal => (
                    <option
                      key={herdAnimal.id}
                      value={herdAnimal.id}
                    >
                      {herdAnimal.id} -{' '}
                      {herdAnimal.category}
                    </option>
                  ),
                )}
              </select>
            </Field>

            <div
              style={{
                display: 'grid',
                gap: 10,
                maxHeight: '58vh',
                overflowY: 'auto',
                paddingRight: 3,
              }}
            >
              {scheduleDrafts.map(
                (draft, draftIndex) => (
                  <div
                    key={draftIndex}
                    style={{
                      background: '#0f172a',
                      border:
                        '1px solid #334155',
                      borderRadius: 7,
                      padding: 10,
                      display: 'grid',
                      gap: 8,
                    }}
                  >
                    <div
                      style={{
                        display: 'flex',
                        justifyContent:
                          'space-between',
                        gap: 8,
                        alignItems: 'center',
                      }}
                    >
                      <strong
                        style={{
                          fontSize: 10,
                        }}
                      >
                        Vaccine{' '}
                        {draftIndex + 1}
                      </strong>

                      {scheduleDrafts.length >
                        1 && (
                        <button
                          type="button"
                          onClick={() =>
                            removeVaccineDraft(
                              draftIndex,
                            )
                          }
                          style={btn('#7f1d1d')}
                        >
                          <Trash2 size={12} />
                          Remove
                        </button>
                      )}
                    </div>

                    <Field label="Vaccine">
                      <select
                        required
                        value={draft.vaccine}
                        onChange={event =>
                          updateDraft(
                            draftIndex,
                            {
                              vaccine:
                                event.target
                                  .value,
                            },
                          )
                        }
                        style={field}
                      >
                        <option value="">
                          Select vaccine
                        </option>

                        {VACCINES.map(
                          vaccine => (
                            <option
                              key={vaccine}
                              value={vaccine}
                            >
                              {vaccine}
                            </option>
                          ),
                        )}
                      </select>
                    </Field>

                    <Field label="Purpose / disease">
                      <input
                        value={draft.purpose}
                        onChange={event =>
                          updateDraft(
                            draftIndex,
                            {
                              purpose:
                                event.target
                                  .value,
                            },
                          )
                        }
                        style={field}
                      />
                    </Field>

                    <Field label="Dose">
                      <input
                        required
                        value={draft.dose}
                        onChange={event =>
                          updateDraft(
                            draftIndex,
                            {
                              dose:
                                event.target
                                  .value,
                            },
                          )
                        }
                        style={field}
                      />
                    </Field>

                    <Field label="Administrator">
                      <input
                        value={
                          draft.administrator
                        }
                        onChange={event =>
                          updateDraft(
                            draftIndex,
                            {
                              administrator:
                                event.target
                                  .value,
                            },
                          )
                        }
                        style={field}
                      />
                    </Field>

                    <div
                      style={{
                        fontSize: 10,
                        color: '#94a3b8',
                      }}
                    >
                      Scheduled dates
                    </div>

                    {draft.dates.map(
                      (
                        scheduledDate,
                        dateIndex,
                      ) => (
                        <div
                          key={dateIndex}
                          style={{
                            display: 'grid',
                            gridTemplateColumns:
                              '1fr auto',
                            gap: 6,
                            alignItems:
                              'center',
                          }}
                        >
                          <input
                            required
                            type="date"
                            value={
                              scheduledDate
                            }
                            onChange={event =>
                              updateDate(
                                draftIndex,
                                dateIndex,
                                event.target
                                  .value,
                              )
                            }
                            style={field}
                          />

                          <button
                            type="button"
                            onClick={() =>
                              removeDate(
                                draftIndex,
                                dateIndex,
                              )
                            }
                            aria-label="Remove scheduled date"
                            style={{
                              ...btn(
                                '#334155',
                              ),
                              padding: 9,
                            }}
                          >
                            <X size={13} />
                          </button>
                        </div>
                      ),
                    )}

                    <button
                      type="button"
                      onClick={() =>
                        addDate(
                          draftIndex,
                        )
                      }
                      style={{
                        ...btn('#334155'),
                        justifySelf: 'start',
                      }}
                    >
                      <Plus size={12} />
                      Add Date
                    </button>
                  </div>
                ),
              )}
            </div>

            <button
              type="button"
              onClick={addVaccineDraft}
              style={{
                ...btn('#334155'),
                justifySelf: 'start',
              }}
            >
              <Plus size={12} />
              Add Another Vaccine
            </button>

            <button
              disabled={saving}
              style={btn('#0369a1')}
            >
              {saving
                ? 'Saving...'
                : 'Save Vaccination Schedule'}
            </button>
              </>
            )}
          </form>
        </Modal>
      )}

      {passport && (
        <AnimalPassportModal
          animalId={passport}
          onClose={() =>
            setPassport(null)
          }
        />
      )}
    </div>
  );
}

function OccurrenceCell({
  rows,
  today,
  administeringId,
  markGiven,
  openAmendSchedule,
}: {
  rows: VaccinationOccurrence[];
  today: string;
  administeringId: number | null;
  markGiven: (
    row: VaccinationOccurrence,
  ) => Promise<void>;
  openAmendSchedule: (
    row: VaccinationOccurrence,
  ) => void;
}) {
  if (!rows.length) {
    return (
      <span
        style={{
          color: '#475569',
        }}
      >
        —
      </span>
    );
  }

  return (
    <div
      style={{
        display: 'grid',
        gap: 6,
      }}
    >
      {rows.map(row => {
        const sameDate =
          Boolean(row.scheduledDate) &&
          row.scheduledDate ===
            row.administeredDate;

        const overdue =
          !row.administeredDate &&
          Boolean(row.scheduledDate) &&
          row.scheduledDate < today;

        const dueToday =
          !row.administeredDate &&
          row.scheduledDate === today;

        if (row.administeredDate) {
          return (
            <div
              key={occurrenceKey(row)}
              style={{
                borderBottom:
                  '1px solid #1f2937',
                paddingBottom: 5,
              }}
            >
              {sameDate ? (
                <div
                  style={{
                    display: 'flex',
                    gap: 4,
                    alignItems: 'center',
                    color: '#86efac',
                    fontWeight: 800,
                  }}
                >
                  <Check size={13} />
                  {shortDate(
                    row.administeredDate,
                  )}
                </div>
              ) : (
                <>
                  <div
                    style={{
                      color: '#cbd5e1',
                    }}
                  >
                    Due{' '}
                    {shortDate(
                      row.scheduledDate,
                    )}
                  </div>
                  <div
                    style={{
                      display: 'flex',
                      gap: 4,
                      alignItems: 'center',
                      color: '#86efac',
                      fontWeight: 800,
                      marginTop: 2,
                    }}
                  >
                    <Check size={13} />
                    {shortDate(
                      row.administeredDate,
                    )}
                  </div>
                </>
              )}

              {row.dose && (
                <div
                  style={{
                    color: '#64748b',
                    fontSize: 8,
                    marginTop: 2,
                  }}
                >
                  {row.dose}
                </div>
              )}
            </div>
          );
        }

        if (!row.scheduledDate) {
          return (
            <div
              key={occurrenceKey(row)}
              style={{
                color: '#94a3b8',
              }}
            >
              Unscheduled
            </div>
          );
        }

        return (
          <div
            key={occurrenceKey(row)}
            style={{
              display: 'flex',
              gap: 5,
              alignItems: 'center',
            }}
          >
            <button
              type="button"
              disabled={row.id == null}
              onClick={() =>
                openAmendSchedule(row)
              }
              title={`Amend ${row.vaccine} scheduled ${row.scheduledDate}`}
              aria-label={`Amend ${row.vaccine} for ${row.animalId} scheduled ${row.scheduledDate}`}
              style={{
                background: 'transparent',
                border: 0,
                padding: 0,
                textAlign: 'left',
                color: overdue
                  ? '#f87171'
                  : dueToday
                    ? '#fcd34d'
                    : '#cbd5e1',
                cursor:
                  row.id == null
                    ? 'not-allowed'
                    : 'pointer',
                fontSize: 9,
                fontWeight:
                  overdue || dueToday
                    ? 800
                    : 600,
                display: 'flex',
                gap: 5,
                alignItems: 'center',
              }}
            >
              <span
                style={{
                  width: 13,
                  height: 13,
                  border:
                    '1px solid currentColor',
                  borderRadius: 3,
                  display: 'inline-flex',
                  flex: '0 0 auto',
                }}
              />

              <span>
                {shortDate(row.scheduledDate)}
              </span>
            </button>
            <button
              type="button"
              disabled={
                row.id == null ||
                administeringId === row.id
              }
              onClick={() => void markGiven(row)}
              title={`Mark Given — ${row.vaccine} scheduled ${row.scheduledDate}`}
              aria-label={`Mark Given ${row.vaccine} for ${row.animalId} scheduled ${row.scheduledDate}`}
              style={{
                ...btn('#15803d'),
                padding: '3px 5px',
                fontSize: 8,
              }}
            >
              <CheckCircle2 size={10} />
              {administeringId === row.id
                ? 'Marking...'
                : 'Mark Given'}
            </button>
          </div>
        );
      })}
    </div>
  );
}

function Metric({
  title,
  value,
}: {
  title: string;
  value: number;
}) {
  return (
    <div style={card}>
      <div
        style={{
          padding: 11,
          textAlign: 'center',
        }}
      >
        <div
          style={{
            fontSize: 9,
            color: '#94a3b8',
            fontWeight: 800,
            textTransform: 'uppercase',
          }}
        >
          {title}
        </div>

        <div
          style={{
            fontSize: 20,
            fontWeight: 900,
            marginTop: 3,
          }}
        >
          {value}
        </div>
      </div>
    </div>
  );
}

function Notice({
  text,
  error = false,
}: {
  text: string;
  error?: boolean;
}) {
  return (
    <div
      style={{
        background: error
          ? '#450a0a'
          : '#064e3b',
        color: error
          ? '#fecaca'
          : '#a7f3d0',
        padding: 9,
        borderRadius: 6,
        marginBottom: 10,
        fontSize: 11,
      }}
    >
      {text}
    </div>
  );
}

function SearchBox({
  value,
  set,
}: {
  value: string;
  set: (value: string) => void;
}) {
  return (
    <div
      style={{
        position: 'relative',
        minWidth: 260,
      }}
    >
      <Search
        size={13}
        style={{
          position: 'absolute',
          left: 9,
          top: 10,
          color: '#64748b',
        }}
      />

      <input
        value={value}
        onChange={event =>
          set(event.target.value)
        }
        placeholder="Search animal, vaccine, category"
        style={{
          ...field,
          paddingLeft: 28,
        }}
      />
    </div>
  );
}

function Field({
  label,
  children,
}: {
  label: string;
  children: React.ReactNode;
}) {
  return (
    <label
      style={{
        fontSize: 10,
        color: '#94a3b8',
        display: 'grid',
        gap: 4,
      }}
    >
      {label}
      {children}
    </label>
  );
}

function ReadOnlyField({
  label,
  value,
}: {
  label: string;
  value: string;
}) {
  return (
    <label
      style={{
        fontSize: 10,
        color: '#94a3b8',
      }}
    >
      {label}
      <div
        style={{
          ...field,
          color: '#cbd5e1',
          background: '#111827',
        }}
      >
        {value || '—'}
      </div>
    </label>
  );
}

function Modal({
  close,
  children,
}: {
  close: () => void;
  children: React.ReactNode;
}) {
  return (
    <div
      style={{
        position: 'fixed',
        inset: 0,
        zIndex: 1000,
        background: 'rgba(0,0,0,.82)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: 14,
      }}
    >
      <div
        style={{
          width: 'min(720px,100%)',
          maxHeight: '90vh',
          overflowY: 'auto',
          background: '#111827',
          border: '1px solid #22c55e',
          borderRadius: 9,
          padding: 18,
          position: 'relative',
        }}
      >
        <button
          type="button"
          onClick={close}
          aria-label="Close"
          style={{
            position: 'absolute',
            right: 10,
            top: 10,
            background: 'none',
            border: 0,
            color: '#fff',
            cursor: 'pointer',
          }}
        >
          <X size={18} />
        </button>

        {children}
      </div>
    </div>
  );
}
