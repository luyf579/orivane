# Publication gate

**SOURCE PUBLIC — PYPI PUBLICATION DEFERRED**

Naming Gate: **APPROVED — ORIVANE**
License Gate: **APPROVED — MIT**
Identity Review: **APPROVED — CLEAN PUBLICATION REPOSITORY**
Public Repository Gate: **COMPLETE — PUBLIC**
PyPI Gate: **DEFERRED — NOT YET PUBLISHED**
Configuration: **MULTI-PROJECT TRUSTED PUBLISHING CONFIGURATION IN PROGRESS**
Git tags: **NONE**
GitHub Releases: **NONE**

The public source repository is `luyf579/orivane`, repository ID `1392226219`.
It became public on 2026-09-28 at the approved launch baseline
`bfb9843dcefe67d33bad39fc0d78c7733e1ca738`. GitHub Private Vulnerability Reporting
is enabled; see [SECURITY](../../SECURITY.md). The [RC gate](rc-gate.md) remains a
historical preparation record.

Final release preparation synchronized 0.1.0 metadata, removed private classifiers,
validated wheels/sdists on Python 3.11/3.12 and added a tag-only Trusted Publishing
workflow. Commerce was added to source before any PyPI publication or tag. All four
current distributions use 0.1.0, omit the Private classifier and undergo packaging checks. The GitHub-only public launch created no tag, GitHub Release
or package upload. Source version 0.1.0 does not imply a published distribution.

PyPI publication will resume as a separate, explicitly authorized task. Before
publishing, recheck package names, configure and verify the four pending publishers,
verify all four publishing environments (`pypi`, `pypi-backend-pydantic`, `pypi-cli`
and `pypi-commerce`), and review the exact commit/artifacts. The existing core
Pending Publisher is configured; backend, CLI and Commerce setup is pending.
No static publishing credential is used. Follow the
[checklist](checklist.md) and [Trusted Publishing instructions](pypi-trusted-publishing.md).
Tags, GitHub Releases, TestPyPI and PyPI uploads require separate Maintainer approval;
green CI alone does not authorize them. After PyPI publication, verify fresh installs.
