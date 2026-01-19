# Sound Assets

This directory contains audio files used in the application.

## Current Files

All sound effects are sourced from [Mixkit](https://mixkit.co/free-sound-effects/) under the [Mixkit License](https://mixkit.co/license/#sfxFree) (free for commercial and personal use).

### UI Interaction
- ✅ `ui_click.wav` - Button click sound
- ✅ `ui_hover.wav` - Hover effect sound
- ✅ `notification.wav` - Notification alert sound

### Game Phases
- ✅ `day_start.wav` - Day phase background music (loop)
- ✅ `night_start.wav` - Night phase background music (loop)

### Game Events
- ✅ `vote_cast.wav` - Voting action sound
- ✅ `player_death.wav` - Player elimination sound
- ✅ `victory.wav` - Victory celebration music
- ✅ `defeat.wav` - Defeat music

## File Format

- Current format: WAV (high quality, larger file size)
- Alternative: MP3 (smaller file size, good browser compatibility)
- Howler.js will automatically fallback between formats as configured in `src/config/soundConfig.ts`

## Adding New Sounds

1. Place audio files in this directory (`frontend/public/sounds/`)
2. Update `src/config/soundConfig.ts` to register the new sound
3. File paths should be relative to `/public/` (e.g., `/sounds/filename.wav`)

## Sound Sources

Royalty-free sound effects can be obtained from:
- https://mixkit.co/free-sound-effects/ (current source)
- https://freesound.org/
- https://pixabay.com/music/

## License

All current audio files are from Mixkit and are licensed under the [Mixkit License](https://mixkit.co/license/#sfxFree):
- Free for commercial and personal use
- No attribution required
