from dairyos.herd.dashboard.services.decision_optimization_service import DecisionOptimizationService



def test_selection():

    result = DecisionOptimizationService().optimize(

        "Milk production decline",

        {

            "Feed Investigation": 85,

            "Health Review": 70,

            "Environment Review": 60

        }

    )

    assert result.selected_action == "Feed Investigation"



def test_confidence():

    result = DecisionOptimizationService().optimize(

        "Milk decline",

        {

            "Feed": 85,

            "Health": 70

        }

    )

    assert result.confidence == 85



def test_reason():

    result = DecisionOptimizationService().optimize(

        "Milk decline",

        {

            "Feed": 85,

            "Health": 70

        }

    )

    assert "Highest" in result.reason



def test_condition_saved():

    result = DecisionOptimizationService().optimize(

        "Health issue",

        {

            "Health Review": 90,

            "Feed": 50

        }

    )

    assert result.condition == "Health issue"



def test_second_choice():

    result = DecisionOptimizationService().optimize(

        "Condition",

        {

            "Feed": 40,

            "Health": 80

        }

    )

    assert result.selected_action == "Health"



def test_low_values():

    result = DecisionOptimizationService().optimize(

        "Condition",

        {

            "A": 10,

            "B": 20

        }

    )

    assert result.confidence == 20



def test_multiple_options():

    result = DecisionOptimizationService().optimize(

        "Condition",

        {

            "A": 30,

            "B": 40,

            "C": 50

        }

    )

    assert result.selected_action == "C"



def test_confidence_type():

    result = DecisionOptimizationService().optimize(

        "Condition",

        {

            "A": 50

        }

    )

    assert isinstance(result.confidence, int)



def test_model_action():

    result = DecisionOptimizationService().optimize(

        "Condition",

        {

            "Action": 90

        }

    )

    assert result.selected_action == "Action"



def test_optimization_flow():

    result = DecisionOptimizationService().optimize(

        "Production decline",

        {

            "Feed Investigation": 85,

            "Health Review": 75

        }

    )

    assert result.selected_action == "Feed Investigation"
