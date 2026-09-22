from pathlib import Path


ROOT = Path(__file__).parents[2]
GATE = ROOT / "src" / "DairyOS.Web" / "src" / "components" / "HumanAccessGate.tsx"
MAIN = ROOT / "src" / "DairyOS.Web" / "src" / "main.tsx"
ACCESS = ROOT / "src" / "dairyos" / "api" / "human_access.py"
APP = ROOT / "src" / "dairyos" / "app.py"


def test_startup_mounts_human_access_gate_not_dashboard_shell():
    source = MAIN.read_text(encoding="utf-8")
    assert "HumanAccessGate" in source
    assert "<HumanAccessGate />" in source


def test_gate_contains_identity_cards_and_safe_states():
    source = GATE.read_text(encoding="utf-8")
    for marker in ("Welcome to DairyOS", "Find your name...", "Need help? Contact Administrator", "BETTER DATA"):
        assert marker in source
    assert "identityCard" in source
    assert "entry_group" not in source.split("return <div style={screen}", 1)[-1]
    assert "bootstrap" in source
    assert "dairyos.human.session" in source


def test_human_access_api_contains_bootstrap_pin_lockout_and_logout_contract():
    source = ACCESS.read_text(encoding="utf-8")
    for marker in ("/status", "/bootstrap", "/login", "/logout", "MAX_PIN_FAILURES", "locked_until"):
        assert marker in source
    assert "PIN" in source
    assert "session_token" in source


def test_human_access_help_records_a_review_request_without_resetting_access():
    source = ACCESS.read_text(encoding="utf-8")
    assert '"/help"' in source
    assert "PENDING_ADMIN_REVIEW" in source


def test_human_access_audit_events_supply_repository_timestamp():
    source = ACCESS.read_text(encoding="utf-8")
    assert "timestamp=utcnow()" in source
    assert "created_at=utcnow()" not in source


def test_human_access_login_uses_json_request_body_not_query_pin():
    source = ACCESS.read_text(encoding="utf-8")
    assert "class LoginRequest(BaseModel)" in source
    assert "def login(payload: LoginRequest)" in source


def test_person_creation_keeps_authenticated_admin_for_audit_actor():
    source = ACCESS.read_text(encoding="utf-8")
    assert "_, current = _require_admin(x_dairyos_human_session)" in source


def test_initial_pin_is_self_service_without_a_setup_code():
    api = ACCESS.read_text(encoding="utf-8")
    gate = GATE.read_text(encoding="utf-8")
    admin = (ROOT / "src" / "DairyOS.Web" / "src" / "components" / "HumanIdentityAdmin.tsx").read_text(encoding="utf-8")
    assert "setup_code" not in api
    assert "One-time PIN setup code" not in gate
    assert "one-time setup code" not in admin.lower()


def test_milk_operator_reuses_milk_fields_without_loading_finance_ledger():
    console = (ROOT / "src" / "DairyOS.Web" / "src" / "components" / "HumanOperatorConsole.tsx").read_text(encoding="utf-8")
    milk = (ROOT / "src" / "DairyOS.Web" / "src" / "components" / "MilkTab.tsx").read_text(encoding="utf-8")
    assert "<MilkTab operatorMode />" in console
    assert "operatorMode" in milk and "Promise.resolve({" in milk


def test_production_routes_require_named_human_session_and_capability():
    source = APP.read_text(encoding="utf-8")
    assert "X-DairyOS-Human-Session" in source
    assert "permission_for_request" in source
    assert "Permission required" in source
    assert "Human authentication required" in source


def test_existing_management_shell_remains_separate_from_gate():
    app = (ROOT / "src" / "DairyOS.Web" / "src" / "App.tsx").read_text(encoding="utf-8")
    main = MAIN.read_text(encoding="utf-8")
    assert "export function MainAppShell" in app
    assert "<MainAppShell />" not in main
