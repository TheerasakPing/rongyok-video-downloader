#!/usr/bin/env python3
"""
Rongyok Video Downloader - GUI Interface
Desktop application with Tkinter + Debug Log
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
import queue
import sys
import io
from pathlib import Path
from typing import Optional
from datetime import datetime

from parser import RongyokParser, SeriesInfo
from downloader import VideoDownloader
from merger import VideoMerger


class LogRedirector(io.StringIO):
    """Redirect stdout/stderr to a queue for GUI display"""

    def __init__(self, log_queue: queue.Queue, original_stream):
        super().__init__()
        self.log_queue = log_queue
        self.original_stream = original_stream

    def write(self, text):
        if text.strip():  # Ignore empty lines
            self.log_queue.put(('log', text.strip()))
        # Also write to original stream
        if self.original_stream:
            self.original_stream.write(text)
            self.original_stream.flush()

    def flush(self):
        if self.original_stream:
            self.original_stream.flush()


class DownloaderGUI:
    """Main GUI Application with Debug Log"""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Rongyok Video Downloader")
        self.root.geometry("800x700")
        self.root.minsize(700, 600)

        # Components
        self.parser = RongyokParser()
        self.downloader: Optional[VideoDownloader] = None
        self.merger = VideoMerger()

        # State
        self.series_info: Optional[SeriesInfo] = None
        self.episode_vars: list[tk.BooleanVar] = []
        self.is_downloading = False
        self.message_queue = queue.Queue()

        # Build UI
        self._create_widgets()
        self._setup_styles()

        # Redirect stdout/stderr to log
        self._setup_log_redirect()

        # Start message processing
        self._process_messages()

        # Initial log
        self._log("Application started")
        self._log(f"FFmpeg available: {self.merger.is_available()}")
        if self.merger.ffmpeg_path:
            self._log(f"FFmpeg path: {self.merger.ffmpeg_path}")

    def _setup_styles(self):
        """Setup ttk styles"""
        style = ttk.Style()
        style.configure('Title.TLabel', font=('Helvetica', 16, 'bold'))
        style.configure('Status.TLabel', font=('Helvetica', 10))

    def _setup_log_redirect(self):
        """Redirect print statements to log panel"""
        self.original_stdout = sys.stdout
        self.original_stderr = sys.stderr
        sys.stdout = LogRedirector(self.message_queue, self.original_stdout)
        sys.stderr = LogRedirector(self.message_queue, self.original_stderr)

    def _log(self, message: str):
        """Add a log message with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.message_queue.put(('log', f"[{timestamp}] {message}"))

    def _create_widgets(self):
        """Create all UI widgets"""

        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Tab 1: Main
        main_tab = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(main_tab, text="Download")

        # Tab 2: Debug Log
        log_tab = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(log_tab, text="Debug Log")

        # === MAIN TAB ===
        self._create_main_tab(main_tab)

        # === LOG TAB ===
        self._create_log_tab(log_tab)

    def _create_main_tab(self, parent):
        """Create main download tab"""

        # Title
        title_label = ttk.Label(
            parent,
            text="🎬 Rongyok Video Downloader",
            style='Title.TLabel'
        )
        title_label.pack(pady=(0, 10))

        # URL Frame
        url_frame = ttk.LabelFrame(parent, text="Series URL", padding="5")
        url_frame.pack(fill=tk.X, pady=5)

        self.url_var = tk.StringVar()
        url_entry = ttk.Entry(url_frame, textvariable=self.url_var, width=60)
        url_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))

        paste_btn = ttk.Button(url_frame, text="Paste", command=self._paste_url)
        paste_btn.pack(side=tk.RIGHT, padx=(0, 5))

        fetch_btn = ttk.Button(url_frame, text="Fetch", command=self._fetch_series)
        fetch_btn.pack(side=tk.RIGHT)

        # Output Frame
        output_frame = ttk.LabelFrame(parent, text="Output Directory", padding="5")
        output_frame.pack(fill=tk.X, pady=5)

        self.output_var = tk.StringVar(value="./output")
        output_entry = ttk.Entry(output_frame, textvariable=self.output_var, width=60)
        output_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))

        browse_btn = ttk.Button(output_frame, text="Browse", command=self._browse_output)
        browse_btn.pack(side=tk.RIGHT)

        # Series Info Frame
        self.info_frame = ttk.LabelFrame(parent, text="Series Info", padding="5")
        self.info_frame.pack(fill=tk.X, pady=5)

        self.info_label = ttk.Label(self.info_frame, text="Enter a URL and click Fetch")
        self.info_label.pack()

        # Episode Selection Frame
        episode_frame = ttk.LabelFrame(parent, text="Episodes", padding="5")
        episode_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        # Selection buttons
        btn_frame = ttk.Frame(episode_frame)
        btn_frame.pack(fill=tk.X, pady=(0, 5))

        select_all_btn = ttk.Button(btn_frame, text="Select All", command=self._select_all)
        select_all_btn.pack(side=tk.LEFT, padx=2)

        deselect_all_btn = ttk.Button(btn_frame, text="Deselect All", command=self._deselect_all)
        deselect_all_btn.pack(side=tk.LEFT, padx=2)

        # Episode grid with scrollbar
        canvas_frame = ttk.Frame(episode_frame)
        canvas_frame.pack(fill=tk.BOTH, expand=True)

        self.episode_canvas = tk.Canvas(canvas_frame, highlightthickness=0, height=120)
        scrollbar = ttk.Scrollbar(canvas_frame, orient=tk.VERTICAL, command=self.episode_canvas.yview)

        self.episode_inner_frame = ttk.Frame(self.episode_canvas)

        self.episode_canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.episode_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.canvas_window = self.episode_canvas.create_window(
            (0, 0),
            window=self.episode_inner_frame,
            anchor=tk.NW
        )

        self.episode_inner_frame.bind('<Configure>', self._on_frame_configure)
        self.episode_canvas.bind('<Configure>', self._on_canvas_configure)
        self.episode_canvas.bind_all('<MouseWheel>', self._on_mousewheel)

        # Progress Frame
        progress_frame = ttk.LabelFrame(parent, text="Progress", padding="5")
        progress_frame.pack(fill=tk.X, pady=5)

        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            progress_frame,
            variable=self.progress_var,
            maximum=100
        )
        self.progress_bar.pack(fill=tk.X, pady=2)

        self.status_var = tk.StringVar(value="Ready")
        status_label = ttk.Label(progress_frame, textvariable=self.status_var, style='Status.TLabel')
        status_label.pack()

        # Options Frame
        options_frame = ttk.Frame(parent)
        options_frame.pack(fill=tk.X, pady=5)

        self.merge_var = tk.BooleanVar(value=True)
        merge_check = ttk.Checkbutton(
            options_frame,
            text="Merge videos after download",
            variable=self.merge_var
        )
        merge_check.pack(side=tk.LEFT)

        # Control Buttons
        control_frame = ttk.Frame(parent)
        control_frame.pack(fill=tk.X, pady=10)

        self.download_btn = ttk.Button(
            control_frame,
            text="Download",
            command=self._start_download
        )
        self.download_btn.pack(side=tk.LEFT, padx=5)

        self.pause_btn = ttk.Button(
            control_frame,
            text="Pause",
            command=self._pause_download,
            state=tk.DISABLED
        )
        self.pause_btn.pack(side=tk.LEFT, padx=5)

        self.resume_btn = ttk.Button(
            control_frame,
            text="Resume",
            command=self._resume_download,
            state=tk.DISABLED
        )
        self.resume_btn.pack(side=tk.LEFT, padx=5)

        self.cancel_btn = ttk.Button(
            control_frame,
            text="Cancel",
            command=self._cancel_download,
            state=tk.DISABLED
        )
        self.cancel_btn.pack(side=tk.LEFT, padx=5)

        self.resume_prev_btn = ttk.Button(
            control_frame,
            text="Resume Previous",
            command=self._resume_previous
        )
        self.resume_prev_btn.pack(side=tk.RIGHT, padx=5)

    def _create_log_tab(self, parent):
        """Create debug log tab"""

        # Header
        header_frame = ttk.Frame(parent)
        header_frame.pack(fill=tk.X, pady=(0, 5))

        ttk.Label(header_frame, text="Debug Log", font=('Helvetica', 14, 'bold')).pack(side=tk.LEFT)

        clear_btn = ttk.Button(header_frame, text="Clear Log", command=self._clear_log)
        clear_btn.pack(side=tk.RIGHT)

        copy_btn = ttk.Button(header_frame, text="Copy Log", command=self._copy_log)
        copy_btn.pack(side=tk.RIGHT, padx=5)

        # Log text area
        self.log_text = scrolledtext.ScrolledText(
            parent,
            wrap=tk.WORD,
            font=('Consolas', 10),
            bg='#1e1e1e',
            fg='#d4d4d4',
            insertbackground='white'
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)

        # Configure tags for colored output
        self.log_text.tag_config('timestamp', foreground='#6a9955')
        self.log_text.tag_config('error', foreground='#f14c4c')
        self.log_text.tag_config('success', foreground='#4ec9b0')
        self.log_text.tag_config('info', foreground='#569cd6')
        self.log_text.tag_config('warning', foreground='#ce9178')

    def _clear_log(self):
        """Clear the log text"""
        self.log_text.delete(1.0, tk.END)
        self._log("Log cleared")

    def _copy_log(self):
        """Copy log to clipboard"""
        log_content = self.log_text.get(1.0, tk.END)
        self.root.clipboard_clear()
        self.root.clipboard_append(log_content)
        self._log("Log copied to clipboard")

    def _append_log(self, message: str):
        """Append message to log with auto-scroll"""
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)

        # Color code based on content
        if "error" in message.lower() or "failed" in message.lower():
            self._highlight_last_line('error')
        elif "success" in message.lower() or "complete" in message.lower():
            self._highlight_last_line('success')
        elif "warning" in message.lower():
            self._highlight_last_line('warning')

    def _highlight_last_line(self, tag: str):
        """Highlight the last line with a tag"""
        self.log_text.tag_add(tag, "end-2l", "end-1l")

    def _on_frame_configure(self, event):
        """Update scroll region when frame size changes"""
        self.episode_canvas.configure(scrollregion=self.episode_canvas.bbox("all"))

    def _on_canvas_configure(self, event):
        """Update inner frame width when canvas resizes"""
        self.episode_canvas.itemconfig(self.canvas_window, width=event.width)

    def _on_mousewheel(self, event):
        """Handle mouse wheel scrolling"""
        self.episode_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _paste_url(self):
        """Paste URL from clipboard"""
        try:
            clipboard_content = self.root.clipboard_get()
            self.url_var.set(clipboard_content)
            self._log(f"Pasted URL: {clipboard_content}")
        except tk.TclError:
            self._log("Clipboard is empty or contains non-text data")
            messagebox.showwarning("Warning", "Clipboard is empty or contains non-text data")

    def _browse_output(self):
        """Open folder browser dialog"""
        folder = filedialog.askdirectory(initialdir=self.output_var.get())
        if folder:
            self.output_var.set(folder)
            self._log(f"Output directory set to: {folder}")

    def _fetch_series(self):
        """Fetch series information from URL"""
        url = self.url_var.get().strip()
        if not url:
            messagebox.showwarning("Warning", "Please enter a URL")
            return

        self._log(f"Fetching URL: {url}")

        series_id = self.parser.parse_series_url(url)
        if not series_id:
            self._log(f"ERROR: Invalid URL - could not extract series_id")
            messagebox.showerror("Error", "Invalid URL. Could not extract series_id")
            return

        self._log(f"Parsed series_id: {series_id}")
        self.status_var.set("Fetching series info...")
        self.root.update()

        # Fetch in background
        def fetch():
            self._log("Starting HTTP request...")
            try:
                series_info = self.parser.get_series_info(series_id)
                if series_info:
                    self._log(f"SUCCESS: Got series info - {series_info.title}")
                    self._log(f"  Total episodes: {series_info.total_episodes}")
                    self._log(f"  Cached URLs: {len(series_info.episode_urls) if series_info.episode_urls else 0}")
                    if series_info.episode_urls:
                        for ep, url in list(series_info.episode_urls.items())[:3]:
                            self._log(f"  Episode {ep}: {url[:60]}...")
                else:
                    self._log("ERROR: Failed to get series info - returned None")
                self.message_queue.put(('series_info', series_info))
            except Exception as e:
                self._log(f"ERROR: Exception during fetch: {str(e)}")
                import traceback
                self._log(traceback.format_exc())
                self.message_queue.put(('series_info', None))

        threading.Thread(target=fetch, daemon=True).start()

    def _update_series_info(self, series_info: Optional[SeriesInfo]):
        """Update UI with series info"""
        if not series_info:
            self.info_label.config(text="Error: Could not fetch series info")
            self.status_var.set("Error")
            self._log("Failed to update UI - no series info")
            return

        self.series_info = series_info

        # Update info label
        self.info_label.config(
            text=f"Title: {series_info.title}\nEpisodes: {series_info.total_episodes}"
        )

        # Clear existing checkboxes
        for widget in self.episode_inner_frame.winfo_children():
            widget.destroy()
        self.episode_vars.clear()

        # Create episode checkboxes in grid
        cols = 5
        for i in range(series_info.total_episodes):
            var = tk.BooleanVar(value=True)
            self.episode_vars.append(var)

            cb = ttk.Checkbutton(
                self.episode_inner_frame,
                text=f"Ep {i+1}",
                variable=var,
                width=8
            )
            row, col = divmod(i, cols)
            cb.grid(row=row, column=col, padx=2, pady=2, sticky=tk.W)

        self.status_var.set("Ready")
        self._log(f"UI updated with {series_info.total_episodes} episodes")

    def _select_all(self):
        """Select all episodes"""
        for var in self.episode_vars:
            var.set(True)

    def _deselect_all(self):
        """Deselect all episodes"""
        for var in self.episode_vars:
            var.set(False)

    def _get_selected_episodes(self) -> list[int]:
        """Get list of selected episode numbers"""
        return [i + 1 for i, var in enumerate(self.episode_vars) if var.get()]

    def _start_download(self):
        """Start downloading selected episodes"""
        if not self.series_info:
            messagebox.showwarning("Warning", "Please fetch series info first")
            return

        selected = self._get_selected_episodes()
        if not selected:
            messagebox.showwarning("Warning", "Please select at least one episode")
            return

        self._log(f"Starting download of {len(selected)} episodes: {selected}")

        # Initialize downloader
        output_dir = self.output_var.get()
        self._log(f"Output directory: {output_dir}")

        self.downloader = VideoDownloader(output_dir)
        self.downloader.init_state(self.series_info, selected)

        # Update UI state
        self.is_downloading = True
        self._update_button_states()

        # Start download thread
        threading.Thread(
            target=self._download_thread,
            args=(self.series_info.series_id, selected),
            daemon=True
        ).start()

    def _download_thread(self, series_id: int, episodes: list[int]):
        """Download thread"""
        try:
            total = len(episodes)
            completed = 0

            for ep_num in episodes:
                if self.downloader.is_cancelled():
                    self._log("Download cancelled by user")
                    break

                # Skip completed
                if self.downloader.state and ep_num in self.downloader.state.completed_episodes:
                    completed += 1
                    self._log(f"Episode {ep_num}: Already downloaded, skipping")
                    self.message_queue.put(('progress', completed, total, f"Episode {ep_num} already downloaded"))
                    continue

                self._log(f"Fetching video URL for episode {ep_num}...")
                self.message_queue.put(('status', f"Fetching episode {ep_num}..."))

                # Get episode URL
                episode_info = self.parser.get_episode_video_url(series_id, ep_num)

                if not episode_info:
                    self._log(f"ERROR: Could not get URL for episode {ep_num}")
                    self.message_queue.put(('status', f"Error: Could not get URL for episode {ep_num}"))
                    continue

                self._log(f"Episode {ep_num} URL: {episode_info.video_url[:80]}...")
                self._log(f"Starting download of episode {ep_num}...")
                self.message_queue.put(('status', f"Downloading episode {ep_num}..."))

                # Download with progress callback
                def progress_cb(downloaded, total_bytes, speed):
                    pct = (downloaded / total_bytes * 100) if total_bytes > 0 else 0
                    speed_mb = speed / 1024 / 1024
                    self.message_queue.put((
                        'download_progress',
                        pct,
                        f"Episode {ep_num}: {pct:.1f}% ({speed_mb:.1f} MB/s)"
                    ))

                success = self.downloader.download_episode(
                    episode_info,
                    progress_callback=progress_cb,
                    use_tqdm=False
                )

                if success:
                    completed += 1
                    self._log(f"SUCCESS: Episode {ep_num} downloaded")
                else:
                    self._log(f"FAILED: Episode {ep_num} download failed")

                self.message_queue.put(('progress', completed, total, f"Completed {completed}/{total}"))

            # Merge if requested
            if self.merge_var.get() and not self.downloader.is_cancelled() and completed > 0:
                self._log("Starting video merge...")
                self.message_queue.put(('status', "Merging videos..."))
                self._merge_videos(episodes)

            self._log(f"Download complete: {completed}/{total} episodes")
            self.message_queue.put(('complete', completed, total))

        except Exception as e:
            self._log(f"ERROR: Exception in download thread: {str(e)}")
            import traceback
            self._log(traceback.format_exc())
            self.message_queue.put(('error', str(e)))

    def _merge_videos(self, episodes: list[int]):
        """Merge downloaded videos"""
        if not self.merger.is_available():
            self._log("ERROR: FFmpeg not found, skipping merge")
            self.message_queue.put(('status', "FFmpeg not found, skipping merge"))
            return

        video_files = []
        for ep in sorted(episodes):
            video_path = self.downloader.get_episode_filename(ep)
            if video_path.exists():
                video_files.append(str(video_path))
                self._log(f"  Found: {video_path}")

        if len(video_files) < 2:
            self._log("Not enough videos to merge (need at least 2)")
            return

        self._log(f"Merging {len(video_files)} videos...")

        # Use series title for filename
        if self.series_info and self.series_info.title:
            import re
            safe_title = re.sub(r'[<>:"/\\|?*]', '', self.series_info.title)
            safe_title = re.sub(r'\s+', ' ', safe_title).strip()
            if len(safe_title) > 100:
                safe_title = safe_title[:100]
            output_path = self.downloader.output_dir / f"{safe_title}.mp4"
        else:
            output_path = self.downloader.output_dir / "merged.mp4"

        self._log(f"Output file: {output_path}")

        def progress_cb(progress: float):
            self.message_queue.put(('merge_progress', progress * 100))

        success = self.merger.merge_with_progress(
            video_files,
            str(output_path),
            progress_callback=progress_cb
        )

        if success:
            self._log(f"SUCCESS: Merged to {output_path}")
            self.message_queue.put(('status', f"Merged to: {output_path}"))

            # Delete individual episode files after successful merge
            self._log("Cleaning up episode files...")
            self.message_queue.put(('status', "Cleaning up episode files..."))
            from pathlib import Path
            deleted_count = 0
            for video_file in video_files:
                try:
                    Path(video_file).unlink()
                    deleted_count += 1
                    self._log(f"  Deleted: {video_file}")
                except Exception as e:
                    self._log(f"  Warning: Could not delete {video_file}: {e}")
            self._log(f"Deleted {deleted_count} episode files")
            self.message_queue.put(('status', f"Merged to: {output_path.name} (deleted {deleted_count} ep files)"))
        else:
            self._log("ERROR: Merge failed")

    def _pause_download(self):
        """Pause current download"""
        if self.downloader:
            self.downloader.pause()
            self._log("Download paused")
            self.status_var.set("Paused")
            self.pause_btn.config(state=tk.DISABLED)
            self.resume_btn.config(state=tk.NORMAL)

    def _resume_download(self):
        """Resume paused download"""
        if self.downloader:
            self.downloader.resume()
            self._log("Download resumed")
            self.status_var.set("Resuming...")
            self.pause_btn.config(state=tk.NORMAL)
            self.resume_btn.config(state=tk.DISABLED)

    def _cancel_download(self):
        """Cancel current download"""
        if self.downloader:
            self.downloader.cancel()
            self._log("Download cancellation requested")
            self.status_var.set("Cancelling...")

    def _resume_previous(self):
        """Resume a previous download session"""
        output_dir = self.output_var.get()
        state_file = Path(output_dir) / "download_state.json"

        self._log(f"Looking for previous session in: {state_file}")

        if not state_file.exists():
            self._log("No previous download state found")
            messagebox.showinfo("Info", "No previous download found in this directory")
            return

        self.downloader = VideoDownloader(output_dir)
        state = self.downloader.load_state()

        if not state:
            self._log("ERROR: Could not load download state")
            messagebox.showerror("Error", "Could not load download state")
            return

        self._log(f"Loaded previous session: {state.series_title}")
        self._log(f"  Completed: {len(state.completed_episodes)}/{len(state.selected_episodes)}")

        # Update UI
        self.url_var.set(f"https://rongyok.com/watch/?series_id={state.series_id}")

        # Fetch series info
        self.series_info = self.parser.get_series_info(state.series_id)
        if self.series_info:
            self._update_series_info(self.series_info)

            # Select only remaining episodes
            remaining = self.downloader.get_remaining_episodes()
            for i, var in enumerate(self.episode_vars):
                var.set((i + 1) in remaining)

            self._log(f"Remaining episodes: {remaining}")

            messagebox.showinfo(
                "Resume",
                f"Loaded previous session:\n"
                f"Series: {state.series_title}\n"
                f"Completed: {len(state.completed_episodes)}/{len(state.selected_episodes)}\n"
                f"Remaining: {len(remaining)} episodes\n\n"
                f"Click Download to continue."
            )

    def _update_button_states(self):
        """Update button states based on download status"""
        if self.is_downloading:
            self.download_btn.config(state=tk.DISABLED)
            self.pause_btn.config(state=tk.NORMAL)
            self.resume_btn.config(state=tk.DISABLED)
            self.cancel_btn.config(state=tk.NORMAL)
            self.resume_prev_btn.config(state=tk.DISABLED)
        else:
            self.download_btn.config(state=tk.NORMAL)
            self.pause_btn.config(state=tk.DISABLED)
            self.resume_btn.config(state=tk.DISABLED)
            self.cancel_btn.config(state=tk.DISABLED)
            self.resume_prev_btn.config(state=tk.NORMAL)

    def _process_messages(self):
        """Process messages from background threads"""
        try:
            while True:
                msg = self.message_queue.get_nowait()
                msg_type = msg[0]

                if msg_type == 'log':
                    self._append_log(msg[1])

                elif msg_type == 'series_info':
                    self._update_series_info(msg[1])

                elif msg_type == 'status':
                    self.status_var.set(msg[1])

                elif msg_type == 'progress':
                    completed, total, status = msg[1], msg[2], msg[3]
                    pct = (completed / total * 100) if total > 0 else 0
                    self.progress_var.set(pct)
                    self.status_var.set(status)

                elif msg_type == 'download_progress':
                    self.progress_var.set(msg[1])
                    self.status_var.set(msg[2])

                elif msg_type == 'merge_progress':
                    self.progress_var.set(msg[1])
                    self.status_var.set(f"Merging: {msg[1]:.1f}%")

                elif msg_type == 'complete':
                    completed, total = msg[1], msg[2]
                    self.is_downloading = False
                    self._update_button_states()
                    self.progress_var.set(100)
                    self.status_var.set(f"Complete! Downloaded {completed}/{total} episodes")
                    messagebox.showinfo("Complete", f"Downloaded {completed}/{total} episodes")

                elif msg_type == 'error':
                    self.is_downloading = False
                    self._update_button_states()
                    self.status_var.set(f"Error: {msg[1]}")
                    messagebox.showerror("Error", msg[1])

        except queue.Empty:
            pass

        # Schedule next check
        self.root.after(100, self._process_messages)

    def run(self):
        """Start the application"""
        self.root.mainloop()

    def __del__(self):
        """Restore stdout/stderr on exit"""
        sys.stdout = self.original_stdout
        sys.stderr = self.original_stderr


def main():
    app = DownloaderGUI()
    app.run()


if __name__ == "__main__":
    main()
