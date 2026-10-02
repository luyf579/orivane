# Release checklist

**V0.1.0 RELEASE COMPLETE**

Orivane v0.1.0 was published on 2026-10-02. The approved release commit and
lightweight tag `v0.1.0` point to `4bc7534f43a10c13784946da754e0f4010a70a12`.
The [publication gate](publication-gate.md) records release acceptance.
Future releases require explicit Maintainer approval.

## Preparation completed

- [x] Naming Gate approved: Orivane; accepted discoverability overlap documented.
- [x] License Gate approved: standard MIT; canonical root and exact package copies.
- [x] Clean publication repository: final repository ID 1392226219.
- [x] Identity audit: canonical noreply history, verified before and after public launch.
- [x] Final package names: orivane-core, orivane-backend-pydantic, orivane-cli, orivane-commerce.
- [x] Final version metadata: 0.1.0; SPDX license, URLs, Python range, exact internal dependencies where present; Commerce depends only on Pydantic.
- [x] All four distributions omit the Private classifier.
- [x] External lock records unchanged; PydanticAI/pydantic-graph 2.48.0 retained.
- [x] Wheel build: four final 0.1.0 wheels; repeated uncompressed contents match.
- [x] sdist build: four final 0.1.0 sdists rebuilt into matching wheels.
- [x] License metadata and root-byte-identical LICENSE in all wheels/sdists.
- [x] Clean install: Python 3.11 local wheelhouse.
- [x] Clean install: Python 3.12 local wheelhouse.
- [x] Separate CLI and Commerce installs: CLI resolves Core/backend; Commerce pulls in neither Core/backend nor CLI.
- [x] CLI final smoke: version 0.1.0 and ten init/validate/run/trace rounds per Python version.
- [x] Old import packages/distributions/CLI absent; old config rejected.
- [x] Telemetry migration and full privacy regression; no legacy aliases.
- [x] Full tests, Ruff, strict mypy and 100% statement/branch coverage on both versions.
- [x] Current-tree/build secret and local-path scans.
- [x] README final install/quickstart wording that remains accurate across publication.
- [x] CHANGELOG: 0.1.0 entry and empty Unreleased section.
- [x] Release notes: capabilities, compatibility, limitations, privacy and MIT.

- [x] Repository public, following explicit visibility approval on 2026-09-28.
- [x] Multi-project workflow configured: one validated build and Core → backend-pydantic → CLI → Commerce publication order.
- [x] Four GitHub environments configured: pypi, pypi-backend-pydantic, pypi-cli and pypi-commerce.
- [x] All four environments verified: v* tags only, reviewer luyf579, Prevent self-review false, no credential secrets.
- [x] GitHub Private Vulnerability Reporting enabled and verified.

## Publication completed

- [x] Final PyPI names checked immediately before publication.
- [x] Exact release commit and artifacts approved by the Maintainer.
- [x] v0.1.0 lightweight tag created at the approved release commit.
- [x] Core publication.
- [x] Core Pending Publisher reified into a normal Trusted Publisher.
- [x] Commerce Pending Publisher configured and verified after Core freed a slot.
- [x] Backend publication.
- [x] CLI publication.
- [x] Commerce publication.
- [x] Four normal GitHub Trusted Publishers verified.
- [x] Zero Pending Publishers verified.
- [x] 8/8 PyPI files verified: four wheels and four sdists.
- [x] 8/8 artifact hashes matched the validated release build.
- [x] 8/8 publish attestations present; publisher identities and subject hashes matched.
- [x] Python 3.11 fresh public installation.
- [x] Python 3.12 fresh public installation.
- [x] CLI public smoke.
- [x] Commerce public smoke.
- [x] Commerce isolation: no Core, backend, CLI or PydanticAI installed.
- [x] GitHub Release published as Orivane v0.1.0, with Draft false and Prerelease false.

## Historical initial bootstrap — v0.1.0

Initial bootstrap completed successfully on 2026-10-02. The GitHub-only public
source launch on 2026-09-28 preceded all tag and package publication. PyPI's account
limit of three pending publishers required Core first → reification → one slot freed
→ Commerce Pending Publisher configured → backend → CLI → Commerce.
All four projects now exist and use normal Trusted Publishers; future releases use
the [subsequent-release process](pypi-trusted-publishing.md#subsequent-releases).
The [historical bootstrap record](pypi-trusted-publishing.md#historical-initial-bootstrap--v010)
preserves the initial sequence. Build evidence comes from
[packaging verification](packaging.md). Attestation presence checks did not perform
cryptographic signature verification.
