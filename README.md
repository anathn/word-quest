# Word Quest: Spelling Adventure 🚀

A space exploration game designed to teach 3rd grade students spelling through engaging gameplay with progress tracking.

## 🎮 Overview

**Word Quest** is an educational game where students pilot a rocket ship through different planets, each representing a spelling word challenge. Correctly spelling words fuels the rocket and helps it travel further through space.

### Key Features
- **Space Exploration Theme**: Journey through planets, solar systems, and galaxies
- **Engaging Gameplay**: Type words to progress, with Captain Cosmos as your guide
- **Progress Tracking**: Detailed analytics for students and parents
- **Motivation Systems**: Streaks, stickers, badges, and positive reinforcement
- **Parent Dashboard**: Monitor progress, customize word lists, receive weekly reports
- **Custom Word Lists**: Import your child's school spelling lists via CSV

### Target Audience
- **Grade Level**: 3rd grade (ages 8-9)
- **Session Length**: 8-12 minutes per session
- **Learning Objective**: Master spelling words through active practice

## 📚 Documentation

Comprehensive documentation is available in the `/docs` directory:

| Document | Description |
|----------|-------------|
| [`docs/01-overview.md`](docs/01-overview.md) | Game design overview and learning objectives |
| [`docs/02-mechanics.md`](docs/02-mechanics.md) | Core gameplay mechanics and input methods |
| [`docs/03-motivation-tracking.md`](docs/03-motivation-tracking.md) | Motivation systems and progress tracking details |
| [`docs/04-design-tech-appendix.md`](docs/04-design-tech-appendix.md) | Technical design, UI guidelines, and implementation notes |

## 🛠️ Setup & Installation

### Prerequisites
- Python 3.8 or higher
- pip package manager
- A display capable of running Pygame (800x600 minimum)

### Installation Steps

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd word-quest
   ```

2. **Create a virtual environment** (required)
   ```bash
   python -m venv .venv
   ```

3. **Activate the virtual environment**
   - **Windows**:
     ```bash
     .venv\Scripts\activate
     ```
   - **macOS/Linux**:
     ```bash
     source .venv/bin/activate
     ```

4. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

5. **Configure email notifications** (optional)
   ```bash
   cp .env.example .env
   ```
   Edit `.env` and add your SMTP credentials for weekly progress reports.

## 🚀 Running the Game

### Starting the Game

Once installed, run the game with:

```bash
python -m src
```

Or if a main entry point exists:

```bash
python main.py
```

### Game Modes

1. **Student Mode**: Play spelling challenges and track progress
2. **Parent Dashboard**: Configure word lists and view analytics
3. **Student Settings**: Customize avatar, difficulty, and preferences

### Controls

- **Keyboard typing**: Type letters to spell words
- **On-screen keyboard**: Visual reference for letter keys
- **Space bar**: Skip animations
- **Mouse**: Click interactive elements

## 🎯 How to Play

### Core Gameplay Loop
1. **Word Reveal**: Rocket approaches a planet with a mystery word
2. **Word Presentation**: Word is spoken aloud, definition shown, starter letters displayed
3. **Spelling Challenge**: Type the remaining letters
4. **Feedback**: 
   - **Correct**: Rocket engines ignite, celebration animation, points awarded
   - **Incorrect**: Gentle hints revealed, try again (no penalty)
5. **Progression**: Complete 5 words to fuel the rocket and travel to the next planet

### Difficulty Levels
| Level | Word Length | Hints |
|-------|-------------|-------|
| 1-3   | 4-5 letters | Full letter count |
| 4-7   | 5-6 letters | First 3 letters |
| 8-12  | 6-7 letters | First 2 letters |
| 13+   | 7+ letters  | First 2 letters |

### Progression System
- **Planets**: Each planet = 5-word set
- **Solar Systems**: 3 planets = 1 solar system (15 words)
- **Galaxies**: 4 solar systems = 1 galaxy (60 words)

### Mastery Requirements
- **Pass**: 4/5 words correct on first attempt → unlock next planet
- **Practice**: 2-3/5 correct → replay planet with same words
- **Struggle**: 0-1/5 correct → parent notification, recommended review

## 📊 Progress Tracking

### Student Metrics
- Words mastered (cumulative counter)
- Accuracy rate with trend indicators
- Words needing practice
- Longest streak achieved
- Session duration statistics

### Parent Features
- **Weekly Email Reports**: Summary of progress sent via email
- **Dashboard**: View detailed analytics and word performance
- **Word List Management**: Import, edit, or manually add spelling words
- **Progress Visualizations**: Graphs and heat maps showing improvement

## 🎨 Visual & Audio

### Visual Style
- **Theme**: Bright, friendly space exploration
- **Colors**: Deep space blue, starlight yellow, success green
- **Typography**: Large, readable fonts (24pt minimum for game text, 48pt for spelling)

### Audio
- **Background Music**: Ambient space music (toggleable)
- **Sound Effects**: Success chimes, gentle feedback for incorrect answers
- **Voice Lines**: Captain Cosmos provides encouraging commentary

### Accessibility
- Color-blind safe palette
- Text-to-speech for all words
- Keyboard navigation support
- Dyslexia-friendly font option

## 🧪 Running Tests

```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=src

