# PyPI Trusted Publishing setup

The public source repository uses a tag-only workflow with four publishing
environments. Core, backend and CLI Pending Publishers are configured; Commerce
requires one pending slot to be freed by the first core publication. These
instructions apply to a separately authorized publication task.

## Pending publishers on PyPI

Open PyPI **Account → Publishing** and inspect existing records. Preserve the
configured core, backend and CLI Pending Publishers without deleting, changing or
resubmitting them. Configure Commerce only when the initial bootstrap frees a slot,
using GitHub as the provider and the exact mapping below.

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

## Initial bootstrap sequencing

PyPI currently limits an account to three Pending Trusted Publishers at once.
For the initial Orivane publication, recheck all four project names and review the
exact release commit, artifacts and all four GitHub environments before tagging.
The approved bootstrap proceeds as follows:

1. Verify that `orivane-core`, `orivane-backend-pydantic` and `orivane-cli` Pending Publishers exist with the exact mappings above.
2. Under separate Maintainer authorization, create and push `v0.1.0` at the approved commit. The tag triggers the validated build; ordinary main pushes do not. Do not create a temporary tag to test publishing.
3. Approve only `publish-core` in `pypi`. Hold approval of the remaining publishing jobs.
4. Verify successful first core publication: PyPI reifies the core Pending Publisher into a normal project publisher and removes its Pending record, reducing the pending count from 3 to 2.
5. Configure `orivane-commerce` with environment `pypi-commerce` and verify its complete mapping before approving any remaining publishing job.
6. Continue backend → CLI → Commerce publication in the existing job order. Verify fresh public installs and CLI smoke on Python 3.11/3.12 before creating a separately approved GitHub Release.

## Subsequent releases

Once the projects exist, they use normal Trusted Publishers rather than Pending
Publishers; subsequent releases do not require this first-publication pending quota
bootstrap. Review project ownership, publisher mappings, the exact release
commit/artifacts and all four environment protections before each approved release.
The workflow does not write repository content. None of these publication actions
is part of documentation maintenance.
