"""DairyOS management Reporting.

Reporting answers farm-management questions. It is a read-only projection
layer: every report consumes an existing DairyOS authority (repository,
classifier or calculation service) and never maintains a competing ledger or
re-implements an authoritative calculation.

Layout
------
``definitions``  typed report / column / filter / result contracts
``periods``      period resolution on the farm operational-date authority
``context``      per-request read context handed to report builders
``registry``     the report catalogue (area -> report definitions)
``areas``        one module of builders per reporting area
``export``       typed CSV / Excel / PDF rendering of a report result
"""
