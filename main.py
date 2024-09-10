import json
import random
import pygame
import os
import tkinter as tk
from tkinter import filedialog, messagebox, Listbox, ttk

# Initialize Pygame Mixer and Dummy Display
pygame.mixer.init()
pygame.display.init()  # Initialize the display module
pygame.display.set_mode((1, 1))  # Create a small dummy display

class Song:
    def __init__(self, title, file_path):
        self.title = title
        self.file_path = file_path
        self.length = self.get_length()
    
    def __str__(self):
        return f"{self.title}"
    
    def get_length(self):
        try:
            sound = pygame.mixer.Sound(self.file_path)
            return sound.get_length()
        except pygame.error as e:
            print(f"Error loading sound: {e}")
            return 0

class Node:
    def __init__(self, song):
        self.song = song
        self.next = None

class PlaylistManager:
    def __init__(self):
        self.head = None
        self.tail = None
        self.currently_playing = None
        self.is_paused = False

    def add_song(self, song):
        new_node = Node(song)
        if not self.head:
            self.head = new_node
            self.tail = new_node
        else:
            self.tail.next = new_node
            self.tail = new_node

    def remove_song(self, index):
        if not self.head:
            return None

        if index == 0:  # Remove the head
            removed_song = self.head.song
            self.head = self.head.next
            if not self.head:  # If the list is now empty, update the tail
                self.tail = None
            return removed_song

        current = self.head
        prev = None
        current_index = 0
        while current and current_index < index:
            prev = current
            current = current.next
            current_index += 1
        
        if current:  # Node to remove is found
            removed_song = current.song
            prev.next = current.next
            if not current.next:  # If the removed node was the tail, update the tail
                self.tail = prev
            return removed_song
        
        return None

    def shuffle_playlist(self):
        if not self.head or not self.head.next:
            return  # No need to shuffle if 0 or 1 song
        
        # Convert linked list to list for shuffling
        songs = []
        current = self.head
        while current:
            songs.append(current.song)
            current = current.next
        
        random.shuffle(songs)
        
        # Rebuild the linked list
        self.head = None
        self.tail = None
        for song in songs:
            self.add_song(song)

    def save_playlist(self, filename):
        songs = []
        current = self.head
        while current:
            songs.append(current.song.__dict__)
            current = current.next
        with open(filename, 'w') as file:
            json.dump(songs, file)

    def load_playlist(self, filename):
        try:
            with open(filename, 'r') as file:
                songs = json.load(file)
                self.head = None
                self.tail = None
                for song_data in songs:
                # Exclude 'length' key when creating a new Song object
                    song_data.pop('length', None)
                    song = Song(**song_data)
                    self.add_song(song)
        except FileNotFoundError:
            
            messagebox.showerror("Error", f"File {filename} not found.")


    def play_song(self, index):
        current = self.head
        current_index = 0
        while current and current_index < index:
            current = current.next
            current_index += 1
        
        if current:
            song = current.song
            if os.path.exists(song.file_path):
                pygame.mixer.music.load(song.file_path)
                pygame.mixer.music.play()
                self.currently_playing = current
                self.is_paused = False
                pygame.mixer.music.set_endevent(pygame.USEREVENT)  # Set event for song end
            else:
                messagebox.showerror("Error", f"File {song.file_path} does not exist.")
    
    def stop_song(self):
        pygame.mixer.music.stop()
        self.currently_playing = None

    def play_entire_playlist(self):
        if not self.head:
            messagebox.showinfo("Info", "No songs in the playlist to play.")
            return

        self.play_song(0)  # Start from the first song

    def pause_song(self):
        if self.is_paused:
            pygame.mixer.music.unpause()
        else:
            pygame.mixer.music.pause()
        self.is_paused = not self.is_paused

    def next_song(self):
        if self.currently_playing and self.currently_playing.next:
            self.play_song_by_node(self.currently_playing.next)

    def previous_song(self):
        if self.currently_playing:
            current = self.head
            prev = None
            while current and current != self.currently_playing:
                prev = current
                current = current.next
            
            if prev:
                self.play_song_by_node(prev)

    def play_song_by_node(self, node):
        song = node.song
        if os.path.exists(song.file_path):
            pygame.mixer.music.load(song.file_path)
            pygame.mixer.music.play()
            self.currently_playing = node
            self.is_paused = False
            pygame.mixer.music.set_endevent(pygame.USEREVENT)
        else:
            messagebox.showerror("Error", f"File {song.file_path} does not exist.")

