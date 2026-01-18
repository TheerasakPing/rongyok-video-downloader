"""
Unit Tests for Rongyok Video Downloader
Tests download functionality, state management, and resume support
"""

import pytest
import json
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, mock_open
from io import BytesIO

# Import the modules under test
from downloader import VideoDownloader, DownloadState, DownloadProgress
from parser import EpisodeInfo, SeriesInfo


class TestDownloadProgress:
    """Tests for DownloadProgress dataclass"""

    def test_download_progress_creation(self):
        """Test basic DownloadProgress creation"""
        progress = DownloadProgress(
            episode=1,
            downloaded_bytes=1024,
            total_bytes=10240
        )
        assert progress.episode == 1
        assert progress.downloaded_bytes == 1024
        assert progress.total_bytes == 10240
        assert progress.completed is False

    def test_download_progress_completed(self):
        """Test DownloadProgress with completed flag"""
        progress = DownloadProgress(
            episode=5,
            downloaded_bytes=10240,
            total_bytes=10240,
            completed=True
        )
        assert progress.completed is True

    def test_download_progress_zero_bytes(self):
        """Test DownloadProgress with zero bytes"""
        progress = DownloadProgress(
            episode=1,
            downloaded_bytes=0,
            total_bytes=0
        )
        assert progress.downloaded_bytes == 0
        assert progress.total_bytes == 0


