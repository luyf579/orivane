# Publication gate

**DO NOT PUBLISH — PUBLICATION APPROVAL REQUIRED**

Naming Gate: **APPROVED — ORIVANE**
License Gate: **APPROVED — MIT**
Identity Review: **APPROVED — CLEAN PUBLICATION REPOSITORY**
Public Repository Gate: **OPEN — PRIVATE UNTIL SEPARATE APPROVAL**
PyPI Gate: **CLOSED — NOT YET PUBLISHED**

The final repository is `luyf579/orivane`, repository ID `1391821801`.
Its approved clean main baseline is `459e73405d21885ee548efffda324aa7c44caa1b`.
The development and pre-public archives remain permanently private and are not
publication targets. The [historical RC blocker](rc-gate.md) has been resolved.

Phase 1J-A prepares synchronized 0.1.0 metadata, removes the three private classifiers,
validates wheels/sdists on Python 3.11/3.12 and adds a tag-only Trusted Publishing
workflow. The final release PR must remain OPEN for Maintainer Release Review.
Green CI does not authorize merging, public visibility, a tag, a GitHub Release,
TestPyPI or PyPI upload.

Before the separately authorized Phase 1J-B publication, recheck PyPI names,
configure the three pending publishers and the `pypi` environment, and review the
exact commit/artifacts. No static publishing credential is used. Follow the
[checklist](checklist.md) and [Trusted Publishing instructions](pypi-trusted-publishing.md).
After publication, verify fresh PyPI installs and GitHub Private Vulnerability Reporting.
