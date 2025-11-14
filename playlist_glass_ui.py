import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import os
import pygame # Replaced playsound and threading

# --- 1. Data Structure: Doubly Linked List Node ---
class Node:
    """A node for the Doubly Linked List."""
    def __init__(self, data):
        self.data = data  # 'data' will be the file path to the song
        self.next = None
        self.prev = None

# --- 2. Data Structure: Doubly Linked List ---
class DoublyLinkedList:
    """The main playlist structure."""
    def __init__(self):
        self.head = None
        self.tail = None

    def add_song(self, node):
        """Adds a song (node) to the end of the playlist."""
        if not self.head:
            self.head = node
            self.tail = node
        else:
            self.tail.next = node
            node.prev = self.tail
            self.tail = node

    def delete_song(self, node):
        """Removes a specific song (node) from the playlist."""
        if node.prev:
            node.prev.next = node.next
        else:
            # It's the head node
            self.head = node.next

        if node.next:
            node.next.prev = node.prev
        else:
            # It's the tail node
            self.tail = node.prev
        
        # Clear node references
        node.next = None
        node.prev = None

    def clear(self):
        """Clears the entire list."""
        self.head = None
        self.tail = None

# --- Main Application ---
class MusicPlayer:
    def __init__(self, root):
        self.root = root
        self.root.title("DSA Music Player")
        self.root.geometry("600x500")
        
        # --- Initialize Pygame Mixer ---
        pygame.init()
        pygame.mixer.init()
        
        # --- Initialize Data Structures ---
        self.playlist = DoublyLinkedList()
        self.song_map = {}  # 4. HashMap (for O(1) search)
        self.history = []   # 2. Stack (for previous songs)
        self.upcoming = []  # 3. Queue (placeholder for future use)

        # --- Playback State ---
        self.current_song_node = None
        self.is_playing = False
        self.is_paused = False
        
        # --- Configure Dark Theme ---
        self.configure_dark_theme()

        # --- Create GUI Widgets ---
        self.create_widgets()
        
        # --- Set up event checker for when song finishes ---
        self.SONG_END_EVENT = pygame.USEREVENT + 1
        pygame.mixer.music.set_endevent(self.SONG_END_EVENT)
        self.check_music_event()

    def configure_dark_theme(self):
        """Sets a clean dark theme for the UI."""
        self.root.configure(bg="#2E2E2E")
        style = ttk.Style()
        style.theme_use("clam")

        # Style for buttons
        style.configure("TButton",
                        background="#4A4A4A",
                        foreground="white",
                        bordercolor="#4A4A4A",
                        lightcolor="#4A4A4A",
                        darkcolor="#4A4A4A")
        style.map("TButton",
                  background=[("active", "#6A6A6A")])

        # Style for Listbox (Playlist)
        self.listbox_bg = "#3C3C3C"
        self.listbox_fg = "#E0E0E0"
        self.select_bg = "#5E81AC" # A nice blue for selection

        # Style for Frames
        style.configure("TFrame", background="#2E2E2E")
        style.configure("TLabel", background="#2E2E2E", foreground="white")
        style.configure("TEntry", fieldbackground="#3C3C3C", foreground="white", insertcolor="white")

    def create_widgets(self):
        """Creates and places all the GUI components."""
        
        # --- Search Bar Frame ---
        search_frame = ttk.Frame(self.root, padding=10)
        search_frame.pack(fill="x")
        
        ttk.Label(search_frame, text="Search:").pack(side="left", padx=5)
        self.search_entry = ttk.Entry(search_frame)
        self.search_entry.pack(side="left", fill="x", expand=True, padx=5)
        self.search_button = ttk.Button(search_frame, text="Find", command=self.search_song)
        self.search_button.pack(side="left")

        # --- Playlist Frame ---
        playlist_frame = ttk.Frame(self.root)
        playlist_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        scrollbar = ttk.Scrollbar(playlist_frame, orient="vertical")
        self.playlist_box = tk.Listbox(playlist_frame,
                                       bg=self.listbox_bg,
                                       fg=self.listbox_fg,
                                       selectbackground=self.select_bg,
                                       selectforeground="white",
                                       height=15,
                                       font=("Helvetica", 10),
                                       activestyle="none",
                                       borderwidth=0,
                                       highlightthickness=0,
                                       yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.playlist_box.yview)
        
        scrollbar.pack(side="right", fill="y")
        self.playlist_box.pack(side="left", fill="both", expand=True)
        self.playlist_box.bind("<Double-1>", lambda e: self.play_music())


        # --- Control Buttons Frame ---
        controls_frame = ttk.Frame(self.root, padding=10)
        controls_frame.pack(fill="x")
        
        # Row 1: Playback
        playback_frame = ttk.Frame(controls_frame)
        playback_frame.pack()
        
        self.prev_button = ttk.Button(playback_frame, text="⏮ Prev", command=self.prev_song)
        self.prev_button.pack(side="left", padx=5)
        
        self.play_button = ttk.Button(playback_frame, text="▶ Play", command=self.play_music)
        self.play_button.pack(side="left", padx=5)
        
        self.stop_button = ttk.Button(playback_frame, text="■ Stop", command=self.stop_music)
        self.stop_button.pack(side="left", padx=5)
        
        self.next_button = ttk.Button(playback_frame, text="Next ⏭", command=self.next_song)
        self.next_button.pack(side="left", padx=5)

        # Row 2: Playlist Management
        manage_frame = ttk.Frame(controls_frame)
        manage_frame.pack(pady=10)
        
        self.add_button = ttk.Button(manage_frame, text="Add Song(s)", command=self.add_songs)
        self.add_button.pack(side="left", padx=5)
        
        self.delete_button = ttk.Button(manage_frame, text="Delete Selected", command=self.delete_song)
        self.delete_button.pack(side="left", padx=5)
        
        self.clear_button = ttk.Button(manage_frame, text="Clear Playlist", command=self.clear_playlist)
        self.clear_button.pack(side="left", padx=5)

    # --- 6. High-Level Functional Flow & Features ---

    def add_songs(self):
        """Loads one or more songs into the playlist."""
        file_paths = filedialog.askopenfilenames(
            title="Select Songs",
            filetypes=(("Audio Files", "*.mp3 *.wav"), ("All Files", "*.*"))
        )
        
        for file_path in file_paths:
            song_name = os.path.basename(file_path)
            if song_name not in self.song_map:
                # Create the node
                new_node = Node(file_path)
                
                # Add to DLL
                self.playlist.add_song(new_node)
                
                # Add to HashMap
                self.song_map[song_name] = new_node
                
                # Add to UI Listbox
                self.playlist_box.insert("end", song_name)

    def delete_song(self):
        """Deletes the currently selected song."""
        try:
            selected_index = self.playlist_box.curselection()[0]
            song_name = self.playlist_box.get(selected_index)
        except IndexError:
            messagebox.showwarning("No Selection", "Please select a song to delete.")
            return

        # Find node in HashMap
        node_to_delete = self.song_map.get(song_name)
        
        if node_to_delete:
            # If it's playing, stop it
            if self.current_song_node == node_to_delete:
                self.stop_music()
                self.current_song_node = None
            
            # Remove from DLL
            self.playlist.delete_song(node_to_delete)
            
            # Remove from HashMap
            del self.song_map[song_name]
            
            # Remove from UI
            self.playlist_box.delete(selected_index)
            self.unhighlight_all() # Clear highlights

    def clear_playlist(self):
        """Clears the entire playlist and all data structures."""
        self.stop_music()
        
        # Clear Data Structures
        self.playlist.clear()
        self.song_map.clear()
        self.history.clear()
        self.upcoming.clear()
        self.current_song_node = None
        
        # Clear UI
        self.playlist_box.delete(0, "end")
        self.play_button.config(text="▶ Play")

    def play_music(self):
        """Plays the selected song, or pauses/resumes the current one."""
        try:
            selected_index = self.playlist_box.curselection()[0]
            song_name = self.playlist_box.get(selected_index)
            selected_node = self.song_map.get(song_name)
        except IndexError:
            # No song is selected in the listbox
            if self.is_paused:
                # Resume playing
                pygame.mixer.music.unpause()
                self.is_playing = True
                self.is_paused = False
                self.play_button.config(text="❚❚ Pause")
            elif self.is_playing:
                # Pause playing
                pygame.mixer.music.pause()
                self.is_playing = False
                self.is_paused = True
                self.play_button.config(text="▶ Play")
            else:
                messagebox.showwarning("No Selection", "Please select a song to play.")
            return

        # A song IS selected in the listbox
        if self.current_song_node == selected_node:
            # Selected song is the one already loaded
            if self.is_paused:
                pygame.mixer.music.unpause()
                self.is_playing = True
                self.is_paused = False
                self.play_button.config(text="❚❚ Pause")
            elif self.is_playing:
                pygame.mixer.music.pause()
                self.is_playing = False
                self.is_paused = True
                self.play_button.config(text="▶ Play")
            else:
                # It was stopped, play from beginning
                self.play_from_node(selected_node)
        else:
            # A new song is selected
            # Stop any currently playing song
            pygame.mixer.music.stop() 
            
            # If a song was playing, push it to history stack
            if self.current_song_node:
                self.history.append(self.current_song_node) # STACK PUSH
                
            # Set new song
            self.current_song_node = selected_node
            self.play_from_node(self.current_song_node)

    def stop_music(self):
        """Stops the music playback."""
        pygame.mixer.music.stop()
        self.is_playing = False
        self.is_paused = False
        self.play_button.config(text="▶ Play")
        self.unhighlight_all()

    def next_song(self):
        """Plays the next song in the Doubly Linked List."""
        if not self.current_song_node:
            messagebox.showwarning("No Song", "No song is currently playing.")
            return
            
        if not self.current_song_node.next:
            messagebox.showinfo("End of Playlist", "You've reached the end of the playlist.")
            return
        
        # Push current song to history (STACK PUSH)
        self.history.append(self.current_song_node)
        
        # Move to next node (DLL Navigation)
        self.current_song_node = self.current_song_node.next
        
        # Play the new song (this automatically stops the old one)
        self.play_from_node(self.current_song_node)

    def prev_song(self):
        """Plays the previous song from the Stack."""
        if not self.history:
            messagebox.showinfo("No History", "No previous songs in history.")
            return
            
        # Pop from history (STACK POP)
        self.current_song_node = self.history.pop()
        
        # Play the new song (this automatically stops the old one)
        self.play_from_node(self.current_song_node)

    def play_from_node(self, node):
        """Helper function to load and play a song from its node."""
        if not node:
            return
        try:
            pygame.mixer.music.load(node.data)
            pygame.mixer.music.play()
            self.is_playing = True
            self.is_paused = False
            self.play_button.config(text="❚❚ Pause")
            self.highlight_current_song()
        except pygame.error as e:
            messagebox.showerror("Playback Error", f"Could not play song:\n{os.path.basename(node.data)}\n\nError: {e}")
            self.is_playing = False
            self.is_paused = False
            self.play_button.config(text="▶ Play")

    def search_song(self):
        """Searches for a song using the HashMap (O(1))."""
        query = self.search_entry.get().strip()
        if not query:
            return

        # Find node in HashMap
        found_node = self.song_map.get(query)
        
        if not found_node:
            # Simple partial match if exact fails
            for song_name in self.song_map.keys():
                if query.lower() in song_name.lower():
                    found_node = self.song_map[song_name]
                    break
        
        if found_node:
            song_name = os.path.basename(found_node.data)
            # Find in listbox
            list_items = self.playlist_box.get(0, "end")
            try:
                index = list_items.index(song_name)
                
                # Highlight in UI
                self.playlist_box.selection_clear(0, "end")
                self.playlist_box.selection_set(index)
                self.playlist_box.activate(index)
                self.playlist_box.see(index)
                
                messagebox.showinfo("Found", f"Found '{song_name}'!")
            except ValueError:
                pass # Should not happen if map is synced
        else:
            messagebox.showinfo("Not Found", f"Could not find a song matching '{query}'.")

    # --- UI & Event Utility Functions ---
    
    def check_music_event(self):
        """Checks if the music has finished playing."""
        for event in pygame.event.get():
            if event.type == self.SONG_END_EVENT:
                # Song finished
                self.is_playing = False
                self.is_paused = False
                self.play_button.config(text="▶ Play")
                self.unhighlight_all()
                # Optional: auto-play next
                # self.next_song() 
        
        # Check again after 100ms
        self.root.after(100, self.check_music_event)

    def highlight_current_song(self):
        """Highlights the currently playing song in the listbox."""
        self.unhighlight_all()
        if self.current_song_node:
            song_name = os.path.basename(self.current_song_node.data)
            list_items = self.playlist_box.get(0, "end")
            try:
                index = list_items.index(song_name)
                self.playlist_box.itemconfig(index, bg="#2A4A6A", fg="white")
                
                # Also select it
                self.playlist_box.selection_clear(0, "end")
                self.playlist_box.selection_set(index)
                self.playlist_box.activate(index)
            except ValueError:
                pass # Song not in listbox, map is out of sync

    def unhighlight_all(self):
        """Resets the background color for all items in the listbox."""
        for i in range(self.playlist_box.size()):
            self.playlist_box.itemconfig(i, bg=self.listbox_bg, fg=self.listbox_fg)


# --- 10. Main Execution ---
if __name__ == "__main__":
    root = tk.Tk()
    app = MusicPlayer(root)
    
    def on_closing():
        # Clean up pygame
        pygame.mixer.quit()
        pygame.quit()
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()