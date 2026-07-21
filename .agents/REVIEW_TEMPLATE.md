# Code Review: <STORY-ID>

**Story:** <Story Title>  
**PR:** #<PR Number>  
**Developer:** <Developer Name>  
**Reviewer:** <Agent Name>  
**Date:** <YYYY-MM-DD>  
**Time Spent:** <N minutes>

---

## Overview

| Metric | Value |
|--------|-------|
| Files Changed | <N> |
| Lines Added | <N> |
| Lines Removed | <N> |
| Complexity | <Low/Medium/High> |

---

## Acceptance Criteria Status

Read the story file at `docs/stories/<STORY-ID>.md` and verify each criterion:

| # | Acceptance Criterion | Status | Notes |
|---|---------------------|--------|-------|
| 1 | <Criterion from story file> | ✅ / ❌ | <Notes> |
| 2 | <Criterion from story file> | ✅ / ❌ | <Notes> |
| 3 | <Criterion from story file> | ✅ / ❌ | <Notes> |

---

## Issues Found

### 🔴 Critical (Must Fix)

*Security vulnerabilities, data loss risks, or crashes*

| # | Issue | Location | Severity | Recommendation |
|---|-------|----------|----------|----------------|
| 1 | <Description> | `<file.py>:<line>` | 🔴 Critical | <How to fix> |

**None found** (if applicable)

---

### 🟠 High (Must Fix)

*Major bugs or significant security issues*

| # | Issue | Location | Severity | Recommendation |
|---|-------|----------|----------|----------------|
| 1 | <Description> | `<file.py>:<line>` | 🟠 High | <How to fix> |

**None found** (if applicable)

---

### 🟡 Medium (Should Fix)

*Code quality issues, missing tests, or minor bugs*

| # | Issue | Location | Severity | Recommendation |
|---|-------|----------|----------|----------------|
| 1 | <Description> | `<file.py>:<line>` | 🟡 Medium | <How to fix> |

**None found** (if applicable)

---

### 🟢 Low (Nice to Fix)

*Style issues or minor improvements*

| # | Issue | Location | Severity | Recommendation |
|---|-------|----------|----------|----------------|
| 1 | <Description> | `<file.py>:<line>` | 🟢 Low | <How to fix> |

**None found** (if applicable)

---

### 💡 Suggestions

*Optional improvements at developer's discretion*

1. <Suggestion 1>
2. <Suggestion 2>

**No suggestions** (if applicable)

---

## Security Review

### Security Checklist

```markdown
## Security Review Checklist

### Input Validation
- [ ] All user inputs validated
- [ ] Input sanitization in place
- [ ] No trust in client-side validation

### Authentication/Authorization
- [ ] Sensitive operations protected
- [ ] User can only access their data
- [ ] Session handling is secure

### Data Protection
- [ ] No secrets in source code
- [ ] Sensitive data encrypted
- [ ] No sensitive data in logs

### Dependencies
- [ ] No known vulnerable dependencies
- [ ] Dependencies are necessary
- [ ] Licenses are compatible

### Project-Specific (Word Quest)
- [ ] Student data handled appropriately
- [ ] No unauthorized data transmission
- [ ] Parent controls are secure

### Overall
- [ ] No obvious attack vectors
- [ ] Error handling doesn't leak info
- [ ] Rate limiting in place (if applicable)
```

### Security Findings

| Severity | Issue | Location | Recommendation |
|----------|-------|----------|----------------|
| <High/Med/Low> | <Description> | `<file.py>:<line>` | <Fix> |

**No security issues found** (if applicable)

---

## Code Quality

### Code Style

- [ ] Consistent naming conventions
- [ ] Proper indentation and formatting
- [ ] Comments where logic is complex
- [ ] No dead code or unused imports
- [ ] Functions are single-responsibility

### Architecture

- [ ] Follows project architecture patterns
- [ ] Dependencies are properly separated
- [ ] No circular dependencies
- [ ] Configuration is externalized
- [ ] Error handling is consistent

### Performance

- [ ] No obvious performance anti-patterns
- [ ] Efficient algorithms and data structures
- [ ] Memory usage is reasonable
- [ ] No unnecessary computations in loops

### Feedback

- <Feedback 1>
- <Feedback 2>

---

## Test Coverage

### Tests Verification

| Test Type | Status | Notes |
|-----------|--------|-------|
| Unit Tests | ✅ / ❌ | <Coverage quality> |
| Integration Tests | ✅ / ❌ | <What's tested> |
| Manual Testing | ✅ / ❌ | <Steps verified> |

### Test Quality Feedback

- <Comment on test quality>
- <Missing test scenarios>

---

## Documentation

- [ ] Story file updated with implementation notes
- [ ] Code has necessary comments
- [ ] Public APIs have docstrings
- [ ] README or setup docs updated if needed
- [ ] Breaking changes documented

---

## Good Work

*Acknowledge good code and smart solutions*

- <Positive feedback 1>
- <Positive feedback 2>

---

## Recommendation

**[ ] Approve** - Ready to merge

**[ ] Request Changes** - Issues must be addressed before merge

### Summary

<One-paragraph summary of review findings and recommendation>

---

## Follow-Up

- [ ] All critical/high issues addressed
- [ ] Medium issues addressed or documented as deferred
- [ ] Re-review completed
- [ ] Story file updated with implementation notes

---

**Review Status:** <Pending / Changes Requested / Approved>  
**Re-review Required:** Yes / No
