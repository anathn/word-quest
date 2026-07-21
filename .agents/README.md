# Multi-Agent Development System

A collaborative AI agent framework for managing software development workflows with specialized agent roles. This framework provides a structured approach for AI agents to work together on any software project.

## Agent Roles

| Agent | Role | Responsibilities |
|-------|------|------------------|
| **Product Manager** | Requirements & Specifications | Define product requirements, create PRD, refine feature requests |
| **Project Manager** | Sprint Planning & Tracking | Create epics, manage sprint status, track progress |
| **Developer** | Implementation | Write code, implement stories, create tests |
| **Code Review** | Quality Assurance | Review code changes, security analysis, approve/reject PRs |

## Documentation

### Agent Instructions

- [`CODE_REVIEW_AGENT_INSTRUCTIONS.md`](./CODE_REVIEW_AGENT_INSTRUCTIONS.md) - Code review guidelines and security checklists
- [`DEV_AGENT_INSTRUCTIONS.md`](./DEV_AGENT_INSTRUCTIONS.md) - Development workflow and best practices
- [`PRODUCT_MANAGER_INSTRUCTIONS.md`](./PRODUCT_MANAGER_INSTRUCTIONS.md) - Product requirements and feature refinement
- [`PROJECT_MANAGER_INSTRUCTIONS.md`](./PROJECT_MANAGER_INSTRUCTIONS.md) - Epic creation and sprint tracking

## Workflow

### Story Lifecycle

```
planning → ready-for-dev → in-progress → review → approved
                              ↓
                      requested-changes
```

### Branch Naming Convention

Feature branches follow the pattern: `{EPIC-ID}-{STORY-ID}`

Example: `EPIC-1-STORY-3`

### Code Review Process

1. Developer completes story and updates status to `review`
2. Code Review agent performs thorough review including:
   - Acceptance criteria verification
   - Code quality analysis
   - Security vulnerability scanning
   - Test coverage verification
3. If issues found → status becomes `requested-changes`
4. If approved → status becomes `approved` and PR can be merged

## Customization

To adapt this framework to your project:

1. Update agent instructions with project-specific guidelines
2. Create project documentation in `docs/` directory
3. Initialize `docs/sprint-status.yaml` with your project's epics and stories
4. Add project-specific security checklists and templates

## Security

Security is taken seriously in this framework. The Code Review agent follows comprehensive security checklists including:

- Input validation and sanitization
- Authentication and authorization checks
- Data protection and encryption
- Common vulnerability scanning (SQL injection, XSS, command injection, etc.)

## Project Context

This agent framework is project-agnostic and can be adapted to any software development project. It supports:

- Story-based development workflow
- Epic and sprint tracking via `docs/sprint-status.yaml`
- Detailed story implementation guides in `docs/stories/`
- Rigorous code review before merging

## Usage

Agents in this system should:

1. Read relevant agent instruction files before starting tasks
2. Follow the established workflow for story progression
3. Update `docs/sprint-status.yaml` when changing story status
4. Create detailed story files in `docs/stories/` for development guidance
5. Follow security best practices in all implementations

## Getting Started

To set up this framework for a new project:

1. Review and customize agent instruction files for your project needs
2. Create initial project documentation in `docs/`
3. Define epics and stories in `docs/sprint-status.yaml`
4. Begin with the first sprint planning

## License

Internal use only.
