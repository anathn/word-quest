# Architecture Design - Word Quest: Spelling Adventure

**Version:** 1.0  
**Created:** July 4, 2026  
**Status:** Proposed

---

## 1. Executive Summary

Word Quest is designed as a **localhost-first educational game** with two deployment options:

1. **Primary: Pygame Desktop Application** - Native Python/Pygame application for Windows, macOS, and Linux
2. **Optional: Docker Container** - Self-contained environment for easy deployment and web-based access

This architecture prioritizes:
- **Offline-first operation** - All core features work without internet
- **Local data storage** - Student progress stored as JSON files on disk
- **Simple deployment** - Single executable or Docker container
- **Accessibility** - WCAG 2.1 AA compliance built from the ground up
- **Cost efficiency** - Zero infrastructure costs for basic deployment

**Key Decision:** Pygame as primary platform with optional Flask web wrapper for browser-based play.

---

## 2. System Overview

### 2.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    WORD QUEST GAME                           │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │   Game       │  │   Audio      │  │   Input      │       │
│  │   Engine     │  │   System     │  │   Handler    │       │
│  │   (Pygame)   │  │   (pygame)   │  │  (Keyboard)  │       │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘       │
│         │                 │                 │                │
│         └─────────────────┼─────────────────┘                │
│                           │                                  │
│                  ┌────────▼────────┐                         │
│                  │  Game State     │                         │
│                  │  Manager        │                         │
│                  └────────┬────────┘                         │
│                           │                                  │
│         ┌─────────────────┼─────────────────┐               │
│         │                 │                 │               │
│  ┌──────▼───────┐  ┌──────▼───────┐  ┌──────▼───────┐       │
│  │   Progress   │  │   Word       │  │   Parent     │       │
│  │   Tracker    │  │   Manager    │  │   Dashboard  │       │
│  │   (JSON)     │  │   (JSON)     │  │   (Pygame)   │       │
│  └──────────────┘  └──────────────┘  └──────────────┘       │
│                                                              │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
                  ┌─────────────────┐
                  │  Local Storage  │
                  │  (JSON Files)   │
                  └─────────────────┘
```

### 2.2 Deployment Options

```
OPTION 1: Native Pygame (Primary)
┌─────────────────────────────────────┐
│  User's Computer                    │
│  ┌─────────────────────────────┐   │
│  │  Word Quest.exe / App       │   │
│  │  ┌───────────────────────┐  │   │
│  │  │  Python + Pygame      │  │   │
│  │  │  Game Assets          │  │   │
│  │  │  Local JSON Data      │  │   │
│  │  └───────────────────────┘  │   │
│  └─────────────────────────────┘   │
└─────────────────────────────────────┘

