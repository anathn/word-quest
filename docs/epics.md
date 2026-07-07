# Word Quest - Epics

**Last Updated:** July 4, 2026  
**Based on PRD Version:** 1.0  
**Based on Architecture Version:** 1.0  
**Total Epics:** 8  
**Total Stories:** 48  
**Total Points:** 150

---

## Epic Index

| ID | Name | Priority | Status | Points | Target Sprint |
|----|------|----------|--------|--------|---------------|
| EPIC-001 | Core Gameplay | P0 | planning | 26 | Sprint 1 |
| EPIC-002 | Progress Tracking | P0 | planning | 36 | Sprint 1 |
| EPIC-003 | Parent Dashboard | P0 | planning | 21 | Sprint 2 |
| EPIC-004 | Motivation Systems | P1 | planning | 27 | Sprint 3 |
| EPIC-005 | Visual & Audio Polish | P1 | planning | 31 | Sprint 3 |
| EPIC-006 | Accessibility | P1 | planning | 19 | Sprint 4 |
| EPIC-007 | Student Progress View | P1 | planning | 16 | Sprint 4 |
| EPIC-008 | Email Reports | P2 | planning | 17 | Sprint 5 |

---

## EPIC-001: Core Gameplay

**Priority:** P0 (Must Have)  
**Status:** in-progress  
**Progress:** 67% (21 of 26 points)
**Estimated Points:** 26  
**Target Sprint:** Sprint 1

### Description
Foundation spelling mechanics and progression system that enables the core game loop.

### Status

**Overall Progress:** 67% (21 of 26 points complete)

#### Completed Stories
- ✅ STORY-001-01 - Word presentation with audio and visual (5pts) - PR #3 merged
- ✅ STORY-001-02 - Keyboard input validation (3pts) - Merged
- ✅ STORY-001-03 - Feedback system (correct/incorrect) (5pts) - Merged
- ✅ STORY-001-04 - Hint escalation system (5pts) - Merged
- ✅ STORY-001-05 - Planet completion logic (5pts) - PR #7 merged
- ✅ STORY-001-06 - Progression between planets (3pts) - PR #8 merged

*All 6 stories complete. Epic ready for acceptance testing.*

### Goal
Enable students to spell words, receive immediate feedback, and progress through planets as they master words. This is the heart of the game—without it, there is no product.

### Scope
**Included:**
- Word presentation with audio pronunciation and visual display
- Keyboard input (physical and on-screen) with validation
- Immediate feedback system (correct/incorrect)
- Progressive hint escalation (letter count → letter-by-letter → full answer)
- Planet completion logic (5 words per planet, 80% mastery threshold)
- Progression animation between planets

**Excluded:**
- Advanced celebration animations (P1 - Visual Polish)
- Voice recognition input (future expansion)
- Multiplayer modes (future expansion)

### Stories

| ID | Title | Status | Points |
|----|-------|--------|--------|
| STORY-001-01 | Word presentation with audio and visual | ready-for-dev | 5 |
| STORY-001-02 | Keyboard input validation | ready-for-dev | 3 |
| STORY-001-03 | Feedback system (correct/incorrect) | ready-for-dev | 5 |
| STORY-001-04 | Hint escalation system | ready-for-dev | 5 |
| STORY-001-05 | Planet completion logic | ready-for-dev | 5 |
| STORY-001-06 | Progression between planets | done | 3 |

### Dependencies
- **None** - This is the foundational epic with no dependencies

### Acceptance Criteria
- [ ] All 6 stories completed and tested
- [ ] Core spelling loop functional end-to-end (word → input → feedback → progression)
- [ ] User testing confirms 3rd graders can play independently after tutorial
- [ ] Feedback occurs within 1 second of response
- [ ] Hint escalation works as designed (3 levels before full answer)

### Risks & Blockers
- **Risk:** Audio integration may be complex on some platforms
- **Mitigation:** Use pygame.mixer which has good cross-platform support
- **Blockers:** None currently

---

## EPIC-002: Progress Tracking

**Priority:** P0 (Must Have)  
**Status:** ready-for-dev  
**Progress:** 0%  
**Estimated Points:** 36  
**Target Sprint:** Sprint 1

### Description
Data collection, storage, and basic visualization of student performance metrics.

### Goal
Capture meaningful data about student performance and provide visibility into progress. This enables parents to understand learning and students to see improvement.

### Scope
**Included:**
- Session data collection (words, attempts, time, hints)
- JSON data persistence with auto-save
- Words mastered counter
- Accuracy rate calculation with trend indicators
- Words needing practice list
- Basic progress graph (fluency trend over weeks)

