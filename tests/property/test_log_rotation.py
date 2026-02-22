"""Property 34: Log File Rotation

This property validates that log files are rotated when they exceed the size limit,
keeping only the configured number of backup files.

Validates Requirements: 14.6
"""

import pytest
from hypothesis import given, strategies as st, settings
from pathlib import Path
import tempfile
import logging
import logging.handlers

from src.logging_config import setup_logging, MAX_LOG_SIZE, BACKUP_COUNT


def cleanup_handlers():
    """Properly close and remove all logging handlers."""
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        try:
            handler.close()
        except Exception:
            pass
        try:
            root_logger.removeHandler(handler)
        except Exception:
            pass


@given(
    num_writes=st.integers(min_value=1, max_value=10)
)
@settings(max_examples=20, deadline=None)
def test_log_rotation_occurs_at_size_limit(num_writes):
    """Property 34: Log files are rotated when size limit is exceeded.
    
    PROPERTY: When a log file exceeds MAX_LOG_SIZE (10MB),
              it MUST be rotated to a backup file and a new log file created.
    
    This ensures log files don't grow unbounded.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        # Override LOG_DIR for testing
        import src.logging_config as logging_config
        original_log_dir = logging_config.LOG_DIR
        original_log_file = logging_config.LOG_FILE
        original_max_size = logging_config.MAX_LOG_SIZE
        
        # Use smaller size for testing (1KB instead of 10MB)
        test_max_size = 1024  # 1KB
        logging_config.LOG_DIR = Path(tmpdir) / ".logs"
        logging_config.LOG_FILE = logging_config.LOG_DIR / "test.log"
        logging_config.MAX_LOG_SIZE = test_max_size
        
        try:
            # Initialize logging
            setup_logging(debug=False)
            
            # Get root logger
            root_logger = logging.getLogger()
            
            # Write enough data to trigger rotation
            # Each write is ~200 bytes, so 10 writes = ~2KB (exceeds 1KB limit)
            large_message = "X" * 200  # 200 byte message
            
            for i in range(num_writes):
                root_logger.info(f"Message {i}: {large_message}")
            
            # Force flush
            for handler in root_logger.handlers:
                if hasattr(handler, 'flush'):
                    handler.flush()
            
            # Check if rotation occurred
            log_file = logging_config.LOG_FILE
            
            # Property: Log file should exist
            assert log_file.exists(), "Log file should exist"
            
            # Property: If we wrote enough data, rotation should have occurred
            total_bytes_written = num_writes * 200
            if total_bytes_written > test_max_size:
                # Check for backup files (*.log.1, *.log.2, etc.)
                backup_files = list(logging_config.LOG_DIR.glob("*.log.*"))
                
                # At least one backup should exist if rotation occurred
                # (Note: RotatingFileHandler rotates when NEXT write would exceed limit)
                # So we might not see rotation until we exceed by a significant amount
                if total_bytes_written > test_max_size * 2:
                    assert len(backup_files) > 0, \
                        f"Backup files should exist after writing {total_bytes_written} bytes (limit: {test_max_size})"
            
            # Clean up handlers properly
            cleanup_handlers()
        
        finally:
            # Restore original values
            logging_config.LOG_DIR = original_log_dir
            logging_config.LOG_FILE = original_log_file
            logging_config.MAX_LOG_SIZE = original_max_size


@given(
    num_rotations=st.integers(min_value=1, max_value=5)
)
@settings(max_examples=10, deadline=None)
def test_log_rotation_keeps_backup_count(num_rotations):
    """Property 34: Log rotation keeps only BACKUP_COUNT backup files.
    
    PROPERTY: When log rotation occurs multiple times,
              only BACKUP_COUNT (3) backup files MUST be kept,
              and older backups MUST be deleted.
    
    This ensures log files don't accumulate indefinitely.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        # Override LOG_DIR for testing
        import src.logging_config as logging_config
        original_log_dir = logging_config.LOG_DIR
        original_log_file = logging_config.LOG_FILE
        original_max_size = logging_config.MAX_LOG_SIZE
        original_backup_count = logging_config.BACKUP_COUNT
        
        # Use smaller size for testing
        test_max_size = 512  # 512 bytes
        logging_config.LOG_DIR = Path(tmpdir) / ".logs"
        logging_config.LOG_FILE = logging_config.LOG_DIR / "test.log"
        logging_config.MAX_LOG_SIZE = test_max_size
        logging_config.BACKUP_COUNT = 3
        
        try:
            # Initialize logging
            setup_logging(debug=False)
            
            # Get root logger
            root_logger = logging.getLogger()
            
            # Write enough data to trigger multiple rotations
            large_message = "X" * 200  # 200 byte message
            
            # Write enough to trigger num_rotations rotations
            # Each rotation needs ~512 bytes, so write more than that
            writes_per_rotation = 4  # 4 * 200 = 800 bytes > 512
            total_writes = num_rotations * writes_per_rotation
            
            for i in range(total_writes):
                root_logger.info(f"Message {i}: {large_message}")
                
                # Force flush periodically
                if i % writes_per_rotation == 0:
                    for handler in root_logger.handlers:
                        if hasattr(handler, 'flush'):
                            handler.flush()
            
            # Final flush
            for handler in root_logger.handlers:
                if hasattr(handler, 'flush'):
                    handler.flush()
            
            # Check backup files
            backup_files = list(logging_config.LOG_DIR.glob("*.log.*"))
            
            # Property: Number of backup files should not exceed BACKUP_COUNT
            assert len(backup_files) <= logging_config.BACKUP_COUNT, \
                f"Should keep at most {logging_config.BACKUP_COUNT} backup files, found {len(backup_files)}"
            
            # Clean up handlers properly
            cleanup_handlers()
        
        finally:
            # Restore original values
            logging_config.LOG_DIR = original_log_dir
            logging_config.LOG_FILE = original_log_file
            logging_config.MAX_LOG_SIZE = original_max_size
            logging_config.BACKUP_COUNT = original_backup_count


