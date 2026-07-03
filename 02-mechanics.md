## 3. Core Gameplay Mechanics

### 3.1 Primary Interaction Loop
1. **Word Reveal:** Rocket approaches a planet with a mystery word
2. **Word Presentation:** 
   - Word is spoken aloud (audio)
   - Definition/context sentence shown
   - First 2-3 letters displayed as starter
3. **Spelling Challenge:**
   - Student types remaining letters
   - Letters appear one-by-one with animation
   - Visual hint available (letter count shown)
4. **Feedback:**
   - **Correct:** Rocket engines ignite, planet clears, points awarded, celebration animation
   - **Incorrect:** Gentle "try again" cue, letter-by-letter hint revealed, no points lost
5. **Progression:** Complete 5 words to fuel rocket and travel to next planet

### 3.2 Input Methods
- **Keyboard typing** (primary): Large on-screen keyboard for visual reference
- **Letter selection** (alternative): Tap letters from floating alphabet bubbles
- **Audio support:** Word pronunciation on-demand button

### 3.3 Game States
- **Exploration Mode:** Rocket travels between planets (between word sets)
- **Challenge Mode:** Active spelling challenge for current word
- **Celebration Mode:** Success animations and progress display
- **Hint Mode:** Letter-by-letter guidance when student struggles

---

## 4. Progression System

### 4.1 Level Structure
- **Planets:** Each planet = 5-word set
- **Solar Systems:** 3 planets = 1 solar system (15 words)
- **Galaxies:** 4 solar systems = 1 galaxy (60 words)

### 4.2 Difficulty Scaffolding
| Level | Word Length | Hints Available | Time Pressure |
|-------|-------------|-----------------|---------------|
| 1-3   | 4-5 letters | Full letter count | None |
| 4-7   | 5-6 letters | First 3 letters | None |
| 8-12  | 6-7 letters | First 2 letters | None |
| 13+   | 7+ letters  | First 2 letters | Optional timer |

### 4.3 Mastery Requirements
- **Pass:** 4/5 words correct on first attempt = unlock next planet
- **Practice:** 2-3/5 correct = replay planet with same words
- **Struggle:** 0-1/5 correct = parent notification, word list review suggested
