from datetime import date

from dairyos.milk.services.milk_session_sequence_service import (
    MilkSessionSequenceService,
    SequenceViolation,
)


class Record:
    def __init__(self, session, status):
        self.milking_session = session
        self.status = status


class Ledger:
    def __init__(self):
        self.by_date = []

    def get_by_date(self, _day):
        return list(self.by_date)

    def settled_sessions_on(self, _day):
        return {r.milking_session for r in self.by_date if r.status == 'RECORDED'}

    def has_any(self):
        return True

    def has_session_ever(self, _session):
        return True

    def earliest_date(self):
        return date(2026, 1, 1)


class Schedule: 
    def get_expected_sessions(self, _animal, _day):
        return ['MORNING', 'EVENING']


class Animal:
    animal_id = 'TD-002'


class MilkRepo:
    def __init__(self, row=None):
        self.row = row

    def ledger_row_for_animal_day(self, _animal_id, _day):
        return self.row


def test_other_animal_production_does_not_settle_session():
    ledger = Ledger()
    ledger.by_date.append(Record('EVENING', 'RECORDED'))
    service = MilkSessionSequenceService(ledger, schedule_service=Schedule(), milk_repository=MilkRepo())
    settled = service.settled_sessions_on(date(2026, 8, 31), animal=Animal())
    assert settled == []


def test_same_animal_cannot_record_same_session_twice():
    ledger = Ledger()
    ledger = Ledger()
    repo = MilkRepo(type('Row', (), {'status':'RECORDED','morning_yield':10,'afternoon_yield':None,'evening_yield':None})())
    service = MilkSessionSequenceService(ledger, schedule_service=Schedule(), milk_repository=repo)
    try:
        service.assert_can_record(date(2026, 8, 31), 'MORNING', animal=Animal())
    except SequenceViolation as exc:
        assert exc.reason == 'SESSION_ALREADY_SETTLED'
    else:
        raise AssertionError('duplicate session was accepted')
