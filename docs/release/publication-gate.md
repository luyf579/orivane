# Publication gate

**DO NOT PUBLISH — PUBLICATION APPROVAL REQUIRED**

Naming Gate: **APPROVED — ORIVANE**
License Gate: **APPROVED — MIT**
Public Repository Gate: **OPEN**
Packaging Gate: **RC VALIDATED — PYTHON 3.11 / 3.12**
PyPI Gate: **CLOSED / DO NOT PUBLISH**

RC result: **BLOCKED — IDENTITY_REVIEW_REQUIRED**. Tests, packaging, privacy and
credential scans pass. The remaining review item is acceptance of the historical
Git author identities before publication; RC preparation continues without exposing
the repository or rewriting history.

The repository remains PRIVATE. RC preparation and a green PR do not authorize
visibility changes, removal of private classifiers, a final version, tag, GitHub
Release, TestPyPI or PyPI upload. See the [RC result](rc-gate.md) and [checklist](checklist.md).

Publication review must include the current-tree/build and full-history audits,
all PR/Issue content, Actions logs/artifacts and Git author identities. Historical
personal emails require **IDENTITY_REVIEW_REQUIRED**: the local audit masks values;
the existing Git history still contains the original identities. Maintainer review
must decide whether they may become public before any visibility change. Do not
rewrite history or alter comments automatically. Ordinary historical development
paths are not credentials; sensitive paths and credentials are blockers.

The final publication phase must also refresh name availability, verify package
ownership, approve public metadata and notes, enable/verify GitHub private vulnerability
reporting after public conversion, and verify the post-upload install. No publishing
credential is read or configured during RC preparation. No public identity, company,
website or contact email is invented.
