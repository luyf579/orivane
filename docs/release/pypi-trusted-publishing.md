# PyPI Trusted Publishing setup

PyPI publication is currently deferred. The source repository is public, but the
packages are not yet published and no tag or GitHub Release exists. These instructions
apply to a separately authorized future publication task. The tag-only workflow uses four publishing environments. The existing core Pending
Publisher uses `pypi`; backend, CLI and Commerce configuration is in progress.

## Pending publishers on PyPI

Open PyPI **Account → Publishing** after configuration approval and inspect existing
records. Preserve the configured core Pending Publisher without deleting, changing
or resubmitting it. Create only missing mappings below, using GitHub as the provider.

| PyPI project | Owner | Repository | Workflow filename | Environment |
| --- | --- | --- | --- | --- |
| orivane-core | luyf579 | orivane | release.yml | pypi |
| orivane-backend-pydantic | luyf579 | orivane | release.yml | pypi-backend-pydantic |
| orivane-cli | luyf579 | orivane | release.yml | pypi-cli |
| orivane-commerce | luyf579 | orivane | release.yml | pypi-commerce |

The workflow field is the filename `release.yml`; the repository file is
`.github/workflows/release.yml`. Verify the repository is `luyf579/orivane`, ID
`1392226219`. The publisher configuration must match the names exactly.

Different environments distinguish the identities of the four first-use Pending
Publishers: PyPI makes repository owner, repository name, workflow filename and
environment unique among pending GitHub publishers, without including the project
name. This restriction does not mean that a normal Trusted Publisher can never
serve multiple existing projects.

A pending publisher does not create a project or reserve its name until first use.
Recheck all four names immediately before publication; another user can register
one in the meantime. Never upload placeholder packages to reserve names.
See [PyPI's pending publisher documentation](https://docs.pypi.org/trusted-publishers/creating-a-project-through-oidc/).

## GitHub environments

The four publishing environments are `pypi`, `pypi-backend-pydantic`, `pypi-cli` and
`pypi-commerce`. Preserve the existing `pypi` environment and create only missing
environments after the configuration commit passes CI. Verify each under
**Settings → Environments**.

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

## Controlled publication sequence

After separate Maintainer approval, verify all package publication gates, recheck
names, verify all four publishers and publishing environments, and review
the exact release commit and artifacts. Only then create the approved `v0.1.0` tag
at that commit. Pushing the tag triggers the publishing workflow; ordinary main
pushes do not. Do not create a temporary tag to test publishing.
Verify fresh PyPI installs and CLI smoke on Python 3.11/3.12 before creating a
separately approved GitHub Release. The workflow does not write repository content.
None of these publication actions is part of documentation maintenance.
