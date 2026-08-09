from ..defaults import DEFAULT_SETTINGS


class ConfigurationManager:


    def __init__(self):

        self.settings = DEFAULT_SETTINGS.copy()


    def get(self, key):

        return self.settings.get(key)


    def set(
        self,
        key,
        value
    ):

        self.settings[key] = value


        return value
