import pygame
import threading
import time
import subprocess
from pathlib import Path

AUDIO_EXTENSIONS = [".mp3", ".wav", ".flac", ".ogg", ".opus"]

class Player:
    def __init__(self, on_finish_callback):
        pygame.mixer.init()
        self.on_finish_callback = on_finish_callback
        self.current_file = None
        self.looping = False
        self.paused = False
        self.start_time = None
        self.pause_start = None
        self.total_paused_time = 0.0
        self.duration = 0.0
        self._monitor_thread = None
        self._stop_flag = False

    def play(self, filepath: Path, loop: bool = False):
        self.stop()
        self.current_file = filepath.resolve()
        self.looping = loop
        self._stop_flag = False
        try:
            pygame.mixer.music.load(str(self.current_file))
            pygame.mixer.music.play(loops=-1 if loop else 0)
            self.start_time = time.time()
            self.total_paused_time = 0.0
            self.pause_start = None
            self.paused = False
            self.duration = self.get_duration(filepath)
            self._monitor_thread = threading.Thread(target=self._monitor_playback, daemon=True)
            self._monitor_thread.start()
        except Exception as e:
            print(f"Error playing file: {e}")

    def _monitor_playback(self):
        while pygame.mixer.music.get_busy():
            if self._stop_flag:
                return
            time.sleep(0.5)
        if not self.paused and not self.looping and not self._stop_flag:
            self.on_finish_callback()

    def toggle_pause(self):
        if self.paused:
            pygame.mixer.music.unpause()
            self.total_paused_time += time.time() - self.pause_start
            self.pause_start = None
            self.paused = False
        else:
            pygame.mixer.music.pause()
            self.pause_start = time.time()
            self.paused = True

    def stop(self):
        pygame.mixer.music.stop()
        self._stop_flag = True
        self.paused = False
        self.start_time = None
        self.pause_start = None
        self.total_paused_time = 0.0
        self.duration = 0.0

    def seek(self, seconds: float):
        try:
            pygame.mixer.music.set_pos(seconds)
            self.start_time = time.time() - seconds
            self.total_paused_time = 0.0
            self.pause_start = None
        except Exception as e:
            print(f"Seek failed: {e}")

    def get_duration(self, filepath: Path) -> float:
        try:
            result = subprocess.run(
                ["ffprobe", "-v", "error", "-show_entries", "format=duration",
                 "-of", "default=noprint_wrappers=1:nokey=1", str(filepath)],
                capture_output=True, text=True
            )
            return float(result.stdout.strip())
        except Exception:
            return 0.0

    def get_elapsed(self) -> float:
        if not self.start_time:
            return 0.0
        if self.paused and self.pause_start:
            paused_elapsed = self.pause_start - self.start_time - self.total_paused_time
            return min(paused_elapsed, self.duration)
        elapsed = time.time() - self.start_time - self.total_paused_time
        if self.looping and self.duration > 0:
            return elapsed % self.duration
        return min(elapsed, self.duration)

    def is_playing(self):
        return pygame.mixer.music.get_busy() and not self.paused


