# Badge Images

This directory contains custom badge icon images for the achievement badge system.

## File Naming Convention

Badge images should be named with the badge ID and `.png` extension:
- `speed_speller.png`
- `perseverance.png`
- `perfect_planet.png`
- `streak_master.png`
- `word_warrior.png`
- `comeback_kid.png`

## Image Specifications

- **Format**: PNG (supports transparency)
- **Recommended Size**: 64x64 pixels
- **Color Mode**: RGBA (32-bit with alpha channel)

## Hybrid Rendering Approach

The badge system uses a hybrid approach:
1. **Asset-based**: If an image exists in this directory, it will be loaded and used
2. **Procedural fallback**: If no image exists, the badge is rendered procedurally based on rarity

This allows for:
- Custom-designed badges for special achievements
- Easy prototyping with procedural graphics
- Mixed approach (some badges with custom art, others procedurally generated)

## Creating New Badge Icons

When designing new badge icons:
1. Create a 64x64 PNG file
2. Use transparent background for best results
3. Follow the space/science theme of the game
4. Ensure the design is recognizable at small sizes
5. Consider color-blind accessibility (avoid relying solely on color)

## Current Badge Images

| Badge ID | Description | Color |
|----------|-------------|-------|
| speed_speller | Complete 10 words in under 5 minutes | Gold |
| perseverance | Master a word after 5+ attempts | Bronze |
| perfect_planet | Complete a planet 5/5 on first attempt | Blue |
| streak_master | Achieve a 10-word streak | Red |
| word_warrior | Master 25 words total | Purple |
| comeback_kid | Correct answer after 3+ incorrect | Green |

## Removing a Badge Icon

To revert to procedural rendering for a badge:
1. Delete the PNG file from this directory
2. The system will automatically fall back to procedural rendering

## Contact

For questions about badge asset creation, contact the Design team.