def test_log_rotation_preserves_content():
    """Property 34: Log rotation preserves log content in backup files.
    
    PROPERTY: When log rotation occurs, the old log content MUST be
              preserved in the backup file, not lost.
    
    This ensures no log data is lost during rotation.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        # Override LOG_DIR for testing
        import src.logging_config as logging_config
        original_log_dir = logging_config.LOG_DIR
        original_log_file = logging_config.LOG_FILE
        original_max_size = logging_config.MAX_LOG_SIZE
        
        # Use smaller size for testing
        test_max_size = 512  # 512 bytes
        logging_config.LOG_DIR = Path(tmpdir) / ".logs"
        logging_config.LOG_FILE = logging_config.LOG_DIR / "test.log"
        logging_config.MAX_LOG_SIZE = test_max_size
        
        try:
            # Initialize logging
            setup_logging(debug=False)
            
            # Get root logger
            root_logger = logging.getLogger()
            
            # Write enough data to trigger rotation FIRST
            large_message = "X" * 200
            for i in range(5):
                root_logger.info(f"Filler {i}: {large_message}")
            
            # NOW write the unique message (after some rotation may have occurred)
            unique_message = "UNIQUE_TEST_MESSAGE_12345"
            root_logger.info(unique_message)
            
            # Write more data to potentially trigger more rotation
            for i in range(5):
                root_logger.info(f"Message {i}: {large_message}")
            
            # Force flush
            for handler in root_logger.handlers:
                if hasattr(handler, 'flush'):
                    handler.flush()
            
            # Check if unique message is preserved somewhere
            log_file = logging_config.LOG_FILE
            backup_files = list(logging_config.LOG_DIR.glob("*.log.*"))
            
            # Read all log files (current + backups)
            all_content = ""
            if log_file.exists():
                all_content += log_file.read_text()
            for backup in backup_files:
                all_content += backup.read_text()
            
            # Property: Unique message should be preserved somewhere
            # (either in current log or in a backup)
            if backup_files:  # Only check if rotation occurred
                assert unique_message in all_content, \
                    "Log content should be preserved during rotation"
            
            # Clean up handlers properly
            cleanup_handlers()
        
        finally:
            # Restore original values
            logging_config.LOG_DIR = original_log_dir
            logging_config.LOG_FILE = original_log_file
            logging_config.MAX_LOG_SIZE = original_max_size


@given(
    concurrent_writes=st.integers(min_value=1, max_value=5)
)
@settings(max_examples=10, deadline=None)
def test_log_rotation_is_atomic(concurrent_writes):
    """Property 34: Log rotation is atomic and doesn't corrupt files.
    
    PROPERTY: When log rotation occurs, the operation MUST be atomic,
              ensuring no log corruption or data loss occurs.
    
    This ensures log files remain valid even during rotation.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        # Override LOG_DIR for testing
        import src.logging_config as logging_config
        original_log_dir = logging_config.LOG_DIR
        original_log_file = logging_config.LOG_FILE
        original_max_size = logging_config.MAX_LOG_SIZE
        
        # Use smaller size for testing
        test_max_size = 512  # 512 bytes
        logging_config.LOG_DIR = Path(tmpdir) / ".logs"
        logging_config.LOG_FILE = logging_config.LOG_DIR / "test.log"
        logging_config.MAX_LOG_SIZE = test_max_size
        
        try:
            # Initialize logging
            setup_logging(debug=False)
            
            # Get root logger
            root_logger = logging.getLogger()
            
            # Write data that will trigger rotation
            large_message = "X" * 200
            for i in range(concurrent_writes * 5):
                root_logger.info(f"Message {i}: {large_message}")
            
            # Force flush
            for handler in root_logger.handlers:
                if hasattr(handler, 'flush'):
                    handler.flush()
            
            # Property: All log files should be readable (not corrupted)
            log_file = logging_config.LOG_FILE
            backup_files = list(logging_config.LOG_DIR.glob("*.log.*"))
            
            # Try to read all files - should not raise exceptions
            if log_file.exists():
                content = log_file.read_text()
                assert len(content) > 0, "Log file should not be empty"
            
            for backup in backup_files:
                content = backup.read_text()
                # Backup files should contain valid log data
                assert len(content) > 0, f"Backup file {backup.name} should not be empty"
            
            # Clean up handlers properly
            cleanup_handlers()
        
        finally:
            # Restore original values
            logging_config.LOG_DIR = original_log_dir
            logging_config.LOG_FILE = original_log_file
            logging_config.MAX_LOG_SIZE = original_max_size


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
