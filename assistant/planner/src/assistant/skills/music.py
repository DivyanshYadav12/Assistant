"""Music playback skill — plays music on various platforms.

Supports:
- YouTube (browser)
- Spotify (if installed)
- Generic web search for music
- Song search and recommendations
"""

from __future__ import annotations

import re
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
        
        # Construct search URL based on platform
        if platform == "spotify":
            url = f"https://open.spotify.com/search/{song.replace(' ', '%20')}"
            webbrowser.open(url)
            return SkillResult(
                status="ok",
                output=f"Searching for '{song}' on Spotify",
                speak=f"Searching for {song} on Spotify"
            )
        elif platform == "youtube music":
            url = f"https://music.youtube.com/search?q={song.replace(' ', '+')}"
            webbrowser.open(url)
            return SkillResult(
                status="ok",
                output=f"Searching for '{song}' on YouTube Music",
                speak=f"Searching for {song} on YouTube Music"
            )
        else:  # Default to YouTube
            url = f"https://www.youtube.com/results?search_query={song.replace(' ', '+')}"
            webbrowser.open(url)
            return SkillResult(
                status="ok",
                output=f"Searching for '{song}' on YouTube",
                speak=f"Searching for {song} on YouTube"
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
