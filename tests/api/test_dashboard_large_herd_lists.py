from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

DASHBOARD = (
    ROOT
    / "src"
    / "DairyOS.Web"
    / "src"
    / "components"
    / "UnifiedDashboard.tsx"
)


def source() -> str:
    return DASHBOARD.read_text(encoding="utf-8")


def test_yield_drop_watchlist_opens_complete_full_page_list():
    text = source()

    assert "setExpandedMilkList('YIELD_DROP')" in text
    assert "Complete active watchlist" in text
    assert "activeDropAlerts.map" in text


def test_production_extremes_opens_complete_full_page_lists():
    text = source()

    assert "setExpandedMilkList('PRODUCTION_EXTREMES')" in text
    assert "Complete non-overlapping production populations" in text
    assert "allTopPerformers.map" in text
    assert "allBottomPerformers.map" in text


def test_production_extremes_no_longer_have_fixed_ten_ceiling():
    text = source()

    assert (
        "const extremesOptions = [1,2,3,4,5,6,7,8,9,10]"
        not in text
    )

    assert "maximumExtremePopulation = Math.max(" in text
    assert "10," in text
    assert "allTopPerformers.length" in text
    assert "allBottomPerformers.length" in text
    assert "Array.from(" in text


def test_selected_population_is_maximum_not_equal_length_quota():
    text = source()

    assert (
        "const displayedTop = "
        "allTopPerformers.slice(0, extremesCount);"
        in text
    )

    assert (
        "const displayedBottom = "
        "allBottomPerformers.slice(0, extremesCount);"
        in text
    )

    assert "balancedExtremesPopulation" not in text


def test_frontend_does_not_merge_or_cross_extreme_populations():
    text = source()

    assert "allTopPerformers.length" in text
    assert "allBottomPerformers.length" in text

    # Each side must remain sourced only from its backend-defined
    # mutually-exclusive population.
    assert (
        "allTopPerformers.slice(0, extremesCount)"
        in text
    )

    assert (
        "allBottomPerformers.slice(0, extremesCount)"
        in text
    )


def test_full_page_does_not_force_equal_list_lengths():
    text = source()

    assert (
        "Highest Production ({allTopPerformers.length})"
        in text
    )

    assert (
        "Lowest Production ({allBottomPerformers.length})"
        in text
    )

    assert (
        "allTopPerformers.map((item, index)"
        in text
    )

    assert (
        "allBottomPerformers.map((item, index)"
        in text
    )
