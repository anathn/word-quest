# Badge Icons

## Current Implementation (MVP)

For the MVP release, badge icons are **procedurally generated** using Pygame drawing primitives. The `BadgeNotification` and `BadgeCollection` components create badge visuals dynamically at runtime using:

- Colored circles based on rarity
- Genre-specific symbols (lightning bolt, mountain, star, shield, etc.)
- Rarity-based border colors
- Animated rainbow effect for legendary badges

## Placeholder Assets

The `icon_path` field in `badge_definitions.json` references paths like `assets/badges/speed_speller.png`, but these PNG files are **not currently used**. The rendering code draws badges procedurally instead.

## Future Enhancement

For a polished release, consider creating custom PNG badge assets:

1. **Dimensions**: 128x128 pixels (current icon size in code)
2. **Format**: PNG with transparency
3. **Style**: Space-themed, colorful, kid-friendly
4. **Rarity tiers**:
   - Common: Silver border, simple design
   - Uncommon: Bronze border, more detailed
   - Rare: Gold border, elaborate design
   - Legendary: Rainbow animated border, spectacular effects

### Suggested Tooling

- **Graphics**: Inkscape (vector), GIMP (raster)
- **Icons**: Freepik, Kenney.nl game assets (for inspiration)
- **Animation**: Lottie for web, or frame-by-frame PNG sequences for Pygame

### Implementation Steps

When ready to add real badge icons:

1. Create PNG assets for all 6 badges × 4 rarities = 24 images (or 6 if using one per badge)
2. Update `BadgeNotification._create_badge_icon()` to load PNG instead of drawing
3. Update `BadgeCollection` to render badge images
4. Add loading/error handling for missing assets

## Current Badge Definitions

| Badge ID | Name | Rarity | Current Icon |
|----------|------|--------|--------------|
| speed_speller | Speed Speller | Common | Lightning bolt (procedural) |
| perseverance | Perseverance | Uncommon | Mountain (procedural) |
| perfect_planet | Perfect Planet | Rare | 5-pointed star (procedural) |
| streak_master | Streak Master | Rare | "10" number (procedural) |
| word_warrior | Word Warrior | Legendary | Shield (procedural) |
| comeback_kid | Comeback Kid | Uncommon | Upward arrow (procedural) |

## Acceptance Criteria Status

✅ **MVP**: Badge icons display correctly using procedural graphics
📝 **Future**: Replace with custom PNG assets for enhanced visual quality

This placeholder strategy is **intentional** for MVP to:
- Reduce initial development time
- Allow quick iteration on badge designs
- Enable programmatic testing without asset dependencies

Assets can be added in a future iteration without changing the badge system logic.