OPTION 2: Docker Container (Alternative)
┌─────────────────────────────────────┐
│  User's Computer                    │
│  ┌─────────────────────────────┐   │
│  │  Docker Container           │   │
│  │  ┌───────────────────────┐  │   │
│  │  │  Python + Pygame      │  │   │
│  │  │  Flask Web Server     │  │   │
│  │  │  Game Assets          │  │   │
│  │  │  Local Volume Mount   │  │   │
│  │  └───────────────────────┘  │   │
│  └─────────────────────────────┘   │
│         │                          │
│         ▼                          │
│  Browser (localhost:5000)          │
└─────────────────────────────────────┘
```

### 2.3 Technology Stack

| Layer | Technology | Rationale |
|-------|------------|-----------|
| **Game Engine** | Pygame 2.5+ | Mature, cross-platform, perfect for 2D educational games |
| **Language** | Python 3.11+ | Easy to learn, excellent library support, cross-platform |
| **Web Wrapper** | Flask 3.0+ | Lightweight, simple, perfect for local web serving |
| **Data Storage** | JSON Files | Human-readable, no database required, easy backup |
| **Audio** | pygame.mixer | Built-in, handles TTS integration |
| **TTS Engine** | gTTS or pyttsx3 | Offline-capable text-to-speech |
| **Packaging** | PyInstaller | Creates standalone executables |
| **Container** | Docker Desktop | Easy deployment, consistent environment |

### 2.4 System Components

| Component | Responsibility | Technology |
|-----------|---------------|------------|
| **Game Engine** | Render graphics, handle game loop, manage states | Pygame |
| **Audio System** | Play music, SFX, text-to-speech | pygame.mixer + pyttsx3 |
| **Input Handler** | Keyboard and mouse input processing | Pygame events |
| **Word Manager** | Load, validate, and serve spelling words | Python classes + JSON |
| **Progress Tracker** | Record and retrieve student progress | JSON persistence |
| **Parent Dashboard** | Word list management, progress viewing | Pygame UI / Flask web |
| **Asset Manager** | Load and cache graphics, sounds | Pygame loading utilities |

---

## 3. Application Architecture

### 3.1 Architecture Pattern

**Pattern:** Event-Driven State Machine

```
┌─────────────────────────────────────────────────────────┐
│                      Game Loop                          │
│                                                         │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐          │
│  │  Input   │───▶│   Game   │───▶│  Render  │          │
│  │  Events  │    │  Update  │    │  Frame   │          │
│  └──────────┘    └──────────┘    └──────────┘          │
│       ▲               │               │                 │
│       │               ▼               │                 │
│       └───────┌───────────────┘       │                 │
│               │  State Machine        │                 │
│               │  - MainMenu           │                 │
│               │  - SpellingChallenge  │                 │
│               │  - Celebration        │                 │
│               │  - ParentDashboard    │                 │
│               │  - StudentProgress    │                 │
│               └───────────────────────┘                 │
└─────────────────────────────────────────────────────────┘
```

### 3.2 Component Design

#### 3.2.1 Core Components

```
word_quest/
├── main.py                    # Entry point, game loop
├── core/
│   ├── game_engine.py         # Main game loop, state management
│   ├── state_machine.py       # Game states (MainMenu, Gameplay, etc.)
│   └── config.py              # Configuration management
├── components/
│   ├── word_manager.py        # Word loading, validation, difficulty
│   ├── progress_tracker.py    # Session tracking, JSON persistence
│   ├── audio_system.py        # Music, SFX, TTS integration
│   └── input_handler.py       # Keyboard, mouse input processing
├── screens/
│   ├── main_menu.py           # Main menu screen
│   ├── spelling_challenge.py  # Core gameplay screen
│   ├── celebration.py         # Success animations
│   ├── parent_dashboard.py    # Parent settings and progress
│   └── student_progress.py    # Student progress view
├── ui/
│   ├── button.py              # Reusable button component
│   ├── keyboard.py            # On-screen keyboard
│   ├── progress_bar.py        # Progress indicators
│   └── typography.py          # Text rendering utilities
├── assets/
│   ├── images/                # Sprites, backgrounds
│   ├── audio/                 # Music, SFX
│   └── fonts/                 # Game fonts
├── data/                      # Runtime data (JSON)
│   ├── students.json          # Student profiles
│   ├── word_lists.json        # Spelling word lists
│   └── progress.json          # Session progress
└── utils/
    ├── validators.py          # Input validation
    ├── helpers.py             # Utility functions
    └── constants.py           # Game constants
