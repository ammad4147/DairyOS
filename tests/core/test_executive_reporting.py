from dairyos.herd.dashboard.services.executive_reporting_service import ExecutiveReportingService



def test_report_creation():

    report = ExecutiveReportingService().generate(

        "Trident Dairies",

        95,

        90,

        88,

        92,

        3,

        85,

        "Review replacement pipeline"

    )

    assert report.farm_name == "Trident Dairies"



def test_green_status():

    report = ExecutiveReportingService().generate(

        "Farm",

        95,

        95,

        95,

        95,

        0,

        95,

        "Maintain operations"

    )

    assert report.farm_status == "GREEN"



def test_yellow_status():

    report = ExecutiveReportingService().generate(

        "Farm",

        75,

        75,

        75,

        75,

        5,

        75,

        "Monitor"

    )

    assert report.farm_status == "YELLOW"



def test_red_status():

    report = ExecutiveReportingService().generate(

        "Farm",

        50,

        50,

        50,

        50,

        10,

        50,

        "Immediate action"

    )

    assert report.farm_status == "RED"



def test_pending_actions():

    report = ExecutiveReportingService().generate(

        "Farm",

        90,

        90,

        90,

        90,

        4,

        90,

        "Review"

    )

    assert report.pending_actions == 4



def test_priority_message():

    report = ExecutiveReportingService().generate(

        "Farm",

        90,

        90,

        90,

        90,

        1,

        90,

        "Check health"

    )

    assert report.priority_message == "Check health"



def test_effectiveness():

    report = ExecutiveReportingService().generate(

        "Farm",

        90,

        90,

        90,

        90,

        1,

        90,

        "Stable"

    )

    assert report.management_effectiveness == 90



def test_report_scores():

    report = ExecutiveReportingService().generate(

        "Farm",

        80,

        80,

        80,

        80,

        1,

        80,

        "Stable"

    )

    assert report.health_score == 80



def test_report_model():

    report = ExecutiveReportingService().generate(

        "Farm",

        100,

        100,

        100,

        100,

        0,

        100,

        "Excellent"

    )

    assert report.farm_status == "GREEN"



def test_report_complete():

    report = ExecutiveReportingService().generate(

        "Farm",

        85,

        85,

        85,

        85,

        2,

        85,

        "Continue"

    )

    assert report.pending_actions == 2
