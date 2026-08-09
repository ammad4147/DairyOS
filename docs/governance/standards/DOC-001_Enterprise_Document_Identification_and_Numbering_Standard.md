---
DocumentID: DOC-001
Title: Enterprise Document Identification and Numbering Standard
Version: 1.0
Status: Approved Baseline
Classification: Enterprise Controlled
Owner: Chief Enterprise Architect
Approver: Project Owner
RepositoryPath: docs/governance/standards

Dependencies:
- CONST-001 DairyOS Engineering Constitution
- META-001 Enterprise Document Metadata Standard

RelatedDocuments:
- EDI Enterprise Documentation Index
- EKR Enterprise Knowledge Repository
- EKG Enterprise Knowledge Graph Framework
- MDB Master Development Bible
- DPL Decision & Progress Ledger
---

# DOC-001

# Enterprise Document Identification and Numbering Standard


## 1. Purpose

This standard establishes the permanent identification system for all DairyOS controlled documents.


## 2. Document Identity Principle

Every controlled document shall have a unique permanent identifier.

Document IDs shall:

- never be reused
- remain traceable
- remain independent from version numbers


## 3. Document ID Format

All DairyOS controlled documents shall follow:


PREFIX-NNN


Example:

CONST-001

META-001

DOC-001

ARCH-001


## 4. Approved Prefix Families


CONST
Constitutional Documents


DAS
Documentation Architecture Stream


GOV
Governance Frameworks


META
Metadata Standards


DOC
Documentation Standards


ARCH
Enterprise Architecture


BUS
Business Architecture


DOM
Domain Architecture


DATA
Data Architecture


APP
Application Architecture


INT
Integration Architecture


SEC
Security Architecture


OPS
Operations Documents


DEV
Development Standards


TEST
Testing Standards


AI
Artificial Intelligence Governance


POL
Policies


PROC
Procedures


STD
Standards


GUIDE
Guides


REF
Reference Documents


TMP
Templates


DPL
Decision and Progress Ledger


## 5. Number Allocation


Numbers are sequential.

Example:

ARCH-001
ARCH-002
ARCH-003


Retired numbers shall never be reused.


## 6. Versioning


Document identity and version are separate.

Example:

ARCH-001

Version 1.0

Version 1.1

Version 2.0


## 7. File Naming Convention


Format:

DOCUMENT-ID_Title.md


Example:

META-001_Enterprise_Document_Metadata_Standard.md


## 8. Repository Governance


The Enterprise Documentation Index maintains:

- Document IDs
- Ownership
- Status
- Relationships
- History


## 9. Knowledge Graph Relationship


Document IDs are the primary identifiers for Enterprise Knowledge Graph relationships.


## Revision History


| Version | Description |
|---|---|
| 1.0 | Approved Baseline |


END OF DOC-001
