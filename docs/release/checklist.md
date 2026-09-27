# Release checklist

**DO NOT PUBLISH — LICENSE AND PUBLICATION GATES OPEN**

Preparation verification is separate from release authorization. Checked items refer
to private Orivane 0.1.0.dev0 artifacts only; repeat after approved version changes.

- [x] Naming Gate approved; coordinated Orivane rename verified before release.
- [ ] License approved, LICENSE/notice files and metadata present.
- [ ] Public repository approved and visibility change authorized separately.
- [ ] Final package metadata and public identities approved.
- [ ] Version bump approved and applied consistently.
- [x] Current lock is clean; dependency versions unchanged.
- [x] Full tests, Ruff, strict mypy and 100% runtime coverage on Python 3.11/3.12.
- [x] Three wheels/sdists built with Hatchling and repeated content comparison.
- [x] Clean wheelhouse install and CLI offline smoke on Python 3.11/3.12.
- [x] Three sdists rebuilt as wheels outside the source tree.
- [x] Current-tree/artifact secret scan and absolute-path scan.
- [ ] Full history secret audit before public conversion.
- [x] Current private README, API docs and executable offline examples prepared.
- [x] Unreleased changelog and release draft prepared.
- [ ] Tag separately authorized and created.
- [ ] GitHub Release separately authorized and created.
- [ ] PyPI credentials/ownership configured in the separately approved publication phase.
- [ ] PyPI upload separately authorized and completed under approved names.
- [ ] Post-upload clean-environment installation.
- [ ] Post-upload smoke test and release acceptance.

No upload, name reservation, tag, Release or public conversion occurs in Phase 1H.
Build evidence is produced by [packaging verification](packaging.md).