# Run specific test file
pytest tests/test_word_manager.py
```

## 📁 Project Structure

```
word-quest/
├── src/                    # Main source code
│   ├── components/        # Core game components
│   │   ├── word_manager.py      # Word list management
│   │   ├── input_handler.py     # Keyboard/input handling
│   │   ├── progress_tracker.py  # Progress data collection
│   │   ├── planet_manager.py    # Level/planet management
│   │   ├── audio_system.py      # Audio playback
│   │   ├── captain_cosmos.py    # Game mascot/character
│   │   └── sticker_manager.py   # Reward system
│   ├── screens/           # Game screens
│   │   ├── spelling_challenge.py   # Main spelling gameplay
│   │   ├── planet_results.py       # Results after word set
│   │   ├── planet_transition.py    # Travel animations
│   │   ├── parent_dashboard.py     # Parent configure/view
│   │   └── student_settings.py     # Student customization
│   ├── models/            # Data models
│   ├── ui/                # UI components
│   ├── animations/        # Animation systems
│   ├── utils/             # Utility functions
│   └── analytics/         # Analytics and reporting
├── docs/                  # Documentation
│   ├── 01-overview.md
│   ├── 02-mechanics.md
│   ├── 03-motivation-tracking.md
│   ├── 04-design-tech-appendix.md
│   └── stories/           # Development stories
├── tests/                 # Unit and integration tests
├── data/                  # Game data
│   ├── badges/            # Badge definitions
│   ├── word_lists/        # Custom word lists
│   └── progress/          # Student progress data
├── assets/                # Game assets
│   └── audio/             # Sound effects and music
├── templates/             # CSV templates for word import
├── requirements.txt       # Python dependencies
├── pytest.ini            # Test configuration
└── .env.example          # Environment variable template
```

## 🤝 Development

### Agent Workflow

This project uses a story-based development workflow. See `.agent/DEV_AGENT_INSTRUCTIONS.md` for guidelines on:
- Story status lifecycle
- Branch naming conventions
- Code review process
- Sprint planning

### Key Files for Developers
- [`.agent/DEV_AGENT_INSTRUCTIONS.md`](.agent/DEV_AGENT_INSTRUCTIONS.md) - Agent guidelines
- [`docs/sprint-status.yaml`](docs/sprint-status.yaml) - Current sprint planning
- [`docs/stories/`](docs/stories/) - Detailed story implementation guides

## 📝 Contributing

1. Check `docs/sprint-status.yaml` for `ready-for-dev` stories
2. Read the detailed story file in `docs/stories/<STORY-ID>.md`
3. Create a feature branch: `{EPIC-ID}-{STORY-ID}` (e.g., `EPIC-1-STORY-3`)
4. Implement following the story file acceptance criteria
5. Write tests and ensure they pass
6. Update story status and create a Pull Request

## 🎓 Educational Alignment

- **Common Core L.3.2f**: Spell grade-appropriate words correctly
- Develops phonics and word recognition skills
- Builds vocabulary through repeated word exposure
- Reinforces letter sequencing and recognition

## 🔮 Future Roadmap

See `docs/04-design-tech-appendix.md` section 10 for expansion ideas including:
- Multiplayer cooperative modes
- Additional word categories (science, math, vocabulary)
- Voice recognition for pronunciation practice
- Mobile/tablet versions
- Teacher classroom dashboard

## 📄 License

[Add your license information here]

## 🙏 Acknowledgments

Built with ❤️ for young learners everywhere.

---

**Questions or feedback?** Contact the development team or open an issue on GitHub.