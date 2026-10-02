# Trusted Publishing configuration

Orivane v0.1.0 was published on 2026-10-02. All four projects exist on PyPI and use
normal GitHub Trusted Publishers. The public source repository uses a tag-only
workflow with four publishing environments and no static publishing credential.
No Pending Publishers remain. Future releases require explicit Maintainer approval.

## Normal publishers on PyPI

Open each project's **Settings → Publishing** and verify its normal GitHub Trusted
Publisher against the exact mapping below. Preserve the existing publishers;
normal subsequent releases do not require creating Pending Publishers.

| PyPI project | Owner | Repository | Workflow filename | Environment |
| --- | --- | --- | --- | --- |
| orivane-core | luyf579 | orivane | release.yml | pypi |
| orivane-backend-pydantic | luyf579 | orivane | release.yml | pypi-backend-pydantic |
| orivane-cli | luyf579 | orivane | release.yml | pypi-cli |
| orivane-commerce | luyf579 | orivane | release.yml | pypi-commerce |

The workflow field is the filename `release.yml`; the repository file is
`.github/workflows/release.yml`. Verify the repository is `luyf579/orivane`, ID
`1392226219`. The publisher configuration must match the names exactly.

Distinct environments preserve each project's existing publisher identity and
separate approval boundary. Verify project ownership and the complete mapping
before each approved release. OIDC issues short-lived publishing credentials;
no static PyPI username, password or API credential is stored.

## GitHub environments

The four publishing environments are `pypi`, `pypi-backend-pydantic`, `pypi-cli` and
`pypi-commerce`. All four are configured; preserve their mappings and verify each
under **Settings → Environments** before publication.

Each environment must allow only deployment **tags** matching `v*`, require reviewer
`luyf579`, and keep **Prevent self-review** disabled so the sole reviewer can approve
a release they triggered. No main, feature or unrestricted branch rule is allowed.
Review the exact approved tag commit before allowing each deployment.

GitHub documents required reviewers as public-repository-only on Free, Pro and Team
plans. Private environment availability and tag restrictions also depend on plan.
If a required control is unavailable, stop configuration and report the limitation.
Do not weaken the publishing design. Verify all four environments and their effective
protection before publication.
See [GitHub's deployment environment rules](https://docs.github.com/en/actions/reference/workflows-and-actions/deployments-and-environments).

## Workflow and artifact boundary

The workflow runs only on pushes of `v*` tags, without `workflow_dispatch`.
The build job checks out that exact tag, verifies its version, and runs the existing
packaging validator with pinned uv 0.12.18. It validates all four packages, repeated
wheel content, sdist rebuilds and offline installation. Only the first validated
`dist/` set of four wheels and four sdists is split into four GitHub Actions artifacts:
`release-orivane-core`, `release-orivane-backend-pydantic`, `release-orivane-cli` and
`release-orivane-commerce`. Each contains exactly its project's one wheel and one sdist.
All eight files come from the same validated build.

Four publish jobs run in explicit `needs` order:
`build → publish-core → publish-backend-pydantic → publish-cli → publish-commerce`.
Each downloads only its own artifact to `dist/`, uses its mapped environment, and
sets `packages-dir: dist/` on the same immutable PyPA action. These jobs do not check
out source, build or run tests. Core precedes its dependents; Commerce follows CLI
to keep the first release deterministic. Existing uploads cause failure;
`skip-existing: true` is not enabled.

Top-level permissions remain `contents: read`. Only the four publish jobs have
`id-token: write`; build has no OIDC write permission. There is no `contents: write`
or `packages: write`.

Publishing uses GitHub OIDC Trusted Publishing, without a stored PyPI username,
password or API credential. Do not create a static publishing secret. PyPA keeps
build execution outside the privileged publish job and generates publish attestations
by default. See [PyPI usage](https://docs.pypi.org/trusted-publishers/using-a-publisher/)
and the [official PyPA action](https://github.com/pypa/gh-action-pypi-publish).

## Subsequent releases

All four projects use normal Trusted Publishers. For a future version:

1. Review and obtain Maintainer approval for the exact release commit and artifacts.
2. Confirm that all four package versions and exact internal requirements are synchronized as approved.
3. Require successful tests, metadata checks and packaging CI on Python 3.11/3.12.
4. Verify project ownership and all four normal Trusted Publisher mappings.
5. Verify all four GitHub environments, required reviewer and v* tag restrictions.
6. Create and push the approved release tag at the reviewed commit.
7. Let the one build job validate all four wheels and four sdists, then split that same artifact set.
8. Review and approve Core → backend → CLI → Commerce in the existing environment/job order.
9. Verify all four PyPI project versions, eight files, hashes and publish attestations.
10. Verify fresh public installs and CLI/Commerce smoke tests, including Commerce isolation.
11. Create the approved GitHub Release with final release notes.

Ordinary main pushes run CI and do not trigger the release workflow. The workflow
does not write repository content. Documentation maintenance does not authorize
another tag or package upload.

## Historical initial bootstrap — v0.1.0

Completed on 2026-10-02. PyPI's account limit was three pending Trusted Publishers.
Different environments distinguished the initial pending identities: repository
owner, repository name, workflow filename and environment were unique among pending
GitHub publishers, without including the project name. This did not prevent a normal
Trusted Publisher from serving multiple existing projects. Pending publishers did
not create projects or reserve names until first use; all four names were rechecked.
No placeholder packages were uploaded to reserve names.
See [PyPI's pending publisher documentation](https://docs.pypi.org/trusted-publishers/creating-a-project-through-oidc/).

1. Verified that `orivane-core`, `orivane-backend-pydantic` and `orivane-cli` Pending Publishers existed with the exact mappings above.
2. Under explicit Maintainer authorization, created and pushed `v0.1.0` at the approved commit `4bc7534f43a10c13784946da754e0f4010a70a12`. The tag triggered the validated build.
3. Approved only `publish-core` in `pypi` initially; the remaining publishing jobs waited for approval.
4. Verified successful first Core publication: PyPI reified its Pending Publisher into a normal project publisher and removed its Pending record, reducing the pending count from 3 to 2.
5. Configured `orivane-commerce` with environment `pypi-commerce` and verified its complete mapping before approving any remaining publishing job.
6. Completed backend → CLI → Commerce publication in the existing job order. Verified fresh public installs and smoke tests on Python 3.11/3.12, then published the approved GitHub Release.

This sequencing is historical and is not required for normal subsequent releases
now that all four projects exist.
