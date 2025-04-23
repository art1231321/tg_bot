import os
import json
from typing import Dict, List, Tuple

VOICES_FILE = "voices.json"
MAX_TITLE_LENGTH = 32

class VoiceStorage:
    def __init__(self):
        self.voices: Dict[str, str] = {}
        self._load_voices()
    
    def _load_voices(self) -> None:
        try:
            with open(VOICES_FILE, "r", encoding="utf-8") as f:
                self.voices = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self.voices = {}
    
    def save_voice(self, title: str, file_id: str) -> bool:
        if file_id in self.voices.values():
            return False
        self.voices[title] = file_id
        self._save_to_file()
        return True
    
    def delete_voice(self, title: str) -> bool:
        if title in self.voices:
            del self.voices[title]
            self._save_to_file()
            return True
        return False
    
    def rename_voice(self, old_title: str, new_title: str) -> bool:
        if old_title in self.voices and new_title not in self.voices:
            self.voices[new_title] = self.voices.pop(old_title)
            self._save_to_file()
            return True
        return False
    
    def _save_to_file(self) -> None:
        with open(VOICES_FILE, "w", encoding="utf-8") as f:
            json.dump(self.voices, f, ensure_ascii=False, indent=4)
    
    def get_all_voices(self) -> List[Tuple[str, str]]:
        return list(self.voices.items())
