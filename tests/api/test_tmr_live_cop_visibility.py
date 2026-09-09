from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

TMR = ROOT / "src/dairyos/api/tmr.py"
COML_UI = ROOT / "src/DairyOS.Web/src/components/COML.tsx"


def test_today_uses_live_tmr_until_daily_lock_exists():
    text = TMR.read_text(encoding="utf-8")

    block = text[
        text.index("def tmr_feed_cost_for_period("):
        text.index('@router.get("")')
    ]

    assert "live_today = build_live_tmr_summary(" in block
    assert 'basis = "LIVE_TMR_PENDING_NOON_LOCK"' in block
    assert 'basis = "LOCKED_DAILY_TMR"' in block
    assert 'basis = "DAILY_TMR_SNAPSHOT_MISSING"' in block


def test_live_tmr_fallback_is_today_only():
    text = TMR.read_text(encoding="utf-8")

    block = text[
        text.index("def tmr_feed_cost_for_period("):
        text.index('@router.get("")')
    ]

    assert "elif day == today and live_today is not None:" in block


def test_coml_does_not_render_missing_cost_as_zero():
    text = COML_UI.read_text(encoding="utf-8")

    assert (
        "value === null || value === undefined || value === ''"
        in text
    )
    assert "return 'N/A';" in text
