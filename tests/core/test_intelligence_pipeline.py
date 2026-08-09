from dairyos.intelligence.integration.intelligence_pipeline import (
    IntelligencePipeline,
)


def test_intelligence_pipeline_status():

    pipeline = IntelligencePipeline(
        gateway=None,
    )

    result = pipeline.status()

    assert result["status"] == "initialized"
