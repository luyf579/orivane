# Release checklist

**DO NOT PUBLISH — PUBLICATION APPROVAL REQUIRED**

Checked items refer to private Orivane 0.1.0rc1 artifacts and completed preparation
checks. Publication remains a separate decision; see [RC gate](rc-gate.md).

- [x] Naming Gate approved: Orivane; accepted discoverability overlap documented.
- [x] License Gate approved: standard MIT; canonical root and exact package copies.
- [x] Package metadata: SPDX license, URLs, Python range, exact internal dependencies.
- [x] RC version 0.1.0rc1 and installed CLI version agree.
- [x] External lock records unchanged; PydanticAI/pydantic-graph 2.48.0 retained.
- [x] Three wheels built; repeated uncompressed contents match.
- [x] Three sdists built and independently rebuilt into matching wheels.
- [x] License metadata and root-byte-identical LICENSE in all wheels/sdists.
- [x] Clean Python 3.11 local wheelhouse installation.
- [x] Clean Python 3.12 local wheelhouse installation.
- [x] CLI RC smoke: ten init/validate/run/trace rounds per Python version.
- [x] Old import packages/distributions/CLI absent; old config rejected.
- [x] Telemetry migration and full privacy regression; no legacy aliases.
- [x] Full tests, Ruff, strict mypy and 100% statement/branch coverage on both versions.
- [x] Current-tree/build secret and local-path scans.
- [x] Reachable Git history, PR head refs and commit-message credential audit.
- [x] All Issue/PR body, comment and review audits.
- [x] Accessible historical Actions logs/attempts and artifact inventory audited.
- [x] Large-object audit and historical path classification.
- [x] README RC readiness, API docs, executable offline examples and draft notes.
- [ ] Historical Git identity acceptance: IDENTITY_REVIEW_REQUIRED; no history rewrite.
- [ ] Repository public, following explicit visibility approval.
- [ ] Enable and verify GitHub Private Vulnerability Reporting after public conversion.
- [ ] Remove Private :: Do Not Upload in the approved final release phase.
- [ ] Version 0.1.0 final, synchronized across packages.
- [ ] Final name availability recheck and PyPI ownership/access verification.
- [ ] Final public metadata/notes and publication approval.
- [ ] Create tag under separate authorization.
- [ ] Create GitHub Release under separate authorization.
- [ ] PyPI publish under separate authorization.
- [ ] Post-PyPI clean install, smoke and release acceptance.

No upload, name reservation, tag, Release or public conversion occurs in Phase 1I.
Build evidence is produced by [packaging verification](packaging.md). Credential
audit success does not approve disclosure of existing Git author identities.
