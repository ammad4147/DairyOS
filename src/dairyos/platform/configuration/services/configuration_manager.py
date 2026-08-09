from dairyos.platform.configuration.models.configuration_change import (
    ConfigurationChange,
)



class ConfigurationManager:
    """
    Enterprise runtime configuration manager.
    """



    def __init__(self):

        self.values = {}

        self.history = []



    def set(
        self,
        key: str,
        value,
        changed_by: str = "system",
    ):


        old_value = self.values.get(
            key
        )


        self.values[key] = value



        self.history.append(

            ConfigurationChange(

                key=key,

                old_value=old_value,

                new_value=value,

                changed_by=changed_by,
            )
        )


        return value



    def get(
        self,
        key: str,
        default=None,
    ):

        return self.values.get(
            key,
            default,
        )



    def changes(self):

        return self.history
