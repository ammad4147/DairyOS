"""Repository for the AppSetting key/value store (2026-08-14)."""

from dairyos.data.models.app_setting import AppSetting


class AppSettingRepository:
    def __init__(self, session=None):
        self.session = session
        self.records = {}

    def get(self, key: str, default=None):
        if self.session:
            row = self.session.query(AppSetting).filter(AppSetting.key == key).first()
            return row.value if row is not None else default
        return self.records.get(key, default)

    def get_all(self) -> dict:
        if self.session:
            return {row.key: row.value for row in self.session.query(AppSetting).all()}
        return dict(self.records)

    def set(self, key: str, value, *, updated_by: str | None = None) -> AppSetting:
        value = None if value is None else str(value)

        if not self.session:
            self.records[key] = value
            return AppSetting(key=key, value=value, updated_by=updated_by)

        row = self.session.query(AppSetting).filter(AppSetting.key == key).first()
        if row is None:
            row = AppSetting(key=key, value=value, updated_by=updated_by)
            self.session.add(row)
        else:
            row.value = value
            row.updated_by = updated_by
        self.session.commit()
        self.session.refresh(row)
        return row
