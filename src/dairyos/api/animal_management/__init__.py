from dairyos.api.animal_management.router import router

# Import the reproduction route module for its registration on the shared
# animal-management router. This preserves the existing router contract.
from dairyos.api.animal_management import reproduction as _reproduction  # noqa: F401,E402

__all__ = [
    "router",
]
