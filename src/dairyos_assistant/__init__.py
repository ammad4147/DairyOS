"""DairyOS Assistant: an isolated, knowledge-only teaching subsystem.

This package is deliberately a sibling of ``dairyos`` rather than a subpackage.

Two consequences follow, and both are intentional:

* ``DairyOS.spec`` collects ``dairyos`` submodules wholesale. A sibling package
  is not reached by that collection, so the Assistant executable can be built
  from its own PyInstaller ``Analysis`` without dragging the operational graph
  into it.
* Nothing in this package may import from ``dairyos``. That rule is enforced by
  test, not by convention, because the Assistant's entire purpose depends on
  having no route to operational farm data.
"""

__all__ = ["__version__"]

__version__ = "0.1.0"
