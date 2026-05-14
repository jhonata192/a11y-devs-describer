import tempfile
import time
from pathlib import Path

from config.settings import settings


class TestSettings:
    def test_default_values(self):
        assert settings.max_file_size_mb == 50
        assert settings.max_pages == 50
        assert settings.log_level == "INFO"
        assert settings.ollama_url == "http://localhost:11434"
        assert settings.vision_model == "llava:7b"
        assert settings.ollama_timeout == 3600
        assert settings.translation_model == "qwen2.5:1.5b"

    def test_bot_token_valid(self):
        assert isinstance(settings.bot_token_valid, bool)

    def test_max_file_size_bytes(self):
        assert settings.max_file_size_bytes == 50 * 1024 * 1024

    def test_allowed_extensions(self):
        assert ".pdf" in settings.allowed_extensions
        assert ".png" in settings.allowed_extensions
        assert ".jpg" in settings.allowed_extensions
        assert ".exe" not in settings.allowed_extensions


class TestCleanupService:
    def test_clean_nonexistent_dir(self):
        from bot.services.cleanup_service import _clean_temp_directory
        saved = settings.temp_dir
        settings.temp_dir = Path(tempfile.mktemp())
        try:
            _clean_temp_directory()
        finally:
            settings.temp_dir = saved

    def test_clean_old_file(self):
        from bot.services.cleanup_service import _clean_temp_directory
        saved = settings.temp_dir
        with tempfile.TemporaryDirectory() as tmpdir:
            settings.temp_dir = Path(tmpdir)
            old_file = Path(tmpdir) / "old.txt"
            old_file.write_text("old")
            old_mtime = time.time() - 7200
            os = __import__("os")
            os.utime(str(old_file), (old_mtime, old_mtime))
            _clean_temp_directory()
            assert not old_file.exists()
        settings.temp_dir = saved

    def test_keep_recent_file(self):
        from bot.services.cleanup_service import _clean_temp_directory
        saved = settings.temp_dir
        with tempfile.TemporaryDirectory() as tmpdir:
            settings.temp_dir = Path(tmpdir)
            recent = Path(tmpdir) / "recent.txt"
            recent.write_text("recent")
            _clean_temp_directory()
            assert recent.exists()
        settings.temp_dir = saved

    def test_keep_output_dir(self):
        from bot.services.cleanup_service import _clean_temp_directory
        saved = settings.temp_dir
        with tempfile.TemporaryDirectory() as tmpdir:
            settings.temp_dir = Path(tmpdir)
            output_dir = Path(tmpdir) / "output"
            output_dir.mkdir()
            (output_dir / "result.txt").write_text("result")
            _clean_temp_directory()
            assert output_dir.exists()
            assert (output_dir / "result.txt").exists()
        settings.temp_dir = saved
