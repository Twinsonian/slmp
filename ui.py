import tkinter as tk
from tkinter import ttk
from pathlib import Path
from player import Player
import pygame
import random
import time
import threading
from visuals import launch_visual


AUDIO_EXTENSIONS = [".mp3", ".wav", ".flac", ".ogg", ".opus"]

class SLMP:
    def __init__(self, root):
        self.root = root
        self.root.title("SLMP - Simple Local Music Player")
        self.root.configure(bg="#1e1e1e")
        self.root.geometry("600x440")

        self.hover_time = None

        self.player = Player(on_finish_callback=self.on_track_finished)
        self.current_dir = Path.home() / "Music"
        self.file_paths = []

        self.scroll_index = 0
        self.scroll_direction = 1  # 1 = forward, -1 = backward


        # Centralized playback state
        self.state = {
            "playing": False,
            "paused": False,
            "loop": False,
            "shuffle": False,
            "stopped": True,
            "current_index": None,
            "current_track": None,
            "volume": 100,
            "muted": False,
        }

        self.setup_ui()
        self.load_files()
        self.update_status_bar()

    def setup_ui(self):
        top_bar = tk.Frame(self.root, bg="#1e1e1e")
        top_bar.pack(fill=tk.X, padx=10, pady=(10, 0))

        self.up_label = tk.Label(top_bar, text="⬆ Up one level ..", fg="#d4d4d4", bg="#1e1e1e", font=("Helvetica", 14), cursor="hand2", anchor="w")
        self.up_label.pack(side=tk.LEFT)
        self.up_label.bind("<Button-1>", lambda e: self.go_up_one_level())

        visual_options = ["Blackout", "Bouncer"]
        self.visual_selector = ttk.Combobox(top_bar, values=visual_options, state="readonly", width=12)
        self.visual_selector.set("Visuals")
        self.visual_selector.pack(side=tk.RIGHT)
        self.visual_selector.bind("<<ComboboxSelected>>", self.on_visual_selected)

        self.file_listbox = tk.Listbox(self.root, bg="#1e1e1e", fg="#d4d4d4", selectbackground="#3c3c3c", highlightbackground="#3c3c3c", relief=tk.FLAT, font=("TkDefaultFont", 14))
        self.file_listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        self.file_listbox.bind("<Double-Button-1>", self.on_file_double_click)

        controls = tk.Frame(self.root, bg="#1e1e1e")
        controls.pack(pady=5, padx=10, anchor="w")

        self.play_button = tk.Button(controls, text="▶ Play", command=lambda: self.apply_state("playpause"), bg="#3c3c3c", fg="#d4d4d4", width=8)
        self.play_button.pack(side=tk.LEFT, padx=5)

        self.loop_button = tk.Button(controls, text="🔁 Loop", command=lambda: self.apply_state("loop"), bg="#3c3c3c", fg="#d4d4d4")
        self.loop_button.pack(side=tk.LEFT, padx=5)

        self.shuffle_button = tk.Button(controls, text="🔀 Shuffle", command=lambda: self.apply_state("shuffle"), bg="#3c3c3c", fg="#d4d4d4")
        self.shuffle_button.pack(side=tk.LEFT, padx=5)

        tk.Button(controls, text="⏹ Stop", command=lambda: self.apply_state("stop"), bg="#3c3c3c", fg="#d4d4d4").pack(side=tk.LEFT, padx=5)

        self.volume_slider = tk.Scale(controls, from_=0, to=100, orient=tk.HORIZONTAL, bg="#1e1e1e", fg="#d4d4d4", troughcolor="#3c3c3c", command=self.update_volume, length=100)
        self.volume_slider.set(100)
        self.volume_slider.pack(side=tk.LEFT, padx=(15, 10))

        self.mute_button = tk.Button(controls, text="🔈", command=self.toggle_mute, bg="#3c3c3c", fg="#d4d4d4")
        self.mute_button.pack(side=tk.LEFT, padx=(10, 10))

        self.progress_canvas = tk.Canvas(self.root, height=20, bg="#1e1e1e", highlightthickness=0)
        self.progress_canvas.pack(fill=tk.X, padx=10, pady=(5, 0))
        self.progress_canvas.bind("<Button-1>", self.on_progress_click)
        self.progress_canvas.bind("<Motion>", self.on_progress_hover)
        self.progress_canvas.bind("<Leave>", self.on_progress_leave)


        self.status_frame = tk.Frame(self.root, bg="#1e1e1e")
        self.status_frame.pack(fill=tk.X, padx=10, pady=(5, 5))

        self.track_label = tk.Label(self.status_frame, text="", anchor="w", bg="#1e1e1e", fg="#d4d4d4", font=("TkDefaultFont", 14))
        self.track_label.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.status_label = tk.Label(self.status_frame, text="00:00 / 00:00", anchor="e", bg="#1e1e1e", fg="#d4d4d4", font=("TkDefaultFont", 14))
        self.status_label.pack(side=tk.RIGHT)

    def load_files(self):
        self.file_listbox.delete(0, tk.END)
        self.file_paths = []

        for item in sorted(self.current_dir.iterdir()):
            if item.suffix.lower() in AUDIO_EXTENSIONS or item.is_dir():
                label = f"  📁 {item.name}" if item.is_dir() else f"  {item.name}"
                self.file_listbox.insert(tk.END, label)
                self.file_paths.append(item)

        self.up_label.config(state="normal" if self.current_dir.parent != self.current_dir else "disabled")
        self.apply_state("stop")

    def go_up_one_level(self):
        if self.current_dir.parent != self.current_dir:
            self.current_dir = self.current_dir.parent
            self.load_files()

    def on_file_double_click(self, event):
        selection = self.file_listbox.curselection()
        if selection:
            index = selection[0]
            path = self.file_paths[index]
            if path.is_dir():
                self.current_dir = path
                self.load_files()
            elif path.suffix.lower() in AUDIO_EXTENSIONS:
                self.state["current_index"] = index
                self.state["current_track"] = path
                self.state["playing"] = True
                self.state["paused"] = False
                self.state["stopped"] = False
                self.apply_state()


    def update_volume(self, value):
        volume = int(value)
        self.state["volume"] = volume
        pygame.mixer.music.set_volume(volume / 100)
        if self.state["muted"] and volume > 0:
            self.state["muted"] = False
            self.mute_button.config(text="🔈")

    def on_progress_hover(self, event):
        if self.player.duration > 0:
            width = self.progress_canvas.winfo_width()
            percent = event.x / width
            self.hover_time = int(percent * self.player.duration)

    def on_progress_leave(self, event):
        self.hover_time = None

    def toggle_mute(self):
        if self.state["muted"]:
            self.volume_slider.set(self.state["volume"])
            pygame.mixer.music.set_volume(self.state["volume"] / 100)
            self.mute_button.config(text="🔈")
            self.state["muted"] = False
        else:
            self.state["volume"] = self.volume_slider.get()
            self.volume_slider.set(0)
            pygame.mixer.music.set_volume(0)
            self.mute_button.config(text="🔇")
            self.state["muted"] = True

    def on_progress_click(self, event):
        if self.player.duration > 0:
            width = self.progress_canvas.winfo_width()
            percent = event.x / width
            seek_time = int(percent * self.player.duration)
            self.player.seek(seek_time)

    def update_status_bar(self):
        if self.state["current_track"]:
            name = self.state["current_track"].name
            if len(name) <= 40:
                display_name = name
            else:
                # Scroll logic
                max_index = len(name) - 40
                display_name = name[self.scroll_index:self.scroll_index + 40]

                # Update scroll index
                self.scroll_index += self.scroll_direction
                if self.scroll_index >= max_index:
                    self.scroll_index = max_index
                    self.scroll_direction = -1
                elif self.scroll_index <= 0:
                    self.scroll_index = 0
                    self.scroll_direction = 1

            self.track_label.config(text=display_name)
        else:
            self.track_label.config(text="")

        # Schedule next update
        self.root.after(500, self.update_status_bar)

    def format_time(self, seconds):
        minutes = seconds // 60
        secs = seconds % 60
        return f"{minutes:02}:{secs:02}"

    def on_track_finished(self):
        if self.state["stopped"]:
            self.state["stopped"] = False
            return

        if self.state["loop"] and self.state["current_track"]:
            # Replay same track
            self.state["playing"] = True
            self.state["paused"] = False
        elif self.state["shuffle"]:
            index = random.randint(0, len(self.file_paths) - 1)
            self.state["current_index"] = index
            self.state["current_track"] = self.file_paths[index]
            self.state["playing"] = True
            self.state["paused"] = False
        else:
            next_index = (self.state["current_index"] + 1) % len(self.file_paths)
            self.state["current_index"] = next_index
            self.state["current_track"] = self.file_paths[next_index]
            self.state["playing"] = True
            self.state["paused"] = False

        self.apply_state()

    def start_visual(self, mode):
        threading.Thread(target=launch_visual, args=(mode,), daemon=True).start()

    def on_visual_selected(self, event):
        mode = self.visual_selector.get().lower()
        threading.Thread(target=launch_visual, args=(mode,), daemon=True).start()
        self.visual_selector.set("Visuals")  # Reset after launch

    def apply_state(self, source=None):
        print(f"DEBUG: apply_state called by '{source}' with state =", self.state)

        # Handle intent
        if source == "stop":
            self.state["playing"] = False
            self.state["paused"] = False
            self.state["stopped"] = True
            self.state["loop"] = False
            self.state["shuffle"] = False
            self.state["current_index"] = None
            self.state["current_track"] = None

            # Auto-select top playable file
            for i, path in enumerate(self.file_paths):
                if path.is_file() and path.suffix.lower() in AUDIO_EXTENSIONS:
                    self.state["current_index"] = i
                    self.state["current_track"] = path
                    break

        elif source == "playpause":
            if self.state["stopped"]:
                selection = self.file_listbox.curselection()
                if selection:
                    index = selection[0]
                    path = self.file_paths[index]
                    if path.is_file() and path.suffix.lower() in AUDIO_EXTENSIONS:
                        self.state["current_index"] = index
                        self.state["current_track"] = path
                        self.state["playing"] = True
                        self.state["paused"] = False
                        self.state["stopped"] = False
            elif self.state["playing"]:
                self.state["playing"] = False
                self.state["paused"] = True
            elif self.state["paused"]:
                self.state["playing"] = True
                self.state["paused"] = False

        elif source == "loop":
            self.state["loop"] = not self.state["loop"]
            if self.state["loop"]:
                self.state["shuffle"] = False

        elif source == "shuffle":
            was_shuffling = self.state["shuffle"]
            self.state["shuffle"] = not was_shuffling

            if self.state["shuffle"]:  # Only act if shuffle is now ON
                self.state["loop"] = False
                valid_files = [f for f in self.file_paths if f.suffix.lower() in AUDIO_EXTENSIONS]
                if valid_files:
                    track = random.choice(valid_files)
                    self.state["current_index"] = self.file_paths.index(track)
                    self.state["current_track"] = track
                    self.state["playing"] = True
                    self.state["paused"] = False
                    self.state["stopped"] = False
            # If shuffle is being turned OFF, do not touch current_track or playback state

        # Run full DMV audit
        self.reconcile_state()

    def reconcile_state(self):
        # Track assignment
        if self.state["current_track"] is None and self.state["current_index"] is not None:
            self.state["current_track"] = self.file_paths[self.state["current_index"]]
        elif self.state["current_track"] and self.state["current_index"] is None:
            try:
                self.state["current_index"] = self.file_paths.index(self.state["current_track"])
            except ValueError:
                self.state["current_index"] = None

        # Listbox sync
        if self.state["current_index"] is not None:
            self.file_listbox.selection_clear(0, tk.END)
            self.file_listbox.selection_set(self.state["current_index"])
            self.file_listbox.activate(self.state["current_index"])
            self.file_listbox.see(self.state["current_index"])

        # Loop & Shuffle UI — moved above stop return
        self.loop_button.config(
            bg="#007acc" if self.state["loop"] else "#3c3c3c",
            relief=tk.SUNKEN if self.state["loop"] else tk.RAISED
        )
        self.shuffle_button.config(
            bg="#007acc" if self.state["shuffle"] else "#3c3c3c",
            relief=tk.SUNKEN if self.state["shuffle"] else tk.RAISED
        )

        if self.state["stopped"]:
            self.player.stop()
            self.play_button.config(text="▶ Play")
            self.track_label.config(text="")
            self.status_label.config(text="00:00 / 00:00")
            self.progress_canvas.delete("all")
            return

        # Always show track info if a track is assigned
        if self.state["current_track"]:
            self.track_label.config(text=self.state["current_track"].name)
            elapsed = self.player.get_elapsed()
            total = self.player.duration
            self.status_label.config(text=f"{int(elapsed // 60):02}:{int(elapsed % 60):02} / {int(total // 60):02}:{int(total % 60):02}")

        if self.state["paused"]:
            if not self.player.paused:
                self.player.toggle_pause()
            self.play_button.config(text="▶ Play")
            return

        if self.state["playing"]:
            if self.state["current_track"]:
                if self.player.paused:
                    self.player.toggle_pause()
                elif not self.player.is_playing() or self.player.current_file != self.state["current_track"]:
                    self.player.play(self.state["current_track"], loop=self.state["loop"])
                self.play_button.config(text="⏸ Pause")

        # Track label and status
        if self.state["current_track"]:
            self.track_label.config(text=self.state["current_track"].name)
            elapsed = self.player.get_elapsed()
            total = self.player.duration
            self.status_label.config(text=f"{int(elapsed // 60):02}:{int(elapsed % 60):02} / {int(total // 60):02}:{int(total % 60):02}")



if __name__ == "__main__":
    root = tk.Tk()
    SLMP(root)
    root.mainloop()

