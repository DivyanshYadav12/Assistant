"""Music playback skill — plays music on various platforms.

Supports:
- YouTube (direct playback with yt-dlp, or search fallback)
- Spotify (search only - requires Spotify desktop app for direct playback)
- YouTube Music (search only)
- SoundCloud (search only)

Requires yt-dlp for direct YouTube playback (optional, falls back to search).
Install with: pip install yt-dlp
"""

from __future__ import annotations

import re
import subprocess
import webbrowser
from pathlib import Path

from assistant.skills.base import SkillContext, SkillResult


class MusicPlaybackSkill:
    name = "music_playback"
    description = "Play music on various platforms"
    risk_default = "low"

    def can_handle(self, intent: str, context: SkillContext) -> float:
        text = intent.lower()
        music_keywords = [
            "play", "music", "song", "track", "listen to",
            "spotify", "youtube", "youtube music", "soundcloud"
        ]
        
        # Check if any music keyword is present
        if any(kw in text for kw in music_keywords):
            # Avoid false positives
            if "file" in text or "search" in text and "music" not in text:
                return 0.0
            return 0.85
        return 0.0

    def execute(self, context: SkillContext) -> SkillResult:
        text = context.user_intent.lower()
        
        # Extract platform (default to YouTube/browser)
        platform = self._extract_platform(text)
        
        # Extract song name
        song = self._extract_song(text)
        
        if not song:
            return SkillResult(
                status="clarify",
                clarification_question="What song would you like me to play?"
            )
        
        # Handle different platforms
        if platform == "spotify":
            return self._play_spotify(song)
        elif platform == "youtube music":
            return self._play_youtube_music(song)
        elif platform == "soundcloud":
            return self._play_soundcloud(song)
        else:  # Default to YouTube
            return self._play_youtube(song)

    def _play_youtube(self, song: str) -> SkillResult:
        """Play song on YouTube (direct playback with yt-dlp, or search fallback)."""
        # Try direct playback with yt-dlp
        video_url = self._get_first_youtube_video(song)
        
        if video_url:
            webbrowser.open(video_url)
            return SkillResult(
                status="ok",
                output=f"Playing '{song}' on YouTube",
                speak=f"Playing {song} on YouTube"
            )
        else:
            # Fallback to search page
            url = f"https://www.youtube.com/results?search_query={song.replace(' ', '+')}"
            webbrowser.open(url)
            return SkillResult(
                status="ok",
                output=f"Searching for '{song}' on YouTube (select a video to play)",
                speak=f"Searching for {song} on YouTube. Please select a video to play."
            )

    def _get_first_youtube_video(self, song: str) -> str | None:
        """Get the first YouTube video URL for a song using yt-dlp."""
        try:
            # Check if yt-dlp is available
            subprocess.run(["yt-dlp", "--version"], capture_output=True, check=True)
        except (FileNotFoundError, subprocess.CalledProcessError):
            # yt-dlp not installed, return None (will fall back to search)
            return None
        
        try:
            # Use yt-dlp to get the first video URL
            result = subprocess.run(
                ["yt-dlp", "--get-id", f"ytsearch:{song}"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0 and result.stdout.strip():
                video_id = result.stdout.strip().split('\n')[0]
                return f"https://www.youtube.com/watch?v={video_id}"
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, Exception):
            pass
        
        return None

    def _play_spotify(self, song: str) -> SkillResult:
        """Play song on Spotify (search only - requires desktop app for direct playback)."""
        url = f"https://open.spotify.com/search/{song.replace(' ', '%20')}"
        webbrowser.open(url)
        return SkillResult(
            status="ok",
            output=f"Searching for '{song}' on Spotify (select a track to play)",
            speak=f"Searching for {song} on Spotify. Please select a track to play."
        )

    def _play_youtube_music(self, song: str) -> SkillResult:
        """Play song on YouTube Music (search only)."""
        url = f"https://music.youtube.com/search?q={song.replace(' ', '+')}"
        webbrowser.open(url)
        return SkillResult(
            status="ok",
            output=f"Searching for '{song}' on YouTube Music (select a track to play)",
            speak=f"Searching for {song} on YouTube Music. Please select a track to play."
        )

    def _play_soundcloud(self, song: str) -> SkillResult:
        """Play song on SoundCloud (search only)."""
        url = f"https://soundcloud.com/search?q={song.replace(' ', '+')}"
        webbrowser.open(url)
        return SkillResult(
            status="ok",
            output=f"Searching for '{song}' on SoundCloud (select a track to play)",
            speak=f"Searching for {song} on SoundCloud. Please select a track to play."
        )

    def _extract_platform(self, text: str) -> str:
        """Extract the music platform from the intent."""
        if "spotify" in text:
            return "spotify"
        elif "youtube music" in text:
            return "youtube music"
        elif "soundcloud" in text:
            return "soundcloud"
        else:
            return "youtube"  # Default

    def _extract_song(self, text: str) -> str | None:
        """Extract the song name from the intent."""
        # Remove common words and platform references
        text = text.lower()
        
        # Remove platform references
        for platform in ["spotify", "youtube", "youtube music", "soundcloud", "on the browser", "in browser"]:
            text = text.replace(platform, "")
        
        # Remove action words
        for action in ["play", "music", "song", "track", "listen to", "i want to", "can you", "please"]:
            text = text.replace(action, "")
        
        # Clean up
        song = text.strip(" ?.,!")
        
        # Remove leading articles
        if song.startswith(("a ", "an ", "the ")):
            song = song[4:] if song.startswith("the ") else song[2:]
        
        return song if len(song) > 2 else None