class MusicApp:
    def __init__(self, root):
        self.manager = PlaylistManager()
        self.root = root
        self.root.title("Music Playlist Manager")
        self.root.geometry("600x650")  # Increased height to accommodate title entry and progress bar
        self.root.configure(bg="#2E4053")
        self.create_widgets()

        # Handle song end event
        self.root.after(100, self.check_pygame_events)

    def create_widgets(self):
        # Playlist Title Entry
        self.title_frame = tk.Frame(self.root, bg="#2E4053")
        self.title_frame.pack(pady=10)

        self.title_label = tk.Label(self.title_frame, text="Playlist Title:", bg="#2E4053", fg="white")
        self.title_label.pack(side=tk.LEFT, padx=5)

        self.title_entry = tk.Entry(self.title_frame, width=40)
        self.title_entry.pack(side=tk.LEFT, padx=5)

        # Playlist Title Display
        self.title_display = tk.Label(self.root, text="", bg="#2E4053", fg="white", font=("Arial", 14, "bold"))
        self.title_display.pack(pady=10)

        self.playlist_listbox = Listbox(self.root, selectmode=tk.SINGLE, width=60, height=15, bg="#212F3C", fg="white", font=("Arial", 12))
        self.playlist_listbox.pack(pady=10)
        self.playlist_listbox.bind("<ButtonRelease-1>", self.on_listbox_click)  # Bind click event

        # Canvas for Progress Bar
        self.progress_frame = tk.Frame(self.root, bg="#2E4053")
        self.progress_frame.pack(pady=10)

        self.progress_canvas = tk.Canvas(self.progress_frame, width=400, height=20, bg="#212F3C", highlightthickness=0)
        self.progress_canvas.pack()

        self.progress_indicator = self.progress_canvas.create_rectangle(0, 0, 0, 20, fill="#58D68D")

        # Frame for adding and removing songs
        song_control_frame = tk.Frame(self.root, bg="#2E4053")
        song_control_frame.pack(pady=10)

        self.add_btn = ttk.Button(song_control_frame, text="Add Song", command=self.add_song, style="Custom.TButton")
        self.add_btn.grid(row=0, column=0, padx=10, pady=5)

        self.remove_btn = ttk.Button(song_control_frame, text="Remove Song", command=self.remove_song, style="Custom.TButton")
        self.remove_btn.grid(row=0, column=1, padx=10, pady=5)

        self.shuffle_btn = ttk.Button(song_control_frame, text="Shuffle Playlist", command=self.shuffle_playlist, style="Custom.TButton")
        self.shuffle_btn.grid(row=0, column=2, padx=10, pady=5)

        self.save_btn = ttk.Button(song_control_frame, text="Save Playlist", command=self.save_playlist, style="Custom.TButton")
        self.save_btn.grid(row=0, column=3, padx=10, pady=5)

        self.load_btn = ttk.Button(song_control_frame, text="Load Playlist", command=self.load_playlist, style="Custom.TButton")  # Load button added
        self.load_btn.grid(row=0, column=4, padx=10, pady=5)

        # Frame for playback controls
        playback_control_frame = tk.Frame(self.root, bg="#2E4053")
        playback_control_frame.pack(pady=10)

        self.previous_btn = ttk.Button(playback_control_frame, text="Previous", command=self.previous_song, style="Custom.TButton")
        self.previous_btn.grid(row=0, column=0, padx=10, pady=5)

        self.play_pause_btn = ttk.Button(playback_control_frame, text="Play", command=self.toggle_play_pause, style="Custom.TButton")
        self.play_pause_btn.grid(row=0, column=1, padx=10, pady=5)

        self.next_btn = ttk.Button(playback_control_frame, text="Next", command=self.next_song, style="Custom.TButton")
        self.next_btn.grid(row=0, column=2, padx=10, pady=5)

        print("Pygame initialized successfully.")

        # Bind the progress bar click event
        self.progress_canvas.bind("<Button-1>", self.on_progress_canvas_click)

    def add_song(self):
        file_paths = filedialog.askopenfilenames(filetypes=[("MP3 Files", "*.mp3")])
        if file_paths:
            for file_path in file_paths:
                title = os.path.basename(file_path)
                self.manager.add_song(Song(title, file_path))
                self.playlist_listbox.insert(tk.END, title)

    def remove_song(self):
        selected = self.playlist_listbox.curselection()
        if selected:
            index = selected[0]
            self.manager.remove_song(index)
            self.playlist_listbox.delete(index)

    def shuffle_playlist(self):
        self.manager.shuffle_playlist()
        self.refresh_playlist()

    def save_playlist(self):
        filename = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files", "*.json")])
        if filename:
            self.manager.save_playlist(filename)

    def load_playlist(self):
        filename = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
        if filename:
            self.manager.load_playlist(filename)
            self.refresh_playlist()  # Refresh the playlist display after loading a new one

    def play_song(self, index):
        self.manager.play_song(index)
        self.play_pause_btn.config(text="Pause")
        self.update_progress_bar()

    def previous_song(self):
        self.manager.previous_song()
        self.update_progress_bar()

    def next_song(self):
        self.manager.next_song()
        self.update_progress_bar()

    def toggle_play_pause(self):
        if self.manager.is_paused:
            self.manager.pause_song()  # Unpause if currently paused
            self.play_pause_btn.config(text="Pause")
        else:
            self.manager.pause_song()  # Pause if currently playing
            self.play_pause_btn.config(text="Play")

    def on_listbox_click(self, event):
        selected = self.playlist_listbox.curselection()
        if selected:
            self.play_song(selected[0])

    def on_progress_canvas_click(self, event):
        if self.manager.currently_playing:
            # Calculate new position based on click
            canvas_width = self.progress_canvas.winfo_width()
            click_x = event.x
            new_position = (click_x / canvas_width) * self.manager.currently_playing.song.length
            pygame.mixer.music.set_pos(new_position)
            self.update_progress_bar()

    def update_progress_bar(self):
        if self.manager.currently_playing:
            # Update the progress bar
            canvas_width = self.progress_canvas.winfo_width()
            song_position = pygame.mixer.music.get_pos() / 1000  # Get position in seconds
            progress_ratio = song_position / self.manager.currently_playing.song.length
            self.progress_canvas.coords(self.progress_indicator, 0, 0, canvas_width * progress_ratio, 20)
            self.root.after(1000, self.update_progress_bar)  # Update progress bar every second

    def on_song_end(self, event=None):
        self.manager.next_song()
        self.update_progress_bar()  # Update progress bar for the next song

    def check_pygame_events(self):
        for event in pygame.event.get():
            if event.type == pygame.USEREVENT:
                self.on_song_end()
        self.root.after(100, self.check_pygame_events)

    def refresh_playlist(self):
        self.playlist_listbox.delete(0, tk.END)
        current = self.manager.head
        while current:
            self.playlist_listbox.insert(tk.END, current.song.title)
            current = current.next

    def set_playlist_title(self):
        title = self.title_entry.get()
        if title:
            self.title_display.config(text=title)

if __name__ == "__main__":
    root = tk.Tk()
    app = MusicApp(root)
    root.mainloop()


