"""Internal protected lifecycle services used by DairyOS Settings and recovery.

This package has no operator-facing application or command-line entry point.
The normal DairyOS runtime owns the Settings reset boundary; these modules
remain internal so recovery and audit safeguards stay in one implementation.
"""