**Excluded:**
- Advanced analytics dashboards (future)
- Real-time collaboration features (future)
- Cloud sync (future)

### Stories

| ID | Title | Status | Points |
|----|-------|--------|--------|
| STORY-002-01 | Session data collection | ready-for-dev | 5 |
| STORY-002-02 | Data persistence (JSON) | ready-for-dev | 3 |
| STORY-002-03 | Words mastered counter | ready-for-dev | 2 |
| STORY-002-04 | Accuracy rate calculation | ready-for-dev | 5 |
| STORY-002-05 | Words needing practice list | ready-for-dev | 3 |
| STORY-002-06 | Progress graph (fluency trend) | ready-for-dev | 8 |

### Dependencies
- **EPIC-001 (Core Gameplay)** - Needs game events to track

### Acceptance Criteria
- [ ] All 6 stories completed and tested
- [ ] Data persists across game sessions
- [ ] Auto-save works after each word (no data loss on crash)
- [ ] Accuracy calculations are correct
- [ ] Trend indicators reflect actual data changes
- [ ] Graph renders correctly with sample data

### Risks & Blockers
- **Risk:** JSON file corruption could lose progress
- **Mitigation:** Implement backup on save, validate file on load
- **Blockers:** None currently

---

## EPIC-003: Parent Dashboard

**Priority:** P0 (Must Have)  
**Status:** planning  
**Progress:** 0%  
**Estimated Points:** 21  
**Target Sprint:** Sprint 2

### Description
Parent-facing interface for word list management and progress monitoring.

### Goal
Give parents control over their child's learning content and visibility into progress without overwhelming them with data.

### Scope
**Included:**
- Password-protected parent authentication
- Student profile management (name, avatar, multiple profiles)
- Word list CRUD operations (add, edit, remove, tag)
- CSV import for school spelling lists
- Weekly summary view (mastered, practice needed, trends)
- Email notification configuration (P2)

**Excluded:**
- Real-time monitoring during gameplay (privacy consideration)
- Teacher/classroom features (future)
- Mobile app version (future)

### Stories

| ID | Title | Status | Points |
|----|-------|--------|--------|
| STORY-003-01 | Parent authentication | planning | 3 |
| STORY-003-02 | Student profile management | planning | 3 |
| STORY-003-03 | Word list CRUD operations | planning | 5 |
| STORY-003-04 | CSV import for word lists | planning | 5 |
| STORY-003-05 | Weekly summary view | planning | 5 |
| STORY-003-06 | Email notification config | planning | 5 |

### Dependencies
- **EPIC-002 (Progress Tracking)** - Needs data to display

### Acceptance Criteria
- [ ] All 6 stories completed and tested
- [ ] Parent settings password-protected
- [ ] Word lists can be created, edited, imported
- [ ] Progress summary displays accurately
- [ ] Multiple student profiles supported
- [ ] CSV import handles common formats

### Risks & Blockers
- **Risk:** Parents may find setup complicated
- **Mitigation:** Clear onboarding flow, video tutorial
- **Blockers:** None currently

---

## EPIC-004: Motivation Systems

**Priority:** P1 (Should Have)  
**Status:** planning  
**Progress:** 0%  
**Estimated Points:** 27  
**Target Sprint:** Sprint 3

### Description
Positive reinforcement through streaks, badges, and character interaction to keep students engaged.

### Goal
Create an engaging experience that encourages regular practice through rewards, recognition, and friendly character guidance.

### Scope
**Included:**
- Streak counter with visual display
- Streak bonus animations (3-word, 5-word milestones)
- Achievement badge system (multiple badge types)
- Captain Cosmos mascot with voice lines
- Rocket color customization
- Space-themed sticker collection

**Excluded:**
- Leaderboards (against design principle - no competition)
- Social sharing (privacy consideration)
- In-app purchases (not applicable)

### Stories

| ID | Title | Status | Points |
|----|-------|--------|--------|
| STORY-004-01 | Streak counter | planning | 2 |
| STORY-004-02 | Streak bonus animations | planning | 5 |
| STORY-004-03 | Achievement badge system | planning | 5 |
| STORY-004-04 | Captain Cosmos character | planning | 8 |
| STORY-004-05 | Rocket customization | planning | 2 |
| STORY-004-06 | Sticker collection | planning | 5 |

### Dependencies
- **EPIC-001 (Core Gameplay)** - Needs gameplay events for triggers

