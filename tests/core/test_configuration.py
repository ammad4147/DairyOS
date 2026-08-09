from dairyos.core.configuration.services.config_manager import ConfigurationManager

from dairyos.core.system.health import system_health

from dairyos.core.system.info import system_info



def test_configuration():

    config = ConfigurationManager()

    assert config.get(
        "currency"
    ) == "PKR"



def test_configuration_update():

    config = ConfigurationManager()

    config.set(
        "milk_unit",
        "litres"
    )

    assert config.get(
        "milk_unit"
    ) == "litres"



def test_system_health():

    result = system_health()

    assert result["status"] == "ONLINE"



def test_system_info():

    result = system_info()

    assert result["name"] == "DairyOS"
