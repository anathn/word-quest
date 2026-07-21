# Word Quest Agent Instructions

This document provides guidance for LLM agents working in this repository.

## Overview

Word Quest is a project with documentation organized in the `/docs` directory. Agents collaborate using a story-based workflow tracked in `docs/sprint-status.yaml`.

## Documentation Structure

| File/Directory | Purpose |
|----------------|----------|
| `docs/PRD.md` | Product Requirements Document |
| `docs/epics.md` | Epic descriptions and scope |
| `docs/sprint-status.yaml` | Sprint planning and story status |
| `docs/stories/` | Project-specific story implementation guides |
| `.agent/` | Agent instructions and document templates |
| `.agent/STORY_TEMPLATE.md` | Template for creating new story files |
| `.agent/REVIEW_TEMPLATE.md` | Code review template |
| `.agent/SECURITY_CHECKLIST.md` | Security review checklist |
| `docs/01-overview.md` | Project overview |
| `docs/02-mechanics.md` | Game mechanics |
| `docs/03-motivation-tracking.md` | Motivation systems |
| `docs/04-design-tech-appendix.md` | Technical appendix |

## Workflow

### Story Status Lifecycle

Stories progress through the following states:

1. **planning** - Story is being planned and refined
2. **ready-for-dev** - Story is ready for an agent to begin development
3. **in-progress** - An agent has selected this story and is actively working on it
4. **review** - Code is complete and awaiting code review
5. **requested-changes** - Code review found issues that need to be addressed
6. **approved** - Code review passed, story is complete

### Agent Responsibilities

#### When Starting a Task

1. Check `docs/sprint-status.yaml` for stories with `ready-for-dev` status
2. **Read the detailed story file in `docs/stories/<STORY-ID>.md`**
3. Understand the acceptance criteria and technical guidance
4. Select a story to work on
5. Update the story status to `in-progress`
6. Create a feature branch named with the epic-story ID (e.g., `EPIC-1-STORY-2`)
7. Implement the story requirements following the story file guidance
8. Ensure all acceptance criteria are met
9. Write tests as specified in the story file
10. Commit changes to the feature branch
11. Update story status to `review`
12. Create a Pull Request with reference to the story file

#### When Code Review Finds Issues

1. Update story status to `requested-changes`
2. Address the feedback
3. Commit changes
4. Update story status back to `review`

#### When Reviewing Code

1. Review PRs from other agents
2. If issues found, add comments and request changes
3. If approved, update the story status to `approved`
4. Merge the PR after approval

#### When Completing an Approved Story

1. Ensure the PR is merged to main
2. Verify the story status is `approved` in `docs/sprint-status.yaml`

## Branch Naming Convention

Feature branches must follow this naming pattern:
```
{EPIC-ID}-{STORY-ID}
```

Example: `EPIC-1-STORY-3`

## Sprint Status File

The file `docs/sprint-status.yaml` tracks all epics and stories. Each story includes:
- `id`: Unique story identifier
- `title`: Brief description
- `status`: Current workflow status
- `assignee`: Agent working on the story (when in-progress)
- `branch`: Feature branch name (when in-progress)
- `pr`: Pull request number (when in review)
- `epic`: Parent epic identifier

## Debugging

Before spending time investigating a failing test or unexpected behavior, read **`docs/traps.md`**. It documents known pitfalls in this codebase — patterns that look correct but cause subtle failures — along with the fix for each one.

## Best Practices

1. Always update `docs/sprint-status.yaml` when changing story status
2. **Read the story file completely before starting implementation**
3. **Follow the technical guidance in story files**
4. **Ensure all acceptance criteria are met before marking complete**
5. Keep commits atomic and descriptive
6. Write clear PR descriptions referencing the story file
7. Address code review feedback promptly
8. Ensure documentation is updated when features change
9. Add implementation notes to the story file if you discover edge cases
10. **Always use a Python virtual environment** - Create and activate a virtual environment (`python -m venv .venv` or `python3 -m venv .venv`) before installing dependencies or running Python code. This isolates project dependencies and prevents conflicts.
11. **Always include timeouts when running unit tests** - When executing unit tests (e.g., `pytest`, `python -m unittest`), always specify a reasonable timeout to prevent test hangs from blocking CI/CD pipelines or developer workflows. Use flags like `--timeout=30` for pytest or wrap tests with timeout mechanisms.

---

## Code Review Process

All code changes go through rigorous code review before merging. The Code Review agent follows these principles:

### Review Mindset

- **Adversarial:** Assume there are bugs and security issues to find
- **Thorough:** Check every acceptance criterion
- **Security-focused:** Take security seriously on every review
- **Constructive:** Provide specific, actionable feedback

### Before Submitting Code for Review

As a developer, ensure your code is ready:

1. **Self-Review Checklist**:
   - [ ] All acceptance criteria from story file are met
   - [ ] Code follows project style guidelines
   - [ ] Unit tests written and passing
   - [ ] No hardcoded secrets or credentials
   - [ ] User inputs are validated
   - [ ] Error handling is in place
   - [ ] Story file updated with implementation notes

2. **Security Self-Check**:
   - [ ] Review `.agent/SECURITY_CHECKLIST.md`
   - [ ] No SQL injection vulnerabilities
   - [ ] No command injection vulnerabilities
   - [ ] No path traversal issues
   - [ ] No hardcoded secrets

### Code Review Resources

| File | Purpose |
|------|----------|
| `.agent/CODE_REVIEW_AGENT_INSTRUCTIONS.md` | Review agent guidelines |
| `.agent/REVIEW_TEMPLATE.md` | Review format template |
| `.agent/SECURITY_CHECKLIST.md` | Security review checklist |

### Responding to Review Feedback

1. **Critical/High Issues:** Must be fixed before merge
2. **Medium Issues:** Should be fixed or documented as deferred
3. **Low Issues/Suggestions:** At developer's discretion
4. Ask clarifying questions if feedback is unclear
5. Update story status appropriately during fixes
