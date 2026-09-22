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


def test_gate_contains_required_entry_groups_and_safe_states():
    source = GATE.read_text(encoding="utf-8")
    for label in ("DAIRYOS MANAGEMENT", "MILK OPERATOR", "ACCOUNTS OPERATOR"):
        assert label in source
    assert "bootstrap" in source
    assert "PIN NOT SET" in source or "PIN NOT YET SET" in source
    assert "dairyos.human.session" in source


def test_human_access_api_contains_bootstrap_pin_lockout_and_logout_contract():
    source = ACCESS.read_text(encoding="utf-8")
    for marker in ("/status", "/bootstrap", "/login", "/logout", "MAX_PIN_FAILURES", "locked_until", "pin_setup_hash"):
        assert marker in source
    assert "PIN" in source
    assert "session_token" in source


def test_human_access_audit_events_supply_repository_timestamp():
    source = ACCESS.read_text(encoding="utf-8")
    assert "timestamp=utcnow()" in source
    assert "created_at=utcnow()" not in source


def test_human_access_login_uses_json_request_body_not_query_pin():
    source = ACCESS.read_text(encoding="utf-8")
    assert "class LoginRequest(BaseModel)" in source
    assert "def login(payload: LoginRequest)" in source


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
