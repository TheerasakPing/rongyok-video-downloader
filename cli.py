#!/usr/bin/env python3
"""
Rongyok Video Downloader - CLI Interface
Download videos from rongyok.com with resume support
"""

import argparse
import sys
import re
from pathlib import Path

from parser import RongyokParser
from downloader import VideoDownloader
from merger import VideoMerger


def parse_episode_range(episode_str: str, max_episode: int) -> list[int]:
    """
    Parse episode selection string

    Examples:
        "1-10" -> [1, 2, 3, ..., 10]
        "1,3,5" -> [1, 3, 5]
        "1-5,10,15-20" -> [1, 2, 3, 4, 5, 10, 15, 16, 17, 18, 19, 20]
        "all" -> [1, 2, ..., max_episode]
    """
    if episode_str.lower() == 'all':
        return list(range(1, max_episode + 1))

    episodes = set()

    for part in episode_str.split(','):
        part = part.strip()
        if '-' in part:
            # Range: 1-10
            match = re.match(r'(\d+)-(\d+)', part)
            if match:
                start, end = int(match.group(1)), int(match.group(2))
                start = max(1, min(start, max_episode))
                end = max(1, min(end, max_episode))
                episodes.update(range(start, end + 1))
        else:
            # Single episode
            try:
                ep = int(part)
                if 1 <= ep <= max_episode:
                    episodes.add(ep)
            except ValueError:
                pass

    return sorted(episodes)


def format_size(size_bytes: int) -> str:
    """Format bytes to human readable string"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"


def main():
    parser = argparse.ArgumentParser(
        description='Download videos from rongyok.com',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s https://rongyok.com/watch/?series_id=941
  %(prog)s https://rongyok.com/watch/?series_id=941 --episodes 1-10
  %(prog)s https://rongyok.com/watch/?series_id=941 --episodes 1,3,5,7
  %(prog)s https://rongyok.com/watch/?series_id=941 --resume
  %(prog)s https://rongyok.com/watch/?series_id=941 --no-merge
        """
    )

    parser.add_argument(
        'url',
        nargs='?',
        help='Rongyok series URL (e.g., https://rongyok.com/watch/?series_id=941)'
    )

    parser.add_argument(
        '-e', '--episodes',
        default='all',
        help='Episodes to download (e.g., "1-10", "1,3,5", "all"). Default: all'
    )

    parser.add_argument(
        '-o', '--output',
        default='./output',
        help='Output directory. Default: ./output'
    )

    parser.add_argument(
        '-r', '--resume',
        action='store_true',
        help='Resume previous download'
    )

    parser.add_argument(
        '--no-merge',
        action='store_true',
        help='Skip merging videos after download'
    )

    parser.add_argument(
        '--merge-only',
        action='store_true',
        help='Only merge existing videos without downloading'
    )

    parser.add_argument(
        '-l', '--list',
        action='store_true',
        help='List episodes without downloading'
    )

    args = parser.parse_args()

    # Handle merge-only mode
    if args.merge_only:
        merge_existing_videos(args.output)
        return

    # Require URL for other operations
    if not args.url:
        parser.print_help()
        sys.exit(1)

    # Initialize components
    rongyok_parser = RongyokParser()
    downloader = VideoDownloader(args.output)
    merger = VideoMerger()

    # Check for resume
    if args.resume:
        state = downloader.load_state()
        if state:
            print(f"Resuming download: {state.series_title}")
            print(f"Completed: {len(state.completed_episodes)}/{len(state.selected_episodes)}")

            # Get remaining episodes
            remaining = downloader.get_remaining_episodes()
            if not remaining:
                print("All episodes already downloaded!")
                if not args.no_merge:
                    merge_downloaded(downloader, merger, state.selected_episodes, state.series_title)
                return

            print(f"Remaining episodes: {remaining}")
            download_episodes(
                rongyok_parser,
                downloader,
                state.series_id,
                remaining,
                args.no_merge,
                merger,
                state.series_title
            )
            return
        else:
            print("No previous download state found. Starting fresh.")

    # Parse series URL
    series_id = rongyok_parser.parse_series_url(args.url)
    if not series_id:
        print(f"Error: Invalid URL. Could not extract series_id from: {args.url}")
        sys.exit(1)

    # Get series info
    print(f"Fetching series info for ID: {series_id}...")
    series_info = rongyok_parser.get_series_info(series_id)

    if not series_info:
        print("Error: Could not fetch series information")
        sys.exit(1)

    print(f"\n{'='*50}")
    print(f"Series: {series_info.title}")
    print(f"Total Episodes: {series_info.total_episodes}")
    print(f"{'='*50}\n")

    # Parse episode selection
    selected_episodes = parse_episode_range(args.episodes, series_info.total_episodes)

    if not selected_episodes:
        print("Error: No valid episodes selected")
        sys.exit(1)

    # List mode
    if args.list:
        print("Selected episodes:")
        for ep in selected_episodes:
            print(f"  - Episode {ep}")
        print(f"\nTotal: {len(selected_episodes)} episodes")
        return

    print(f"Selected episodes: {selected_episodes}")
    print(f"Output directory: {args.output}")

    # Confirm
    response = input(f"\nDownload {len(selected_episodes)} episodes? [Y/n]: ").strip().lower()
    if response and response != 'y':
        print("Cancelled.")
        return

    # Initialize download state
    downloader.init_state(series_info, selected_episodes)

    # Download
    download_episodes(
        rongyok_parser,
        downloader,
        series_id,
        selected_episodes,
        args.no_merge,
        merger,
        series_info.title
    )