```

#### 3.2.2 Component Responsibilities

| Component | Responsibility | Interfaces |
|-----------|---------------|------------|
| **GameEngine** | Main loop, frame rate, state transitions | `run()`, `change_state()`, `quit()` |
| **StateMachine** | Manage current game state, transitions | `push_state()`, `pop_state()`, `current_state` |
| **WordManager** | Load words, serve by difficulty, track mastery | `get_word()`, `mark_mastered()`, `get_word_list()` |
| **ProgressTracker** | Record attempts, accuracy, hints, save/load | `record_attempt()`, `get_stats()`, `export_data()` |
| **AudioSystem** | Play music, SFX, manage TTS queue | `play_music()`, `play_sfx()`, `speak()` |
| **InputHandler** | Process keyboard/mouse events | `get_input()`, `is_key_pressed()`, `get_text()` |

### 3.3 Data Flow

```
Student Input Flow:
┌─────────────┐    ┌──────────────┐    ┌──────────────┐
│  Keyboard   │───▶│ InputHandler │───▶│ GameState    │
│  (Type Word)│    │              │    │              │
└─────────────┘    └──────────────┘    └──────┬───────┘
                                               │
                                               ▼
                                      ┌──────────────────┐
                                      │ WordManager      │
                                      │ validate_answer()│
                                      └────────┬─────────┘
                                               │
                    ┌──────────────────────────┼──────────────────────────┐
                    │                          │                          │
                    ▼                          ▼                          ▼
           ┌──────────────┐           ┌──────────────┐           ┌──────────────┐
           │  Correct!    │           │  Need Hint   │           │  Incorrect   │
           │  Celebrate   │           │  Escalate    │           │  Retry Cue   │
           └──────┬───────┘           └──────┬───────┘           └──────┬───────┘
                  │                          │                          │
                  └──────────────────────────┼──────────────────────────┘
                                             │
                                             ▼
                                    ┌──────────────────┐
                                    │ ProgressTracker  │
                                    │ record_attempt() │
                                    └────────┬─────────┘
                                             │
                                             ▼
                                    ┌──────────────────┐
                                    │  Save to JSON    │
                                    │  (Auto-save)     │
                                    └──────────────────┘
```

### 3.4 API Design (Internal)

All APIs are internal Python interfaces, not REST APIs.

#### Game State Interface
```python
class GameState:
    def enter(self): pass      # Called when state becomes active
    def exit(self): pass       # Called when state becomes inactive
    def handle_events(self): pass  # Process input events
    def update(self): pass     # Update game logic
    def render(self): pass     # Draw to screen
```

#### Word Manager Interface
```python
class WordManager:
    def load_word_list(self, list_id: str) -> List[Word]
    def get_word(self, difficulty: int) -> Word
    def mark_mastered(self, word: str, student_id: str)
    def get_mastery_status(self, student_id: str) -> Dict
```

#### Progress Tracker Interface
```python
class ProgressTracker:
    def record_attempt(self, student_id: str, word: str, 
                       correct: bool, attempts: int, 
                       hints_used: int, time_spent: float)
    def get_session_stats(self, student_id: str, session_id: str) -> Dict
    def get_student_progress(self, student_id: str) -> Dict
    def export_data(self, student_id: str) -> bytes
