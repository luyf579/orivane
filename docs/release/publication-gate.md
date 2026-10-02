# Publication gate

**SOURCE PUBLIC — V0.1.0 RELEASE COMPLETE**

- Naming Gate: **APPROVED — ORIVANE**
- License Gate: **APPROVED — MIT**
- Identity Review: **APPROVED — CLEAN PUBLICATION REPOSITORY**
- Public Repository Gate: **COMPLETE — PUBLIC**
- PyPI Gate: **COMPLETE**
- Tag: **v0.1.0 — LIGHTWEIGHT**
- GitHub Release: **PUBLISHED**
- PyPI Projects: **4**
- Trusted Publishers: **4 NORMAL**
- Pending Publishers: **0**
- PyPI files and matching artifact hashes: **8/8**
- Attestations: **8/8 PRESENT**
- Public installs: **Python 3.11 PASS; Python 3.12 PASS**

Release date: **2026-10-02**. The approved release commit and tag SHA are
`4bc7534f43a10c13784946da754e0f4010a70a12`.
[Orivane v0.1.0](https://github.com/luyf579/orivane/releases/tag/v0.1.0)
is published with Draft false and Prerelease false.
The [release workflow](https://github.com/luyf579/orivane/actions/runs/37005040358)
completed successfully with all five jobs: one validated build and four publications.

The public source repository is `luyf579/orivane`, repository ID `1392226219`.
It became public on 2026-09-28 at the approved launch baseline
`bfb9843dcefe67d33bad39fc0d78c7733e1ca738`. GitHub Private Vulnerability Reporting
is enabled; see [SECURITY](../../SECURITY.md). The [RC gate](rc-gate.md) remains a
historical preparation record.

## Completed package publication

Core, backend, CLI and Commerce 0.1.0 are published. Each project has one wheel and
one sdist from the same validated build; all eight published file hashes matched.
Fresh public installs passed on Python 3.11 and 3.12, including CLI and Commerce
smoke tests and a separate Commerce isolation check.
All eight files have publish attestations with matching public publisher identities
and subject hashes. This presence check did not perform cryptographic signature
verification.

All four projects use normal GitHub Trusted Publishers with the environments
`pypi`, `pypi-backend-pydantic`, `pypi-cli` and `pypi-commerce`.
No Pending Publishers remain, and no static publishing credential is used.

## Historical initial bootstrap — v0.1.0

Initial bootstrap completed on 2026-10-02. PyPI's account limit of three pending
publishers required Core first → reification → a slot freed → Commerce Pending
Publisher configured and verified → backend → CLI → Commerce.
The [historical bootstrap record](pypi-trusted-publishing.md#historical-initial-bootstrap--v010)
preserves the initial sequence. It is unnecessary for normal subsequent releases
now that all four projects exist.

Future tags, GitHub Releases, TestPyPI and PyPI uploads require explicit Maintainer
approval of the exact release commit and artifacts; green CI alone does not authorize
them. Follow the [completed v0.1.0 checklist](checklist.md) and
[subsequent-release process](pypi-trusted-publishing.md#subsequent-releases).
