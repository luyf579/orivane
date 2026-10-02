# Release checklist

**SOURCE PUBLIC — PYPI PUBLICATION DEFERRED**

**MULTI-PROJECT TRUSTED PUBLISHING CONFIGURATION IN PROGRESS**

Checked items cover release preparation, GitHub-only public launch and the
subsequent four-package Commerce validation.
Package publication remains a separate decision; see the [publication gate](publication-gate.md).

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
- [x] README final install/quickstart wording, with future publication tense.
- [x] CHANGELOG: 0.1.0 entry and empty Unreleased section.
- [x] Release notes: capabilities, compatibility, limitations, privacy and MIT.
- [ ] Recheck all four PyPI names immediately before a separately approved publication.
- [x] Repository public, following explicit visibility approval on 2026-09-28.
- [x] Core Pending Trusted Publisher configured with release.yml and environment pypi.
- [ ] Backend, CLI and Commerce Pending Publishers configured with their distinct environments.
- [x] Existing GitHub pypi environment configured with deployment tag rule v*.
- [ ] Three additional GitHub publishing environments configured: pypi-backend-pydantic, pypi-cli and pypi-commerce; final publishing environment count: four.
- [ ] All four environments verified: v* tags only, reviewer luyf579, Prevent self-review false, no credential secrets.
- [ ] Maintainer approval of the exact release commit and artifacts when publication resumes.
- [x] GitHub Private Vulnerability Reporting enabled and verified.
- [ ] v0.1.0 tag under separate authorization.
- [ ] GitHub Release under separate authorization.
- [ ] PyPI publish under separate authorization.
- [ ] Post-PyPI install verification, smoke and release acceptance.

The original release preparation preceded the GitHub-only public launch; Commerce
was added to source and included in subsequent four-package validation. That launch
created no tag, GitHub Release or package upload. Remaining publication
steps are deferred to a separate task. Build evidence is produced by
[packaging verification](packaging.md); future publication follows
[Trusted Publishing](pypi-trusted-publishing.md).