```

---

## 4. Data Architecture

### 4.1 Database Selection

**Decision:** JSON File Storage (No Database Required)

**Rationale:**
- Offline-first requirement
- Simple data structure (profiles, words, progress)
- Human-readable for debugging
- Easy backup and migration
- No database setup or maintenance
- Scales well for expected data volume (< 100MB per student)

### 4.2 Data Models

#### Student Profile
```json
{
  "student_id": "std_001",
  "name": "Alex Johnson",
  "avatar": "astronaut_blue",
  "created_at": "2026-07-04T10:00:00Z",
  "settings": {
    "difficulty": 2,
    "hint_preference": "progressive",
    "text_to_speech": true,
    "music_enabled": true,
    "font": "opendyslexic"
  }
}
```

#### Word List
```json
{
  "list_id": "list_001",
  "name": "3rd Grade - Week 1",
  "difficulty": 2,
  "words": [
    {
      "word": "because",
      "definition": "for the reason that",
      "example": "I stayed inside because it was raining",
      "starter_letters": 2
    },
    {
      "word": "planet",
      "definition": "a large round body in space",
      "example": "Earth is a planet",
      "starter_letters": 3
    }
  ]
}
```

#### Progress Record
```json
{
  "student_id": "std_001",
  "sessions": [
    {
      "session_id": "sess_001",
      "date": "2026-07-04T10:00:00Z",
      "duration_seconds": 480,
      "planet_completed": "mercury",
      "words": [
        {
          "word": "because",
          "correct": true,
          "attempts": 1,
          "hints_used": 0,
          "time_seconds": 12.5
        },
        {
          "word": "planet",
          "correct": true,
          "attempts": 2,
          "hints_used": 1,
          "time_seconds": 18.3
        }
      ],
      "accuracy": 1.0,
      "best_streak": 5
    }
  ],
  "mastered_words": ["because", "planet", "space"],
  "needs_practice": ["astronaut"],
  "achievements": ["first_planet", "perfect_streak"],
  "total_sessions": 12,
  "total_words_mastered": 23
}
```

### 4.3 File Structure

```
data/
├── students.json              # All student profiles
├── word_lists.json            # All word lists (can be edited by parents)
├── progress/
│   ├── std_001_progress.json  # Per-student progress
│   ├── std_002_progress.json
│   └── ...
└── settings.json              # Global application settings
```

### 4.4 Data Persistence Strategy

| Data Type | Storage | Sync Strategy | Backup |
|-----------|---------|---------------|--------|
| Student Profiles | students.json | Local only | Export to JSON |
| Word Lists | word_lists.json | Local only | Export to JSON |
| Progress Data | progress/*.json | Auto-save after each word | Export to JSON |
| Settings | settings.json | Immediate save | Export to JSON |

### 4.5 Data Migration Strategy

**Versioning:** Each JSON file includes a `version` field

```json
{
  "version": "1.0",
  "last_updated": "2026-07-04T10:00:00Z",
  "data": { ... }
}
```

**Migration Process:**
1. On startup, check data version
2. If version < current, run migration script
3. Backup old data before migration
4. Migration scripts stored in `migrations/` directory

---

## 5. Security Architecture

### 5.1 Authentication & Authorization

**Parent Dashboard Protection:**
```
┌─────────────────────────────────────┐
│  Parent Dashboard Access            │
│                                     │
│  ┌─────────────────────────────┐   │
│  │  Password Required          │   │
│  │  - Stored as SHA-256 hash   │   │
│  │  - Local verification only  │   │
│  │  - Default: "parent123"     │   │
│  └─────────────────────────────┘   │
│                │                    │
│                ▼                    │
│  ┌─────────────────────────────┐   │
│  │  Access Granted:            │   │
│  │  - Word list management     │   │
│  │  - Progress viewing         │   │
│  │  - Settings configuration   │   │
│  └─────────────────────────────┘   │
└─────────────────────────────────────┘
```

**Authentication Flow:**
```python
# Password stored as hash in settings.json
"parent_password_hash": "ef92b7a89e...SHA256..."

# Verification
import hashlib
def verify_password(plain_text, stored_hash):
    return hashlib.sha256(plain_text.encode()).hexdigest() == stored_hash
```

### 5.2 Data Protection

| Data Type | Protection | Justification |
|-----------|-----------|---------------|
| Student Names | Local storage only | No external transmission |
| Progress Data | Local JSON files | No cloud storage |
| Parent Password | SHA-256 hash | Never stored in plain text |
| Word Lists | Plain text JSON | No sensitive data |

**Encryption Requirements:**
- **At Rest:** Not required (local-only, no sensitive PII)
- **In Transit:** N/A (no network transmission in basic mode)
- **Email Reports (Optional):** TLS for SMTP, opt-in only

### 5.3 Input Validation

```python
# Word Input Validation
def validate_spelling_input(text: str) -> str:
    text = text.strip().lower()           # Remove whitespace, lowercase
    text = re.sub(r'[^a-z]', '', text)    # Remove non-letters
    return text[:20]                       # Max 20 characters

# Word List Import Validation
def validate_word_import(words: List[Dict]) -> List[Word]:
    valid_words = []
    for word in words:
        if is_valid_word(word):
            valid_words.append(Word(word))
    return valid_words

def is_valid_word(word: Dict) -> bool:
    return (
        'word' in word and
        len(word['word']) >= 3 and
        len(word['word']) <= 20 and
        word['word'].isalpha()
    )
```

### 5.4 Security Headers (Flask Web Mode Only)

```python
@app.after_request
def add_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Content-Security-Policy'] = "default-src 'self'"
    return response
