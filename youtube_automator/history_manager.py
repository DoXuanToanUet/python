import os
import json
from datetime import datetime

class HistoryManager:
    def __init__(self):
        self.history_file = "youtube_automator_history.json"
        self.history = self.load_history()
        
    def load_history(self):
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, 'r', encoding='utf-8') as file:
                    return json.load(file)
            except:
                return {"sessions": [], "videos": []}
        else:
            return {"sessions": [], "videos": []}
    
    def save_history(self):
        with open(self.history_file, 'w', encoding='utf-8') as file:
            json.dump(self.history, file, ensure_ascii=False, indent=2)
    
    def add_video_interaction(self, video_data):
        self.history["videos"].append(video_data)
        self.save_history()
    
    def add_session(self, session_data):
        session_id = session_data.get("session_id")
        if not session_id:
            self.history["sessions"].append(session_data)
        else:
            for i, session in enumerate(self.history["sessions"]):
                if session.get("session_id") == session_id:
                    self.history["sessions"][i] = session_data
                    break
            else:
                self.history["sessions"].append(session_data)
        self.save_history()
    
    def get_history(self):
        return self.history
    
    def get_session_videos(self, session_id):
        return [video for video in self.history["videos"] if video.get("session_id") == session_id]