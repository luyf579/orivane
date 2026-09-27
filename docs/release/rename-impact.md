# Rename impact

**DO NOT PUBLISH — LICENSE AND PUBLICATION GATES OPEN**

Before the first public v0.1.0 release, rename cost remains bounded: this is private
development, there is no published compatibility promise, and there are three small
workspace packages. The user approved Orivane and accepted GitHub same-name risk.
The coordinated rename changes repository/distribution/import/executable identities,
current documentation and tooling. No git history or historical issue text is rewritten.

| Area | Coordinated rename scope |
| --- | --- |
| Repository | Update repository name/URLs with explicit approval |
| Distributions / imports | Update directories, imports, requirements and metadata together |
| CLI | Rename console script and module invocation documentation/tests |
| README / docs / examples | Update current instructions, links and terminology |
| pyproject / uv.lock | Change package identities, resolve without unrelated upgrades |
| GitHub Actions / tests | Update selectors and verify installed-wheel behavior |
| ADRs | Annotate historical provisional decisions and update current references |
| Issues | Preserve historical issue text; link the new decision when appropriate |
| Git history | Preserve it; no rewrite |

Full tests, type checks, wheel/sdist builds and clean installs verify the renamed packages. Inspect
dependency direction and console/import names in artifacts, not just source search.