```

### 5.5 Secrets Management

**No External Secrets Required** for basic deployment:
- All configuration stored in local `settings.json`
- Parent password is the only secret, stored as hash
- No API keys or external service credentials needed

**For Email Reports (Optional):**
- SMTP credentials stored in `settings.json` as encrypted values
- Use environment variables for Docker deployment

---

## 6. Infrastructure Architecture

### 6.1 Deployment Options

#### Option 1: Native Pygame Application (Recommended)

**Target Platforms:** Windows, macOS, Linux

**Requirements:**
- Python 3.11+ (bundled in executable)
- No internet required
- 100MB disk space

**Distribution:**
- Windows: `WordQuest.exe` (PyInstaller)
- macOS: `WordQuest.app` (PyInstaller)
- Linux: `word_quest` binary or AppImage

**Installation:**
```bash
# Development
pip install -r requirements.txt
python main.py

# Production (build executable)
pyinstaller --onefile --windowed main.py
# Output: dist/main.exe (Windows) or dist/main (macOS/Linux)
```

#### Option 2: Docker Container

**Use Cases:**
- Easy deployment for tech-savvy parents
- Web browser access (no installation)
- Consistent environment across platforms

**Dockerfile:**
```dockerfile
FROM python:3.11-slim

# Install dependencies
RUN apt-get update && apt-get install -y \
    python3-pygame \
    python3-flask \
    xvfb \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Copy application
COPY . .

# Create volume for persistent data
VOLUME /app/data

# Expose web port (if using Flask mode)
EXPOSE 5000

# Run application
CMD ["python", "main.py"]
```

**docker-compose.yml:**
```yaml
version: '3.8'

services:
  word-quest:
    build: .
    ports:
      - "5000:5000"
    volumes:
      - ./data:/app/data
    environment:
      - GAME_MODE=web
    restart: unless-stopped
```

**Running Docker:**
```bash
# Build and run
docker-compose up -d

# Access via browser
# http://localhost:5000
```

### 6.2 System Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| **OS** | Windows 10 / macOS 10.14 / Linux | Windows 11 / macOS 12 / Linux |
| **CPU** | Dual-core 1.5 GHz | Quad-core 2.0 GHz |
| **RAM** | 2 GB | 4 GB |
| **Storage** | 100 MB | 500 MB (for assets) |
| **Graphics** | OpenGL 2.0 support | OpenGL 3.0+ |
| **Audio** | Any sound card | Any sound card |

### 6.3 Environment Configuration

**Development Environment:**
```bash
# .env file
GAME_MODE=development
DEBUG=true
LOG_LEVEL=DEBUG
DATA_DIR=./data
```

**Production Environment:**
```bash
# .env file
GAME_MODE=production
DEBUG=false
LOG_LEVEL=INFO
DATA_DIR=./data
```

**Docker Environment:**
```bash
# docker-compose.yml
environment:
  - GAME_MODE=production
  - DEBUG=false
  - DATA_DIR=/app/data
