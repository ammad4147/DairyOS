from enum import Enum



class ResourceType(str, Enum):

    USERS = "users"

    ANIMALS = "animals"

    STORAGE = "storage"

    API_CALLS = "api_calls"
