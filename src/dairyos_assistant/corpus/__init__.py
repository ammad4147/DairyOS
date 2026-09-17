"""Knowledge corpus loading and integrity validation.

Standard library only. This subpackage must never import ``dairyos``, a
database driver, or an HTTP client.
"""

from dairyos_assistant.corpus.validation import (
    Finding,
    Severity,
    validate_corpus,
)

__all__ = ["Finding", "Severity", "validate_corpus"]