```

---

## 7. Scalability & Performance

### 7.1 Scaling Strategy

**Horizontal Scaling:** Not applicable (single-user application)

**Vertical Scaling:**
- Game runs on local machine, scales with hardware
- No server-side scaling required

**Data Scaling:**
| Metric | Expected | Maximum | Impact |
|--------|----------|---------|--------|
| Students per installation | 3-5 | 10 | Minimal |
| Words per list | 50-100 | 500 | Minimal |
| Sessions per student | 50-100 | 1000 | JSON remains fast |
| Data size per student | 100KB | 10MB | Trivial |

### 7.2 Performance Optimization

**Target Performance:**
- Frame rate: ≥ 60 FPS (target), ≥ 30 FPS (minimum)
- Response time: < 1 second for all interactions
- Load time: < 3 seconds to main menu
- Save time: < 500ms for progress persistence

**Optimization Strategies:**

1. **Asset Loading:**
   - Preload assets at startup
   - Cache loaded images and sounds
   - Lazy load non-critical assets

2. **Audio Optimization:**
   - Use compressed audio formats (OGG)
   - Pool audio channels to prevent overlap
   - Preload common SFX

3. **Data Persistence:**
   - Batch writes (save after each word, not each keystroke)
   - Async file I/O where possible
   - Compress old session data

4. **Rendering:**
   - Use sprite batching for stars/background
   - Limit particle effects
   - Cap frame rate to 60 FPS

### 7.3 Load Testing Plan

**Test Scenarios:**
1. **Startup Test:** Measure time from launch to main menu
2. **Word Challenge Test:** Measure response time for 100 consecutive words
3. **Progress Load Test:** Load progress data for 100 sessions
4. **Memory Test:** Run game for 2 hours, monitor memory usage

**Acceptance Criteria:**
- All tests pass within performance targets
- No memory leaks (memory stable over 2-hour test)
- No frame drops below 30 FPS

---

## 8. Reliability & Availability

### 8.1 High Availability Design

**Single-User Application:**
- No uptime requirements (runs locally)
- No failover needed
- Data is local and persistent

### 8.2 Disaster Recovery

**Data Backup Strategy:**
```
┌─────────────────────────────────────────────────────────┐
│  Automatic Backup                                       │
│                                                         │
│  ┌──────────────┐    ┌──────────────┐    ┌────────────┐│
│  │  Daily Auto  │───▶│  Backup      │───▶│  backup/   ││
│  │  Backup      │    │  (timestamp) │    │  *.json    ││
│  └──────────────┘    └──────────────┘    └────────────┘│
│                                                         │
│  ┌──────────────┐    ┌──────────────┐    ┌────────────┐│
│  │  Manual      │───▶│  Export      │───▶│  user-     ││
│  │  Export      │    │  Function    │    │  selected/ ││
│  └──────────────┘    └──────────────┘    └────────────┘│
└─────────────────────────────────────────────────────────┘
```

**Recovery Procedures:**
1. **Corrupted Data:** Restore from backup in `backup/` directory
2. **Accidental Deletion:** Use export file from parent dashboard
3. **Reinstallation:** Copy data folder to new installation

### 8.3 Monitoring & Alerting

**Local Monitoring:**
```python
# Logging configuration
import logging

