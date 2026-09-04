"""Navigation Visibility administrator credential lifecycle contracts."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def _login(client, password: str):
    return client.post(
        "/auth/login",
        json={"username": "admin", "password": password},
    )


def test_navigation_credential_setup_recovery_and_rotation(client, monkeypatch):
    monkeypatch.delenv("DAIRYOS_ADMIN_PASSWORD", raising=False)
    monkeypatch.setenv("DAIRYOS_ADMIN_USERNAME", "admin")

    status = client.get("/settings/navigation-credentials")
    assert status.status_code == 200, status.text
    assert status.json() == {
        "username": "admin",
        "setup_required": True,
        "recovery_configured": False,
    }

    too_short = client.post(
        "/settings/navigation-credentials/setup",
        json={"username": "admin", "new_password": "short"},
    )
    assert too_short.status_code == 422, too_short.text

    default_password = client.post(
        "/settings/navigation-credentials/setup",
        json={"username": "admin", "new_password": "dairyos"},
    )
    assert default_password.status_code == 422, default_password.text

    initial_password = "DairyOS-Admin-2026!"
    setup = client.post(
        "/settings/navigation-credentials/setup",
        json={"username": "admin", "new_password": initial_password},
    )
    assert setup.status_code == 200, setup.text
    first_recovery_code = setup.json()["recovery_code"]
    assert first_recovery_code
    assert setup.json()["recovery_code_display"] == "ONE_TIME"

    duplicate_setup = client.post(
        "/settings/navigation-credentials/setup",
        json={"username": "admin", "new_password": "Another-Admin-2026!"},
    )
    assert duplicate_setup.status_code == 409, duplicate_setup.text

    assert _login(client, "dairyos").status_code == 401
    signed_in = _login(client, initial_password)
    assert signed_in.status_code == 200, signed_in.text
    token = signed_in.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    unauthenticated_rotation = client.post(
        "/settings/navigation-credentials/recovery-code"
    )
    assert unauthenticated_rotation.status_code == 401, unauthenticated_rotation.text

    rotated = client.post(
        "/settings/navigation-credentials/recovery-code",
        headers=headers,
    )
    assert rotated.status_code == 200, rotated.text
    second_recovery_code = rotated.json()["recovery_code"]
    assert second_recovery_code
    assert second_recovery_code != first_recovery_code

    bad_recovery = client.post(
        "/settings/navigation-credentials/recover",
        json={
            "username": "admin",
            "recovery_code": first_recovery_code,
            "new_password": "Recovered-Admin-2026!",
        },
    )
    assert bad_recovery.status_code == 401, bad_recovery.text

    recovered_password = "Recovered-Admin-2026!"
    recovered = client.post(
        "/settings/navigation-credentials/recover",
        json={
            "username": "admin",
            "recovery_code": second_recovery_code,
            "new_password": recovered_password,
        },
    )
    assert recovered.status_code == 200, recovered.text
    third_recovery_code = recovered.json()["recovery_code"]
    assert third_recovery_code
    assert third_recovery_code != second_recovery_code

    assert _login(client, initial_password).status_code == 401
    assert _login(client, recovered_password).status_code == 200

    reused_code = client.post(
        "/settings/navigation-credentials/recover",
        json={
            "username": "admin",
            "recovery_code": second_recovery_code,
            "new_password": "Should-Not-Work-2026!",
        },
    )
    assert reused_code.status_code == 401, reused_code.text

    final_status = client.get("/settings/navigation-credentials")
    assert final_status.status_code == 200, final_status.text
    assert final_status.json()["setup_required"] is False
    assert final_status.json()["recovery_configured"] is True


def test_navigation_credential_ui_exposes_complete_lifecycle():
    settings_source = (
        ROOT / "src" / "DairyOS.Web" / "src" / "components" / "SettingsTab.tsx"
    ).read_text(encoding="utf-8")
    control_source = (
        ROOT
        / "src"
        / "DairyOS.Web"
        / "src"
        / "components"
        / "NavigationVisibilityControl.tsx"
    ).read_text(encoding="utf-8")

    assert "NavigationVisibilityControl" in settings_source
    for required in (
        "Set Initial Password",
        "Recover / Reset Password",
        "Recover Password",
        "Change Password",
        "Generate Recovery Code",
        "Rotate Recovery Code",
        "/settings/navigation-credentials",
        "/settings/navigation-credentials/setup",
        "/settings/navigation-credentials/recover",
        "/settings/navigation-credentials/recovery-code",
        "/auth/me/password",
    ):
        assert required in control_source
