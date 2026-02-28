---
name: spotify-player
description: Terminal Spotify playback/search via spotify_player. Use when asked to play music, search Spotify, or control playback.
homepage: https://github.com/aome510/spotify-player
metadata:
  {
    "openclaw":
      {
        "emoji": "🎵",
        "requires": { "anyBins": ["spotify_player"] },
        "install":
          [
            {
              "id": "winget",
              "kind": "winget",
              "package": "aome510.spotify-player",
              "label": "Install spotify_player (winget)",
            }
          ],
      },
  }
---

# spotify_player

Use `spotify_player` to control Spotify playback and search for music.

## Requirements

- Spotify Premium account.
- `spotify_player` installed via `winget install aome510.spotify-player`.

## Setup / Authentication

On first run, the user needs to authenticate. Running any command like `spotify_player authenticate` will generate a login URL or open the browser automatically.

## Common CLI Commands

- **Authentication:** `spotify_player authenticate`
- **Playback Control:**
  - Play: `spotify_player playback play`
  - Pause: `spotify_player playback pause`
  - Next track: `spotify_player playback next`
  - Previous track: `spotify_player playback previous`
- **Search and Play:**
  - Search track and play: `spotify_player playback start track "<query>"`
  - Search playlist and play: `spotify_player playback start playlist "<query>"`
  - Search album and play: `spotify_player playback start album "<query>"`
- **Connect Device:**
  - `spotify_player connect`
- **Like Track:**
  - `spotify_player like`

## Notes

- Config folder on Windows is typically `%USERPROFILE%\.config\spotify-player` or `%APPDATA%\spotify-player`.
- The CLI can run seamlessly in OpenClaw's background tasks to queue music or skip tracks while the user works.
