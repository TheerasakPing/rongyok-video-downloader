"""
Video Merger
Uses FFmpeg to merge multiple video files into one
"""

import os
import subprocess
import shutil
import platform
from pathlib import Path
from typing import Optional, Callable


class VideoMerger:
    """Merges multiple video files using FFmpeg"""

    def __init__(self):
        self.ffmpeg_path = self._find_ffmpeg()

    def _find_ffmpeg(self) -> Optional[str]:
        """Find FFmpeg executable"""
        # Check if ffmpeg is in PATH
        ffmpeg = shutil.which('ffmpeg')
        if ffmpeg:
            return ffmpeg

        # Check common locations
        common_paths = [
            '/usr/local/bin/ffmpeg',
            '/usr/bin/ffmpeg',
            '/opt/homebrew/bin/ffmpeg',
            'C:\\ffmpeg\\bin\\ffmpeg.exe',
            'C:\\Program Files\\ffmpeg\\bin\\ffmpeg.exe',
        ]

        for path in common_paths:
            if os.path.exists(path):
                return path

        return None

    def is_available(self) -> bool:
        """Check if FFmpeg is available"""
        return self.ffmpeg_path is not None

    def get_video_duration(self, video_path: str) -> float:
        """Get video duration in seconds"""
        if not self.ffmpeg_path:
            return 0.0

        try:
            # Derive ffprobe path correctly (handle windows paths)
            ffmpeg_path = Path(self.ffmpeg_path)
            ffprobe_name = ffmpeg_path.name.replace('ffmpeg', 'ffprobe')
            ffprobe_path = str(ffmpeg_path.parent / ffprobe_name)

            result = subprocess.run(
                [
                    ffprobe_path,
                    '-v', 'error',
                    '-show_entries', 'format=duration',
                    '-of', 'default=noprint_wrappers=1:nokey=1',
                    video_path
                ],
                capture_output=True,
                text=True,
                timeout=30
            )
            return float(result.stdout.strip())
        except (subprocess.TimeoutExpired, ValueError):
            return 0.0

    def merge_videos(
        self,
        video_files: list[str],
        output_path: str,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> bool:
        """
        Merge multiple video files into one

        Args:
            video_files: List of video file paths (in order)
            output_path: Output file path
            progress_callback: Optional callback(current, total)

        Returns:
            True if successful
        """
        if not self.ffmpeg_path:
            print("Error: FFmpeg not found. Please install FFmpeg.")
            print("  macOS: brew install ffmpeg")
            print("  Ubuntu: sudo apt install ffmpeg")
            print("  Windows: Download from https://ffmpeg.org/download.html")
            return False

        if not video_files:
            print("Error: No video files to merge")
            return False

        # Verify all input files exist
        for vf in video_files:
            if not os.path.exists(vf):
                print(f"Error: File not found: {vf}")
                return False

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Create concat file
        concat_file = output_path.parent / "concat_list.txt"

        try:
            # Write concat list
            with open(concat_file, 'w', encoding='utf-8') as f:
                for video_file in video_files:
                    # Use absolute path and escape single quotes
                    abs_path = os.path.abspath(video_file)

                    if platform.system() == 'Windows':
                        # Windows: Use forward slashes and escape with backslash
                        escaped_path = abs_path.replace('\\', '/').replace("'", "\\'")
                    else:
                        # Unix: Use shell-style escaping
                        escaped_path = abs_path.replace("'", "'\\''")

                    f.write(f"file '{escaped_path}'\n")

            print(f"Merging {len(video_files)} videos...")

            # Run FFmpeg concat
            cmd = [
                self.ffmpeg_path,
                '-f', 'concat',
                '-safe', '0',
                '-i', str(concat_file),
                '-c', 'copy',  # Copy without re-encoding (fast)
                '-y',  # Overwrite output
                str(output_path)
            ]

            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )

            # Wait for completion
            stdout, stderr = process.communicate()

            if process.returncode != 0:
                print(f"FFmpeg error: {stderr}")
                return False

            # Verify output
            if output_path.exists() and output_path.stat().st_size > 0:
                print(f"Merged successfully: {output_path}")
                return True
            else:
                print("Error: Output file not created")
                return False

        except subprocess.TimeoutExpired:
            print("Error: FFmpeg timed out")
            return False
        except Exception as e:
            print(f"Error during merge: {e}")
            return False
        finally:
            # Cleanup concat file
            if concat_file.exists():
                concat_file.unlink()

    def merge_with_progress(
        self,
        video_files: list[str],
        output_path: str,
        progress_callback: Optional[Callable[[float], None]] = None
    ) -> bool:
        """
        Merge with progress tracking (requires re-encoding, slower)

        Args:
            video_files: List of video file paths
            output_path: Output file path
            progress_callback: Callback with progress 0.0-1.0

        Returns:
            True if successful
        """
        if not self.ffmpeg_path:
            print("Error: FFmpeg not found")
            return False

        # Get total duration
        total_duration = sum(self.get_video_duration(vf) for vf in video_files)
        if total_duration == 0:
            # Fallback to simple merge
            return self.merge_videos(video_files, output_path)

        output_path = Path(output_path)
        concat_file = output_path.parent / "concat_list.txt"

        try:
            # Write concat list
            with open(concat_file, 'w', encoding='utf-8') as f:
                for video_file in video_files:
                    abs_path = os.path.abspath(video_file)

                    if platform.system() == 'Windows':
                        # Windows: Use forward slashes and escape with backslash
                        escaped_path = abs_path.replace('\\', '/').replace("'", "\\'")
                    else:
                        # Unix: Use shell-style escaping
                        escaped_path = abs_path.replace("'", "'\\''")

                    f.write(f"file '{escaped_path}'\n")

            # Run FFmpeg with progress
            cmd = [
                self.ffmpeg_path,
                '-f', 'concat',
                '-safe', '0',
                '-i', str(concat_file),
                '-c', 'copy',
                '-progress', 'pipe:1',
                '-y',
                str(output_path)
            ]

            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )

            # Parse progress output
            current_time = 0
            for line in process.stdout:
                if line.startswith('out_time_ms='):
                    try:
                        time_ms = int(line.split('=')[1])
                        current_time = time_ms / 1000000  # Convert to seconds
                        if progress_callback and total_duration > 0:
                            progress = min(current_time / total_duration, 1.0)
                            progress_callback(progress)
                    except ValueError:
                        pass

            process.wait()

            if process.returncode != 0:
                stderr = process.stderr.read()
                print(f"FFmpeg error: {stderr}")
                return False

            return output_path.exists() and output_path.stat().st_size > 0

        except Exception as e:
            print(f"Error: {e}")
            return False
        finally:
            if concat_file.exists():
                concat_file.unlink()


# Test
if __name__ == "__main__":
    merger = VideoMerger()

    if merger.is_available():
        print(f"FFmpeg found: {merger.ffmpeg_path}")
    else:
        print("FFmpeg not found!")
        print("Please install FFmpeg:")
        print("  macOS: brew install ffmpeg")
        print("  Ubuntu: sudo apt install ffmpeg")
