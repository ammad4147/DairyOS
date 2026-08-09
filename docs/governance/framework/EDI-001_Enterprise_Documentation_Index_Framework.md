---
DocumentID: EDI-001
Title: Enterprise Documentation Index Framework
Version: 1.0
Status: Approved Baseline
Classification: Enterprise Controlled
Owner: Chief Enterprise Architect
Approver: Project Owner
RepositoryPath: docs/governance/framework

Dependencies:
- DAS-001 Documentation Architecture Stream
- EDS Enterprise Documentation System
- EKR Enterprise Knowledge Repository
- META-001 Enterprise Document Metadata Standard
- DOC-001 Enterprise Document Identification and Numbering Standard
- BOOTSTRAP-STR-002 Documentation Tooling Structure Update

RelatedDocuments:
- EKG-001 Enterprise Knowledge Graph Framework
- MDB Master Development Bible
- DPL Decision and Progress Ledger

MetadataSchemaVersion: 1.0
InformationSensitivity: Internal Controlled
ConfidenceLevel: Confirmed
---

# EDI-001

# Enterprise Documentation Index Framework


## 1. Purpose

The Enterprise Documentation Index (EDI) is the authoritative registry of all controlled DairyOS documents.

EDI ensures every document can be:

- identified
- located
- owned
- tracked
- related
- governed


## 2. Governing Principle

Every controlled document must exist in the Enterprise Documentation Index.

A document not registered in EDI is considered uncontrolled.


## 3. Scope

EDI applies to:

- Constitutions
- Standards
- Frameworks
- Policies
- Procedures
- Architecture Documents
- Domain Documents
- Operational Documents
- Decision Records
- Templates
- Reference Documents


## 4. EDI Position Within DairyOS


Controlled Document

↓

Enterprise Documentation Index

↓

Enterprise Knowledge Graph

↓

Enterprise Knowledge Repository


## 5. Core Responsibilities


EDI maintains:


### Document Identity

- Document ID
- Title
- Type
- Version


### Ownership

- Owner
- Approver
- Maintainer
- Review Authority


### Lifecycle

- Status
- Effective Date
- Review Date
- Revision History


### Repository

- Repository Location
- Storage Classification


### Relationships

- Dependencies
- Related Documents
- Superseded Documents


## 6. Registration Model


Every document registration shall contain:


- Document ID
- Title
- Version
- Status
- Classification
- Owner
- Approver
- Repository Location
- Dependencies
- Related Documents
- Revision History


## 7. Lifecycle States


Draft

↓

Under Review

↓

Approved

↓

Active

↓

Superseded

↓

Archived

↓

Retired


## 8. Governance Rules


Rule 1:

Document IDs shall be unique.


Rule 2:

Document records shall not be deleted.


Rule 3:

Historical versions remain traceable.


Rule 4:

Ownership changes require controlled updates.


## 9. Relationship With META-001


META-001 defines required document metadata.

EDI controls document registration.


Together they provide enterprise documentation governance.


## 10. Relationship With EKG-001


EDI provides document inventory.

EKG provides knowledge relationships.


## 11. Automation Principles


Future automation may support:

- document discovery
- metadata validation
- relationship analysis


Automation shall not approve documents.


## 12. Enterprise Knowledge System Role


The controlled lifecycle is:


Create Document

↓

Approve Document

↓

Register in EDI

↓

Store in EKR

↓

Connect in EKG

↓

Maintain Lifecycle


## Revision History


| Version | Description |
|---|---|
| 1.0 | Approved Baseline |


END OF EDI-001
