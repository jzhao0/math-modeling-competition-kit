# Security policy

## Supported line

Security fixes target the current public `v0.1.x` line.

## Do not commit secrets

Do not commit API keys, access tokens, cookies, passwords, private keys, credential files, raw account exports, or local `.env` files.

The repository ignores common local secret formats, and MMKit's submission gate includes pattern checks for common credential families. These checks are defense in depth, not a guarantee that every possible secret format will be detected.

## If a secret is exposed

1. Revoke or rotate the credential immediately at the provider.
2. Remove it from the current branch.
3. Assess whether repository history, release artifacts, package indexes, caches, or mirrors also contain it.
4. Treat history rewriting as a separate remediation decision; deleting a current file does not invalidate a credential that was already exposed.
5. Do not paste the live secret into an issue, pull request, or discussion.

## Reporting

For a suspected security issue, avoid posting live credentials publicly. Open an issue only when the report can be made without exposing a secret; otherwise use a private GitHub-supported contact path available to the repository owner.