class TestDownloadState:
    """Tests for DownloadState dataclass"""

    @pytest.fixture
    def sample_state(self):
        """Create sample download state"""
        return DownloadState(
            series_id=941,
            series_title="Test Series",
            total_episodes=30,
            output_dir="./output",
            selected_episodes=[1, 2, 3, 4, 5],
            completed_episodes=[1, 2]
        )

    def test_download_state_creation(self, sample_state):
        """Test basic DownloadState creation"""
        assert sample_state.series_id == 941
        assert sample_state.series_title == "Test Series"
        assert sample_state.total_episodes == 30
        assert sample_state.output_dir == "./output"
        assert sample_state.selected_episodes == [1, 2, 3, 4, 5]
        assert sample_state.completed_episodes == [1, 2]
        assert sample_state.current_episode is None
        assert sample_state.current_progress is None

    def test_download_state_with_current_progress(self):
        """Test DownloadState with current progress"""
        progress = DownloadProgress(
            episode=3,
            downloaded_bytes=5000,
            total_bytes=10000
        )
        state = DownloadState(
            series_id=941,
            series_title="Test",
            total_episodes=10,
            output_dir="./out",
            selected_episodes=[1, 2, 3],
            completed_episodes=[1, 2],
            current_episode=3,
            current_progress=progress
        )
        assert state.current_episode == 3
        assert state.current_progress.downloaded_bytes == 5000

    def test_download_state_save(self, sample_state):
        """Test saving state to JSON file"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = f.name

        try:
            sample_state.save(temp_path)

            with open(temp_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            assert data['series_id'] == 941
            assert data['series_title'] == "Test Series"
            assert data['completed_episodes'] == [1, 2]
        finally:
            os.unlink(temp_path)

    def test_download_state_load(self, sample_state):
        """Test loading state from JSON file"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = f.name

        try:
            sample_state.save(temp_path)
            loaded = DownloadState.load(temp_path)

            assert loaded is not None
            assert loaded.series_id == sample_state.series_id
            assert loaded.series_title == sample_state.series_title
            assert loaded.completed_episodes == sample_state.completed_episodes
        finally:
            os.unlink(temp_path)

    def test_download_state_load_with_progress(self):
        """Test loading state with current_progress"""
        state_data = {
            "series_id": 941,
            "series_title": "Test",
            "total_episodes": 10,
            "output_dir": "./out",
            "selected_episodes": [1, 2, 3],
            "completed_episodes": [1],
            "current_episode": 2,
            "current_progress": {
                "episode": 2,
                "downloaded_bytes": 5000,
                "total_bytes": 10000,
                "completed": False
            }
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(state_data, f)
            temp_path = f.name

        try:
            loaded = DownloadState.load(temp_path)

            assert loaded is not None
            assert loaded.current_episode == 2
            assert loaded.current_progress is not None
            assert loaded.current_progress.downloaded_bytes == 5000
        finally:
            os.unlink(temp_path)

    def test_download_state_load_file_not_found(self):
        """Test loading from non-existent file returns None"""
        loaded = DownloadState.load("/nonexistent/path/file.json")
        assert loaded is None

    def test_download_state_load_invalid_json(self):
        """Test loading invalid JSON returns None"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("not valid json {{{")
            temp_path = f.name

        try:
            loaded = DownloadState.load(temp_path)
            assert loaded is None
        finally:
            os.unlink(temp_path)


class TestVideoDownloaderInit:
    """Tests for VideoDownloader initialization"""

    def test_downloader_creates_output_dir(self):
        """Test downloader creates output directory"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = os.path.join(tmpdir, "new_output")
            downloader = VideoDownloader(output_dir)

            assert os.path.exists(output_dir)
            assert downloader.output_dir == Path(output_dir)

    def test_downloader_default_state(self):
        """Test downloader starts with no state"""
        with tempfile.TemporaryDirectory() as tmpdir:
            downloader = VideoDownloader(tmpdir)

            assert downloader.state is None
            assert downloader._paused is False
            assert downloader._cancelled is False

    def test_downloader_has_session(self):
        """Test downloader has requests session"""
        with tempfile.TemporaryDirectory() as tmpdir:
            downloader = VideoDownloader(tmpdir)

            assert downloader.session is not None
            assert 'User-Agent' in downloader.session.headers

    def test_downloader_chunk_size(self):
        """Test downloader has correct chunk size"""
        assert VideoDownloader.CHUNK_SIZE == 1024 * 1024  # 1MB


class TestVideoDownloaderControls:
    """Tests for pause/resume/cancel controls"""

    @pytest.fixture
    def downloader(self):
        """Create downloader in temp directory"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield VideoDownloader(tmpdir)

    def test_pause(self, downloader):
        """Test pause sets flag"""
        downloader.pause()
        assert downloader.is_paused() is True

    def test_resume(self, downloader):
        """Test resume clears pause flag"""
        downloader.pause()
        downloader.resume()
        assert downloader.is_paused() is False

    def test_cancel(self, downloader):
        """Test cancel sets flag"""
        downloader.cancel()
        assert downloader.is_cancelled() is True

    def test_reset(self, downloader):
        """Test reset clears all flags"""
        downloader.pause()
        downloader.cancel()
        downloader.reset()

        assert downloader.is_paused() is False
        assert downloader.is_cancelled() is False


class TestVideoDownloaderState:
    """Tests for state management"""

    @pytest.fixture
    def downloader(self):
        """Create downloader in temp directory"""
        tmpdir = tempfile.mkdtemp()
        d = VideoDownloader(tmpdir)
        yield d
        # Cleanup
        import shutil
        shutil.rmtree(tmpdir, ignore_errors=True)

    @pytest.fixture
    def sample_series(self):
        """Create sample series info"""
        return SeriesInfo(
            series_id=941,
            title="Test Series",
            total_episodes=30
        )

    def test_init_state(self, downloader, sample_series):
        """Test initializing download state"""
        downloader.init_state(sample_series, [1, 2, 3, 4, 5])

        assert downloader.state is not None
        assert downloader.state.series_id == 941
        assert downloader.state.selected_episodes == [1, 2, 3, 4, 5]
        assert downloader.state.completed_episodes == []

    def test_init_state_sorts_episodes(self, downloader, sample_series):
        """Test init_state sorts episode list"""
        downloader.init_state(sample_series, [5, 1, 3, 2, 4])

        assert downloader.state.selected_episodes == [1, 2, 3, 4, 5]

    def test_init_state_saves_file(self, downloader, sample_series):
        """Test init_state saves state file"""
        downloader.init_state(sample_series, [1, 2])

        assert downloader.state_file.exists()

    def test_load_state(self, downloader, sample_series):
        """Test loading saved state"""
        downloader.init_state(sample_series, [1, 2, 3])
        downloader.state.completed_episodes = [1]
        downloader._save_state()

        # Create new downloader
        downloader2 = VideoDownloader(str(downloader.output_dir))
        loaded = downloader2.load_state()

        assert loaded is not None
        assert loaded.completed_episodes == [1]

    def test_clear_state(self, downloader, sample_series):
        """Test clearing state"""
        downloader.init_state(sample_series, [1, 2])
        assert downloader.state_file.exists()

        downloader.clear_state()

        assert not downloader.state_file.exists()
        assert downloader.state is None

    def test_get_remaining_episodes(self, downloader, sample_series):
        """Test getting remaining episodes"""
        downloader.init_state(sample_series, [1, 2, 3, 4, 5])
        downloader.state.completed_episodes = [1, 2, 3]

        remaining = downloader.get_remaining_episodes()

        assert remaining == [4, 5]

    def test_get_remaining_episodes_no_state(self, downloader):
        """Test get_remaining_episodes with no state"""
        remaining = downloader.get_remaining_episodes()
        assert remaining == []


class TestVideoDownloaderFilenames:
    """Tests for filename generation"""

    @pytest.fixture
    def downloader(self):
        """Create downloader in temp directory"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield VideoDownloader(tmpdir)

    def test_get_episode_filename(self, downloader):
        """Test episode filename generation"""
        filename = downloader.get_episode_filename(1)
        assert filename.name == "ep_01.mp4"

    def test_get_episode_filename_double_digit(self, downloader):
        """Test double-digit episode filename"""
        filename = downloader.get_episode_filename(15)
        assert filename.name == "ep_15.mp4"

    def test_get_episode_filename_high_number(self, downloader):
        """Test high episode number filename"""
        filename = downloader.get_episode_filename(100)
        assert filename.name == "ep_100.mp4"


class TestDownloadEpisode:
    """Tests for download_episode method with mocked requests"""

    @pytest.fixture
    def downloader(self):
        """Create downloader in temp directory"""
        tmpdir = tempfile.mkdtemp()
        d = VideoDownloader(tmpdir)
        yield d
        import shutil
        shutil.rmtree(tmpdir, ignore_errors=True)

    @pytest.fixture
    def episode_info(self):
        """Create sample episode info"""
        return EpisodeInfo(
            episode_number=1,
            title="ตอนที่ 1",
            video_url="http://example.com/video.mp4"
        )

    @patch('requests.Session.get')
    def test_download_episode_success(self, mock_get, downloader, episode_info):
        """Test successful episode download"""
        # Mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {'Content-Length': '1000'}
        mock_response.iter_content = Mock(return_value=[b'x' * 1000])
        mock_get.return_value = mock_response

        success = downloader.download_episode(episode_info, use_tqdm=False)

        assert success is True
        assert downloader.get_episode_filename(1).exists()

    @patch('requests.Session.get')
    def test_download_episode_resume_partial(self, mock_get, downloader, episode_info):
        """Test resuming partial download"""
        # Create partial file
        temp_file = downloader.get_episode_filename(1).with_suffix('.mp4.part')
        with open(temp_file, 'wb') as f:
            f.write(b'x' * 500)

        # Mock 206 Partial Content response
        mock_response = Mock()
        mock_response.status_code = 206
        mock_response.headers = {'Content-Range': 'bytes 500-999/1000'}
        mock_response.iter_content = Mock(return_value=[b'y' * 500])
        mock_get.return_value = mock_response

        success = downloader.download_episode(episode_info, use_tqdm=False)

        assert success is True
        # Check Range header was sent
        call_args = mock_get.call_args
        assert 'Range' in call_args.kwargs.get('headers', {})

    @patch('requests.Session.get')
    def test_download_episode_http_error(self, mock_get, downloader, episode_info):
        """Test handling HTTP errors"""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        success = downloader.download_episode(episode_info, use_tqdm=False)

        assert success is False

    @patch('requests.Session.get')
    def test_download_episode_network_error(self, mock_get, downloader, episode_info):
        """Test handling network errors"""
        import requests
        mock_get.side_effect = requests.RequestException("Connection failed")

        success = downloader.download_episode(episode_info, use_tqdm=False)

        assert success is False

    @patch('requests.Session.get')
    def test_download_episode_cancelled(self, mock_get, downloader, episode_info):
        """Test download cancellation"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {'Content-Length': '10000'}

        # Simulate chunks and cancel mid-download
        def iter_chunks(*args, **kwargs):
            yield b'x' * 1000
            downloader.cancel()
            yield b'x' * 1000

        mock_response.iter_content = iter_chunks
        mock_get.return_value = mock_response

        success = downloader.download_episode(episode_info, use_tqdm=False)

        assert success is False
        assert downloader.is_cancelled() is True

    @patch('requests.Session.get')
    def test_download_episode_with_callback(self, mock_get, downloader, episode_info):
        """Test progress callback is called"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {'Content-Length': '1000'}
        mock_response.iter_content = Mock(return_value=[b'x' * 500, b'x' * 500])
        mock_get.return_value = mock_response

        callback = Mock()
        success = downloader.download_episode(
            episode_info,
            progress_callback=callback,
            use_tqdm=False
        )

        assert success is True
        assert callback.called

    @patch('requests.Session.get')
    def test_download_episode_updates_state(self, mock_get, downloader, episode_info):
        """Test download updates completion state"""
        # Initialize state
        series = SeriesInfo(series_id=941, title="Test", total_episodes=10)
        downloader.init_state(series, [1, 2, 3])

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {'Content-Length': '1000'}
        mock_response.iter_content = Mock(return_value=[b'x' * 1000])
        mock_get.return_value = mock_response

        success = downloader.download_episode(episode_info, use_tqdm=False)

        assert success is True
        assert 1 in downloader.state.completed_episodes


class TestDownloadAll:
    """Tests for download_all method"""

    @pytest.fixture
    def downloader(self):
        """Create downloader in temp directory"""
        tmpdir = tempfile.mkdtemp()
        d = VideoDownloader(tmpdir)
        yield d
        import shutil
        shutil.rmtree(tmpdir, ignore_errors=True)

    @pytest.fixture
    def episodes(self):
        """Create sample episode list"""
        return [
            EpisodeInfo(episode_number=1, title="Ep 1", video_url="http://example.com/1.mp4"),
            EpisodeInfo(episode_number=2, title="Ep 2", video_url="http://example.com/2.mp4"),
            EpisodeInfo(episode_number=3, title="Ep 3", video_url="http://example.com/3.mp4"),
        ]

    @patch.object(VideoDownloader, 'download_episode')
    def test_download_all_success(self, mock_download, downloader, episodes):
        """Test downloading all episodes successfully"""
        mock_download.return_value = True

        successful, failed = downloader.download_all(episodes)

        assert successful == 3
        assert failed == 0
        assert mock_download.call_count == 3

    @patch.object(VideoDownloader, 'download_episode')
    def test_download_all_with_failures(self, mock_download, downloader, episodes):
        """Test downloading with some failures"""
        mock_download.side_effect = [True, False, True]

        successful, failed = downloader.download_all(episodes)

        assert successful == 2
        assert failed == 1

    @patch.object(VideoDownloader, 'download_episode')
    def test_download_all_skips_completed(self, mock_download, downloader, episodes):
        """Test skipping already completed episodes"""
        # Initialize state with episode 1 completed
        series = SeriesInfo(series_id=941, title="Test", total_episodes=10)
        downloader.init_state(series, [1, 2, 3])
        downloader.state.completed_episodes = [1]

        mock_download.return_value = True

        successful, failed = downloader.download_all(episodes)

        # Episode 1 counted as success but not downloaded
        assert successful == 3
        assert failed == 0
        assert mock_download.call_count == 2  # Only 2 and 3 downloaded

    @patch.object(VideoDownloader, 'download_episode')
    def test_download_all_cancelled(self, mock_download, downloader, episodes):
        """Test cancellation during download_all"""
        def side_effect(ep, **kwargs):
            if ep.episode_number == 2:
                downloader.cancel()
                return False
            return True

        mock_download.side_effect = side_effect

        successful, failed = downloader.download_all(episodes)

        # Should stop after cancellation
        assert successful == 1
        assert mock_download.call_count == 2

    @patch.object(VideoDownloader, 'download_episode')
    def test_download_all_with_callback(self, mock_download, downloader, episodes):
        """Test progress callback in download_all"""
        mock_download.return_value = True
        callback = Mock()

        downloader.download_all(episodes, progress_callback=callback)

        assert callback.call_count == 3


class TestEdgeCases:
    """Tests for edge cases and error handling"""

    def test_empty_episodes_list(self):
        """Test downloading empty episode list"""
        with tempfile.TemporaryDirectory() as tmpdir:
            downloader = VideoDownloader(tmpdir)
            successful, failed = downloader.download_all([])
            assert successful == 0
            assert failed == 0

    def test_large_episode_number(self):
        """Test handling large episode numbers"""
        with tempfile.TemporaryDirectory() as tmpdir:
            downloader = VideoDownloader(tmpdir)
            filename = downloader.get_episode_filename(9999)
            assert "9999" in str(filename)

    def test_unicode_in_series_title(self):
        """Test handling Thai characters in series title"""
        with tempfile.TemporaryDirectory() as tmpdir:
            downloader = VideoDownloader(tmpdir)
            series = SeriesInfo(
                series_id=941,
                title="ซีรีส์ภาษาไทย",
                total_episodes=10
            )
            downloader.init_state(series, [1])

            assert downloader.state.series_title == "ซีรีส์ภาษาไทย"

            # Verify it saves and loads correctly
            loaded = downloader.load_state()
            assert loaded.series_title == "ซีรีส์ภาษาไทย"


# Run tests if executed directly
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
