# Repository Rules

## Branching Strategy

- **main**: Production-ready code only. Never push directly.
- **dev**: Integration branch for feature merges before main.
- **feature/***: Per-issue branches (e.g., `feature/issue-123`).
- All work must reference a GitHub/GitLab issue number in commit messages and PR titles.

## Issue Tracking Requirement

Every change requires an associated issue:
- New features: Create feature request or enhancement issue first
- Bug fixes: Link to existing bug report if available, create new otherwise
- Commit message format: `fix: #123 - describe fix` | `feat: #456 - add capability`
- PR title must include the linked issue number (e.g., "#789 - Add user authentication")

## Pull Request Approval Policy

| Scenario | Required Approvals |
|----------|-------------------|
| Normal changes | 1+ approval from team member |
| Merge conflicts detected | 2+ approvals required |
| Breaking API changes | 2+ approvals + maintainer sign-off |
- All PRs require passing CI/CD pipeline before merge
- Reviewers must leave constructive feedback on code quality, not just functionality
- Stale PRs (>14 days) are auto-closed; reopen with updated issue reference if still needed

## Commit Conventions (Conventional Commits)

```bash
type(scope): subject #issue-number
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`  
Scopes: `api`, `ui`, `db`, `auth`, `export`, etc.

## Code Review Standards

- No merge conflicts allowed without explicit resolution discussion
- All tests must pass before PR submission (`pytest -v`)
- Documentation updates required for new public APIs or configuration changes
- Performance regressions >10% require benchmark data in PR description