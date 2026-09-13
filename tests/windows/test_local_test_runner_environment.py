from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
RUNNER = REPO_ROOT / "scripts" / "test" / "Run-LocalTests.ps1"


def test_local_runner_sanitizes_postgres_environment_before_initdb() -> None:
    source = RUNNER.read_text(encoding="utf-8")

    required_postgres_environment = {
        "PGDATA",
        "PGDATABASE",
        "PGHOST",
        "PGHOSTADDR",
        "PGOPTIONS",
        "PGPASSFILE",
        "PGPASSWORD",
        "PGPORT",
        "PGSERVICE",
        "PGSERVICEFILE",
        "PGSYSCONFDIR",
        "PGUSER",
    }

    for name in required_postgres_environment:
        assert f'"{name}"' in source

    sanitize_marker = (
        'foreach ($name in $postgresEnvironmentNames) {\n'
        '    Remove-Item "Env:$name" -ErrorAction SilentlyContinue\n'
        '}'
    )
    initdb_marker = "& $initDb `"

    assert sanitize_marker in source
    assert initdb_marker in source
    assert source.index(sanitize_marker) < source.index(initdb_marker)


def test_local_runner_preserves_empty_vs_absent_environment_state() -> None:
    source = RUNNER.read_text(encoding="utf-8")

    assert "$exists = Test-Path $path" in source
    assert "Exists = $exists" in source
    assert "$state = $previousEnvironment[$name]" in source
    assert "if ($state.Exists)" in source
    assert 'Set-Item "Env:$name" -Value $state.Value' in source


def test_local_runner_manages_dairyos_and_postgres_environment_together() -> None:
    source = RUNNER.read_text(encoding="utf-8")

    assert "$dairyOsEnvironmentNames = @(" in source
    assert "$postgresEnvironmentNames = @(" in source
    assert "$managedEnvironmentNames = @(" in source
    assert "$dairyOsEnvironmentNames" in source
    assert "$postgresEnvironmentNames" in source
    assert "foreach ($name in $managedEnvironmentNames)" in source