logging.basicConfig(
    filename='logs/word_quest.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Log key events
logging.info(f"Student {student_id} completed word: {word}")
logging.warning(f"Student {student_id} failed word 3 times: {word}")
logging.error(f"Error saving progress: {error}")
```

**Alerting (Optional - Email Reports):**
- Weekly progress email to parents
- Alert when student struggles (0-1/5 correct on planet)

---

## 9. Cost Analysis

### 9.1 Infrastructure Costs

**Option 1: Native Pygame**
| Item | Cost | Notes |
|------|------|-------|
| Development | $0 | Open source tools |
| Distribution | $0 | Free executable |
| Hosting | $0 | No hosting required |
| **Total** | **$0** | One-time development only |

**Option 2: Docker Deployment**
| Item | Cost | Notes |
|------|------|-------|
| Docker Desktop | $0 | Free for personal use |
| Development | $0 | Open source tools |
| **Total** | **$0** | One-time development only |

### 9.2 Operational Costs

| Cost Type | Amount | Frequency |
|-----------|--------|-----------|
| Server Costs | $0 | N/A (localhost) |
| Bandwidth | $0 | N/A (offline) |
| Storage | $0 | User's disk space |
| Support | Variable | Parent/teacher time |

### 9.3 Cost Optimization

**Already Optimized:**
- No cloud infrastructure costs
- No third-party service dependencies
- No licensing fees
- Open source technology stack

---

## 10. Architecture Decision Records

### ADR-001: Pygame as Primary Game Engine

**Status:** Accepted

**Context:**
We need a game engine that is:
- Cross-platform (Windows, macOS, Linux)
- Easy to develop with
- Suitable for 2D educational games
- Free and open source
- Stable and well-maintained

**Decision:**
Use Pygame 2.5+ as the primary game engine.

**Rationale:**
- Mature, stable library with 20+ years of history
- Perfect fit for 2D games with simple graphics
- Large community and extensive documentation
- No licensing costs
- Easy to package with PyInstaller for distribution

**Consequences:**
- **Positive:** Fast development, easy deployment, no costs
- **Positive:** Works offline, no external dependencies
- **Negative:** Limited to 2D graphics
- **Negative:** Performance not suitable for 3D or complex games (not needed for this project)

---

### ADR-002: JSON File Storage (No Database)

**Status:** Accepted

**Context:**
We need a data storage solution that:
- Works offline
- Is simple to implement
- Allows easy backup and migration
- Is human-readable for debugging
- Scales for expected data volume

**Decision:**
Use JSON files for all data storage.

**Rationale:**
- No database setup or maintenance required
- Human-readable format for debugging
- Easy to backup, restore, and migrate
- Python has built-in JSON support
- Scales well for expected data (< 10MB per student)

**Consequences:**
- **Positive:** Zero setup, easy debugging, simple backup
- **Positive:** No database driver dependencies
- **Negative:** No built-in query language (not needed)
- **Negative:** No concurrent access (single-user app)

---

### ADR-003: Local-First Architecture

**Status:** Accepted

**Context:**
The game must:
- Work without internet
- Protect student privacy
- Be simple to deploy
- Have zero infrastructure costs

**Decision:**
Design as a local-first application with all data stored on user's device.

**Rationale:**
- Meets offline requirement from PRD
- No data leaves user's device (privacy)
- Zero infrastructure costs
- Simple deployment (single executable or Docker)

**Consequences:**
- **Positive:** Works offline, protects privacy, zero costs
- **Positive:** Simple deployment and maintenance
- **Negative:** No cross-device sync (can be added later)
- **Negative:** No cloud backup (user must manage backups)

---

### ADR-004: Docker as Optional Deployment

**Status:** Accepted

**Context:**
Some users may prefer:
- Browser-based access
- Easy deployment without Python installation
- Consistent environment across platforms

**Decision:**
Provide Docker container as optional deployment method.

**Rationale:**
- Familiar to tech-savvy users
- Consistent environment
- Easy to update (pull new image)
- Volume mounts for persistent data

**Consequences:**
- **Positive:** Easy deployment, consistent environment
- **Positive:** Browser access via Flask web mode
- **Negative:** Requires Docker installation
- **Negative:** Slightly larger footprint than native

---

## 11. Risks & Mitigations

### 11.1 Technical Risks

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| **Pygame compatibility issues** | Medium | Low | Test on all target platforms early |
| **Audio driver conflicts** | Medium | Medium | Graceful fallback if audio fails |
| **Large JSON files slow** | Low | Low | Archive old sessions, compress data |
| **Memory leaks in long sessions** | Medium | Low | Profile memory usage, implement restart prompt |
| **Docker graphics issues** | Medium | Medium | Provide native option as fallback |

### 11.2 Operational Risks

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| **Data loss from disk failure** | High | Low | Auto-backup, export functionality |
| **User can't install software** | Medium | Medium | Provide Docker option, detailed guides |
| **Parent can't manage word lists** | Medium | High | Simple UI, CSV import, tutorials |
| **Student loses progress** | High | Low | Auto-save after each word |

### 11.3 Mitigation Strategies

**Data Loss Prevention:**
```python
# Auto-backup before any data modification
def save_progress(progress_data):
    # Backup current data
    backup_file = f"backup/progress_{datetime.now().isoformat()}.json"
    shutil.copy("data/progress.json", backup_file)
    
    # Save new data
    with open("data/progress.json", "w") as f:
        json.dump(progress_data, f, indent=2)
```

**Graceful Degradation:**
```python
# Audio system with fallback
class AudioSystem:
    def __init__(self):
        try:
            pygame.mixer.init()
            self.audio_available = True
        except:
            self.audio_available = False
            logging.warning("Audio not available, continuing without sound")
    
    def play_sfx(self, sound):
        if self.audio_available:
            sound.play()
```

---

## 12. Future Considerations

### 12.1 Planned Enhancements

**Phase 2 (Post-MVP):**
- Cloud sync option (optional, opt-in)
- Multi-device progress sync
- Teacher dashboard for classrooms
- Advanced analytics and reports
- More game modes and challenges

**Phase 3 (Long-term):**
- Mobile app (React Native or Flutter)
- Web app (React + Flask API)
- Multiplayer features
- Custom themes and avatars
- Integration with school systems

### 12.2 Technical Debt

**Known Technical Debt:**
1. **JSON Storage:** May need migration to SQLite for larger deployments
2. **No API Layer:** Internal APIs not designed for external access
3. **Limited Testing:** Initial focus on functionality over test coverage

**Refactoring Plan:**
- Monitor data size; migrate to SQLite if > 50MB per student
- Add API layer if cloud sync is added
- Increase test coverage to 80% before Phase 2

### 12.3 Evolution Path

```
Current State (v1.0)
├── Pygame native app
├── JSON file storage
├── Local-only operation
└── Basic parent dashboard

Phase 2 (v2.0)
├── Optional cloud sync
├── SQLite for larger datasets
├── Enhanced analytics
└── Teacher dashboard

Phase 3 (v3.0)
├── Mobile apps (iOS/Android)
├── Web application
├── Multiplayer features
└── Advanced customization
```

---

## Appendix A: Directory Structure

```
word_quest/
├── .agent/
│   └── ARCHITECTURE_AGENT_INSTRUCTIONS.md
├── docs/
│   ├── PRD.md
│   ├── architecture.md          # This document
│   └── implementation-guide.md
├── src/
│   ├── main.py                  # Entry point
│   ├── core/
│   │   ├── game_engine.py
│   │   ├── state_machine.py
│   │   └── config.py
│   ├── components/
│   │   ├── word_manager.py
│   │   ├── progress_tracker.py
│   │   ├── audio_system.py
│   │   └── input_handler.py
│   ├── screens/
│   │   ├── main_menu.py
│   │   ├── spelling_challenge.py
│   │   ├── celebration.py
│   │   ├── parent_dashboard.py
│   │   └── student_progress.py
│   ├── ui/
│   │   ├── button.py
│   │   ├── keyboard.py
│   │   ├── progress_bar.py
│   │   └── typography.py
│   ├── utils/
│   │   ├── validators.py
│   │   ├── helpers.py
│   │   └── constants.py
│   └── data/                    # Runtime data
│       ├── students.json
│       ├── word_lists.json
│       ├── progress/
│       └── settings.json
├── assets/
│   ├── images/
│   │   ├── rocket.png
│   │   ├── planets/
│   │   ├── backgrounds/
│   │   └── ui/
│   ├── audio/
│   │   ├── music/
│   │   ├── sfx/
│   │   └── voice/
│   └── fonts/
│       ├── opendyslexic.ttf
│       └── game_font.ttf
├── tests/
│   ├── test_word_manager.py
│   ├── test_progress_tracker.py
│   └── test_game_engine.py
├── docker/
│   ├── Dockerfile
│   └── docker-compose.yml
├── requirements.txt
├── setup.py
├── README.md
└── .env.example
```

---

## Appendix B: Technology Comparison

### Game Engine Options

| Engine | Pros | Cons | Verdict |
|--------|------|------|---------|
| **Pygame** | Simple, mature, Python, free | 2D only, no IDE | ✅ **Selected** |
| **Kivy** | Cross-platform, touch support | Steeper learning, larger size | ❌ |
| **Panda3D** | 3D support, powerful | Overkill, complex | ❌ |
| **Unity** | Powerful, asset store | Heavy, C#, overkill | ❌ |
| **Godot** | Lightweight, GDScript | Less Python, smaller community | ❌ |

### Storage Options

| Storage | Pros | Cons | Verdict |
|---------|------|------|---------|
| **JSON Files** | Simple, human-readable, no setup | No queries, single-user | ✅ **Selected** |
| **SQLite** | Queries, ACID, embedded | More complex, binary | ⚠️ Future |
| **PostgreSQL** | Full-featured, scalable | Overkill, setup required | ❌ |
| **Firebase** | Real-time, cloud | Requires internet, costs | ❌ |

---

**Document Version:** 1.0  
**Last Updated:** July 4, 2026  
**Author:** Architecture Agent  
**Review Status:** Pending