### Acceptance Criteria
- [ ] All 6 stories completed and tested
- [ ] Streaks track correctly and display visually
- [ ] Badges unlock at correct milestones
- [ ] Captain Cosmos provides encouraging feedback
- [ ] Customizations persist across sessions
- [ ] No punitive mechanics (streak breaks don't penalize)

### Risks & Blockers
- **Risk:** Character voice lines may require professional recording
- **Mitigation:** Use TTS for MVP, upgrade later if budget allows
- **Blockers:** None currently

---

## EPIC-005: Visual & Audio Polish

**Priority:** P1 (Should Have)  
**Status:** planning  
**Progress:** 0%  
**Estimated Points:** 31  
**Target Sprint:** Sprint 3

### Description
Engaging space-themed visuals and supportive audio feedback that make the game enjoyable.

### Goal
Transform the functional MVP into a polished, delightful experience that kids want to return to.

### Scope
**Included:**
- Space theme visuals (deep blue background, stars, planets)
- Rocket ship sprite with engine flame animations
- Success/failure sound effects
- Background music (ambient, toggleable)
- Letter appearance animations (fade-in, bounce)
- Planet bloom effects on completion

**Excluded:**
- 3D graphics (2D sufficient for target audience)
- Complex particle systems (performance consideration)
- VR/AR support (future)

### Stories

| ID | Title | Status | Points |
|----|-------|--------|--------|
| STORY-005-01 | Space theme visuals | planning | 5 |
| STORY-005-02 | Rocket sprite with animations | planning | 8 |
| STORY-005-03 | Success/failure SFX | planning | 3 |
| STORY-005-04 | Background music | planning | 5 |
| STORY-005-05 | Letter animations | planning | 5 |
| STORY-005-06 | Planet bloom on completion | planning | 5 |

### Dependencies
- **EPIC-001 (Core Gameplay)** - Needs game states to apply visuals to

### Acceptance Criteria
- [ ] All 6 stories completed and tested
- [ ] Visual theme consistent with design guidelines
- [ ] Animations smooth (≥30 FPS)
- [ ] Audio appropriate volume levels, toggleable
- [ ] Color palette accessible (color-blind safe)
- [ ] Assets optimized for performance

### Risks & Blockers
- **Risk:** Asset creation may take longer than expected
- **Mitigation:** Use placeholder assets for MVP, iterate with polish
- **Blockers:** None currently

---

## EPIC-006: Accessibility

**Priority:** P1 (Should Have)  
**Status:** planning  
**Progress:** 0%  
**Estimated Points:** 19  
**Target Sprint:** Sprint 4

### Description
Inclusive design features ensuring the game is usable by students with diverse needs.

### Goal
Make Word Quest accessible to all learners, including those with visual, auditory, or learning differences.

### Scope
**Included:**
- Color-blind safe palette review
- Text-to-speech engine integration
- Closed captions for all audio
- Full keyboard navigation
- OpenDyslexic font option
- High contrast mode toggle

**Excluded:**
- Sign language avatars (complexity)
- Eye-tracking support (niche requirement)
- Braille display support (niche requirement)

### Stories

| ID | Title | Status | Points |
|----|-------|--------|--------|
| STORY-006-01 | Color-blind safe palette | planning | 2 |
| STORY-006-02 | Text-to-speech engine | planning | 5 |
| STORY-006-03 | Closed captions | planning | 3 |
| STORY-006-04 | Keyboard navigation | planning | 5 |
| STORY-006-05 | OpenDyslexic font | planning | 2 |
| STORY-006-06 | High contrast mode | planning | 2 |

### Dependencies
- **EPIC-005 (Visual & Audio Polish)** - Needs audio/visual to make accessible

### Acceptance Criteria
- [ ] All 6 stories completed and tested
- [ ] WCAG 2.1 Level AA compliance target met
- [ ] Game fully playable with keyboard only
- [ ] TTS works for all words with adjustable speed
- [ ] Color combinations tested with simulators
- [ ] Font options apply consistently

### Risks & Blockers
- **Risk:** TTS quality may vary across platforms
- **Mitigation:** Test on all target platforms, provide fallback options
- **Blockers:** None currently

---

## EPIC-007: Student Progress View

**Priority:** P1 (Should Have)  
**Status:** planning  
**Progress:** 0%  
**Estimated Points:** 16  
**Target Sprint:** Sprint 4

### Description
Kid-friendly progress visualization showing achievements and growth.

### Goal
Give students a sense of accomplishment and visible evidence of their improvement in an age-appropriate way.

### Scope
**Included:**
- Personal space map showing visited planets
- Achievement badge collection display
- Progress journal with readable text summaries
- Simple progress stats (words mastered, best streak, time practiced)

**Excluded:**
- Complex data visualizations (for parents instead)
- Social comparison features (against design principles)
- Exportable progress reports (for parents instead)

### Stories

| ID | Title | Status | Points |
|----|-------|--------|--------|
| STORY-007-01 | Personal space map | planning | 5 |
| STORY-007-02 | Achievement badge display | planning | 3 |
| STORY-007-03 | Progress journal | planning | 5 |
| STORY-007-04 | Simple progress stats | planning | 3 |

### Dependencies
- **EPIC-002 (Progress Tracking)** - Needs data to display
- **EPIC-004 (Motivation Systems)** - Needs badge system

### Acceptance Criteria
- [ ] All 4 stories completed and tested
- [ ] Space map visually shows progression
- [ ] Badge display engaging and clear
- [ ] Journal language age-appropriate (3rd grade reading level)
- [ ] Stats encouraging, not discouraging
- [ ] No negative comparisons or rankings

### Risks & Blockers
- **Risk:** Language may be too complex for target age
- **Mitigation:** User test with 3rd graders, iterate based on feedback
- **Blockers:** None currently

---

## EPIC-008: Email Reports

**Priority:** P2 (Nice to Have)  
**Status:** planning  
**Progress:** 0%  
**Estimated Points:** 17  
**Target Sprint:** Sprint 5

### Description
Automated weekly progress summaries sent to parents via email.

### Goal
Keep parents informed of progress without requiring them to actively check the dashboard.

### Scope
**Included:**
- Email service integration (SMTP/API)
- Progress report template design
- Scheduling system (day/time configuration)
- Unsubscribe/opt-out handling

**Excluded:**
- SMS notifications (complexity)
- Push notifications (requires mobile app)
- Real-time alerts (privacy consideration)

### Stories

| ID | Title | Status | Points |
|----|-------|--------|--------|
| STORY-008-01 | Email service integration | planning | 5 |
| STORY-008-02 | Report template design | planning | 5 |
| STORY-008-03 | Scheduling system | planning | 5 |
| STORY-008-04 | Unsubscribe handling | planning | 2 |

### Dependencies
- **EPIC-003 (Parent Dashboard)** - Needs email configuration
- **EPIC-002 (Progress Tracking)** - Needs data to report

### Acceptance Criteria
- [ ] All 4 stories completed and tested
- [ ] Emails send on schedule
- [ ] Report content accurate and readable
- [ ] Unsubscribe works immediately
- [ ] GDPR-compliant data handling
- [ ] Opt-in required (no unsolicited emails)

### Risks & Blockers
- **Risk:** Emails may be marked as spam
- **Mitigation:** Use reputable email service, include clear sender info
- **Blockers:** None currently

---

## Epic Dependencies Graph

```
EPIC-001 (Core Gameplay)
    ├── EPIC-002 (Progress Tracking)
    │     ├── EPIC-003 (Parent Dashboard)
    │     │     └── EPIC-008 (Email Reports)
    │     └── EPIC-007 (Student Progress View)
    ├── EPIC-004 (Motivation Systems)
    └── EPIC-005 (Visual & Audio Polish)
          └── EPIC-006 (Accessibility)
                └── EPIC-007 (Student Progress View)
```

---

## Sprint Allocation Summary

| Sprint | Focus | Epics | Points |
|--------|-------|-------|--------|
| Sprint 1 | MVP Foundation | EPIC-001, EPIC-002 | 62 |
| Sprint 2 | Parent Tools | EPIC-003 | 21 |
| Sprint 3 | Engagement | EPIC-004, EPIC-005 | 58 |
| Sprint 4 | Inclusion | EPIC-006, EPIC-007 | 35 |
| Sprint 5 | Polish | EPIC-008 | 17 |
| **Total** | | **8 epics** | **150** |

---

## Completion Checklist

### EPIC-001: Core Gameplay
- [ ] All stories done
- [ ] Core loop tested end-to-end
- [ ] User testing passed

### EPIC-002: Progress Tracking
- [ ] All stories done
- [ ] Data persistence verified
- [ ] Calculations validated

### EPIC-003: Parent Dashboard
- [ ] All stories done
- [ ] Authentication working
- [ ] Word management functional

### EPIC-004: Motivation Systems
- [ ] All stories done
- [ ] Rewards triggering correctly
- [ ] Character integration complete

### EPIC-005: Visual & Audio Polish
- [ ] All stories done
- [ ] Performance at target (≥30 FPS)
- [ ] Assets finalized

### EPIC-006: Accessibility
- [ ] All stories done
- [ ] WCAG AA compliance verified
- [ ] Keyboard-only play confirmed

### EPIC-007: Student Progress View
- [ ] All stories done
- [ ] Age-appropriate language verified
- [ ] Visual design engaging

### EPIC-008: Email Reports
- [ ] All stories done
- [ ] Delivery reliable
- [ ] Compliance verified

---

**Document Status:** Ready for Development  
**Next Review:** After Sprint 1 completion