def download_episodes(
    rongyok_parser: RongyokParser,
    downloader: VideoDownloader,
    series_id: int,
    episodes: list[int],
    skip_merge: bool,
    merger: VideoMerger,
    series_title: str = None
):
    """Download selected episodes"""

    print(f"\nStarting download of {len(episodes)} episodes...\n")

    successful = 0
    failed = 0

    for i, ep_num in enumerate(episodes):
        # Skip already completed
        if downloader.state and ep_num in downloader.state.completed_episodes:
            print(f"Episode {ep_num}: Already downloaded, skipping")
            successful += 1
            continue

        print(f"\n[{i+1}/{len(episodes)}] Fetching episode {ep_num}...")

        # Get episode URL
        episode_info = rongyok_parser.get_episode_video_url(series_id, ep_num)

        if not episode_info:
            print(f"Error: Could not get video URL for episode {ep_num}")
            failed += 1
            continue

        # Download
        if downloader.download_episode(episode_info, use_tqdm=True):
            successful += 1
        else:
            failed += 1

    # Summary
    print(f"\n{'='*50}")
    print(f"Download Complete!")
    print(f"  Successful: {successful}")
    print(f"  Failed: {failed}")
    print(f"{'='*50}")

    # Merge if requested
    if not skip_merge and successful > 0:
        merge_downloaded(downloader, merger, episodes, series_title)


def sanitize_filename(name: str) -> str:
    """Remove invalid characters from filename"""
    import re
    # Remove invalid filename characters
    name = re.sub(r'[<>:"/\\|?*]', '', name)
    # Remove extra whitespace
    name = re.sub(r'\s+', ' ', name).strip()
    # Limit length
    if len(name) > 100:
        name = name[:100]
    return name


def merge_downloaded(downloader: VideoDownloader, merger: VideoMerger, episodes: list[int], series_title: str = None, delete_after_merge: bool = True):
    """Merge downloaded videos"""

    if not merger.is_available():
        print("\nWarning: FFmpeg not found. Cannot merge videos.")
        print("Install FFmpeg to enable video merging:")
        print("  macOS: brew install ffmpeg")
        print("  Ubuntu: sudo apt install ffmpeg")
        return

    # Get list of downloaded files
    video_files = []
    for ep in sorted(episodes):
        video_path = downloader.get_episode_filename(ep)
        if video_path.exists():
            video_files.append(str(video_path))

    if len(video_files) < 2:
        print("\nNot enough videos to merge (need at least 2)")
        return

    # Use series title for filename if provided
    if series_title:
        safe_title = sanitize_filename(series_title)
        output_path = downloader.output_dir / f"{safe_title}.mp4"
    else:
        output_path = downloader.output_dir / "merged.mp4"

    print(f"\nMerging {len(video_files)} videos...")
    if merger.merge_videos(video_files, str(output_path)):
        print(f"Merged video saved to: {output_path}")

        # Delete individual episode files after successful merge
        if delete_after_merge:
            print("Cleaning up individual episode files...")
            deleted_count = 0
            for video_file in video_files:
                try:
                    Path(video_file).unlink()
                    deleted_count += 1
                except Exception as e:
                    print(f"  Warning: Could not delete {video_file}: {e}")
            print(f"Deleted {deleted_count} episode files.")
    else:
        print("Failed to merge videos")


def merge_existing_videos(output_dir: str):
    """Merge existing videos in output directory"""

    merger = VideoMerger()
    if not merger.is_available():
        print("Error: FFmpeg not found")
        sys.exit(1)

    output_path = Path(output_dir)
    if not output_path.exists():
        print(f"Error: Directory not found: {output_dir}")
        sys.exit(1)

    # Find all episode files
    video_files = sorted(output_path.glob("ep_*.mp4"))

    if not video_files:
        print("No video files found matching pattern: ep_*.mp4")
        sys.exit(1)

    print(f"Found {len(video_files)} video files:")
    for vf in video_files:
        print(f"  - {vf.name}")

    merged_path = output_path / "merged.mp4"
    print(f"\nMerging to: {merged_path}")

    if merger.merge_videos([str(vf) for vf in video_files], str(merged_path)):
        print("Merge successful!")
    else:
        print("Merge failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
