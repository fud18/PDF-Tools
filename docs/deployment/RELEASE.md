# Release Process

PDF Tools uses Semantic Versioning and annotated Git tags.

## Release Validation

Run the complete release check from the repository root:

    source .venv/bin/activate

    PDFTOOLS_EXPECTED_VERSION=0.4.0 \
    PDFTOOLS_RELEASE_TAG=v0.4.0 \
    ./scripts/release-check.sh

The release check verifies:

- The current branch is `main`
- The Git working tree is clean
- Local `main` matches `origin/main`
- The intended tag does not already exist
- Version metadata is consistent
- Ruff passes
- Black passes
- mypy passes
- pytest passes
- The production health endpoint works
- The public OpenAPI document is valid
- Swagger UI is available
- Authentication is enforced

## Creating an Annotated Tag

After the release check passes:

    git tag -a v0.4.0 -m "PDF Tools v0.4.0 - Production Platform"

    git push origin v0.4.0

## GitHub Release

Create a GitHub release from the annotated tag:

- Tag: `v0.4.0`
- Title: `PDF Tools v0.4.0 – Production Platform`
- Release notes: Copy the matching section from `CHANGELOG.md`

## Post-Release Verification

    git ls-remote --tags origin | grep 'v0.4.0'

    curl -s https://pdf-tools.rstechwiz.net/v1/health |
    python3 -m json.tool
