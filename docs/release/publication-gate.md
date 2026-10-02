# Publication gate

**SOURCE PUBLIC — STAGED FIRST-PUBLISH BOOTSTRAP REQUIRED**

Naming Gate: **APPROVED — ORIVANE**
License Gate: **APPROVED — MIT**
Identity Review: **APPROVED — CLEAN PUBLICATION REPOSITORY**
Public Repository Gate: **COMPLETE — PUBLIC**
PyPI Gate: **STAGED FIRST-PUBLISH BOOTSTRAP REQUIRED**
Configuration: **3/4 Pending Publishers configured**
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

Core, backend and CLI Pending Publishers are configured. Commerce is waiting for
one slot: PyPI currently permits at most three Pending Trusted Publishers per account.
All four GitHub environments are configured: `pypi`, `pypi-backend-pydantic`,
`pypi-cli` and `pypi-commerce`. No static publishing credential is used.

The separately approved initial publication must proceed in stages: core first →
core Pending Publisher reified into a normal publisher and removed → one slot freed →
Commerce Pending Publisher configured and verified → backend, CLI and Commerce jobs
continue in order. Before tagging, recheck package names and review the exact
commit/artifacts and all four environments. Follow the [checklist](checklist.md)
and [Initial bootstrap sequencing](pypi-trusted-publishing.md#initial-bootstrap-sequencing).
Tags, GitHub Releases, TestPyPI and PyPI uploads require separate Maintainer approval;
green CI alone does not authorize them. After PyPI publication, verify fresh installs.
