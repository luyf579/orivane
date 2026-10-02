# PyPI Trusted Publishing setup

PyPI publication is currently deferred. The source repository is public, but the
packages are not yet published and no tag or GitHub Release exists. These instructions
apply to a separately authorized future publication task. The tag-only workflow and
GitHub `pypi` environment already exist; pending publishers have not been verified.

## Pending publishers on PyPI

After separate approval, open PyPI **Account → Publishing** and create one Pending
Trusted Publisher for each project below. Select GitHub as the provider.

| PyPI project | Owner | Repository | Workflow filename | Environment |
| --- | --- | --- | --- | --- |
| orivane-core | luyf579 | orivane | release.yml | pypi |
| orivane-backend-pydantic | luyf579 | orivane | release.yml | pypi |
| orivane-cli | luyf579 | orivane | release.yml | pypi |
| orivane-commerce | luyf579 | orivane | release.yml | pypi |

The workflow field is the filename `release.yml`; the repository file is
`.github/workflows/release.yml`. Verify the repository is `luyf579/orivane`, ID
`1392226219`. The publisher configuration must match the names exactly.

A pending publisher does not create a project or reserve its name until first use.
Recheck all four names immediately before publication; another user can register
one in the meantime. Never upload placeholder packages to reserve names.
See [PyPI's pending publisher documentation](https://docs.pypi.org/trusted-publishers/creating-a-project-through-oidc/).

## GitHub environment

The existing `pypi` environment permits deployment tags matching `v*`. Before a
separately approved publication, open **Settings → Environments → pypi** and verify
its configuration rather than creating another environment.

Where supported by the account/plan, set the repository owner as a required reviewer
and select deployment **tag** rules that allow only release tags matching `v*`.
Do not add a branch rule that permits ordinary branch/PR deployments. Review the
exact approved tag commit before allowing a deployment.

GitHub documents required reviewers as public-repository-only on Free, Pro and Team
plans. Private environment availability and tag restrictions also depend on plan.
If a control is unavailable, record that limitation in the publication review;
do not upgrade a plan or weaken the publishing design to work around it. Configuration
and its effective protection must be verified when publication resumes.
See [GitHub's deployment environment rules](https://docs.github.com/en/actions/reference/workflows-and-actions/deployments-and-environments).

## Workflow and artifact boundary

The workflow runs only on pushes of `v*` tags, without `workflow_dispatch`.
The build job checks out that exact tag, verifies its version, and runs the existing
packaging validator with pinned uv 0.12.18. It validates all four packages, repeated
wheel content, sdist rebuilds and offline installation. Only the first validated
`dist/` set of four wheels and four sdists is transferred as `release-distributions`.

The publish job downloads that same artifact and runs the official PyPA publishing
action, pinned to an immutable commit. It does not check out source or rebuild.
Top-level permissions are `contents: read`; only the publish job has
`id-token: write`, and it uses environment `pypi`. There is no `contents: write`.

Publishing uses GitHub OIDC Trusted Publishing, without a stored PyPI username,
password or API credential. Do not create a static publishing secret. PyPA keeps
build execution outside the privileged publish job and generates publish attestations
by default. See [PyPI usage](https://docs.pypi.org/trusted-publishers/using-a-publisher/)
and the [official PyPA action](https://github.com/pypa/gh-action-pypi-publish).

## Controlled publication sequence

After separate Maintainer approval, verify all package publication gates, recheck
names, configure/verify the publishers and existing `pypi` environment, and review
the exact release commit and artifacts. Only then create the approved `v0.1.0` tag
at that commit. Pushing the tag triggers the publishing workflow; ordinary main
pushes do not. Do not create a temporary tag to test publishing.
Verify fresh PyPI installs and CLI smoke on Python 3.11/3.12 before creating a
separately approved GitHub Release. The workflow does not write repository content.
None of these publication actions is part of documentation maintenance.
