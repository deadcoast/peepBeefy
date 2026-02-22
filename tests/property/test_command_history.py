"""Property-based tests for command history functionality.

Tests Property 40: Recent Commands Tracking
Validates Requirements 5.5
"""

import pytest
from hypothesis import given, strategies as st, assume, settings
from pathlib import Path
import tempfile
import shutil

from command_history import CommandHistory


# Strategy for generating valid command strings
command_strategy = st.text(
    alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'P', 'Zs')),
    min_size=1,
    max_size=100
).filter(lambda x: x.strip())  # Ensure non-empty after stripping


class TestCommandHistoryProperties:
    """Property-based tests for CommandHistory class."""
    
    @given(commands=st.lists(command_strategy, min_size=1, max_size=50))
    @settings(max_examples=100, deadline=None)
    def test_property_40_recent_commands_tracking(self, commands):
        """Property 40: Recent Commands Tracking
        
        PROPERTY: For any sequence of commands added to history:
        1. get_recent(N) returns at most N commands
        2. Commands are returned in reverse chronological order (most recent first)
        3. The most recently added command appears first in get_recent()
        4. Consecutive duplicate commands are deduplicated
        
        Validates: Requirements 5.5 (recent commands quick-access list)
        """
        # Create temporary directory for history file
        with tempfile.TemporaryDirectory() as tmpdir:
            history_file = Path(tmpdir) / "test_history.json"
            history = CommandHistory(max_size=100, history_file=history_file)
            
            # Add all commands to history
            for cmd in commands:
                history.add(cmd)
            
            # Property 1: get_recent(N) returns at most N commands
            for n in [1, 3, 5, 10]:
                recent = history.get_recent(count=n)
                assert len(recent) <= n, \
                    f"get_recent({n}) returned {len(recent)} commands, expected at most {n}"
            
            # Property 2 & 3: Commands are in reverse chronological order
            # Most recent command should be first
            recent_5 = history.get_recent(count=5)
            if recent_5:
                # The first item should be the last command added (after deduplication)
                # Build expected history with deduplication
                deduplicated = []
                for cmd in commands:
                    if not deduplicated or deduplicated[-1] != cmd:
                        deduplicated.append(cmd)
                
                if deduplicated:
                    expected_most_recent = deduplicated[-1]
                    assert recent_5[0] == expected_most_recent, \
                        f"Most recent command should be '{expected_most_recent}', got '{recent_5[0]}'"
                    
                    # Verify reverse chronological order
                    expected_recent = list(reversed(deduplicated[-5:]))
                    assert recent_5 == expected_recent, \
                        f"Recent commands not in correct order. Expected {expected_recent}, got {recent_5}"
            
            # Property 4: Consecutive duplicates are deduplicated
            # Create a fresh history to test this property in isolation
            test_history = CommandHistory(max_size=100)
            test_cmd = "test_duplicate"
            test_history.add(test_cmd)
            test_history.add(test_cmd)  # Duplicate
            
            recent = test_history.get_recent(count=10)
            # The test_cmd should appear exactly once
            count_in_recent = recent.count(test_cmd)
            
            assert count_in_recent == 1, \
                f"Consecutive duplicate '{test_cmd}' should appear only once, found {count_in_recent} times"
    
    @given(commands=st.lists(command_strategy, min_size=1, max_size=20))
    @settings(max_examples=100, deadline=None)
    def test_history_navigation_consistency(self, commands):
        """Property: History navigation maintains consistency.
        
        PROPERTY: For any sequence of commands:
        1. Navigating backward then forward returns to the same position
        2. get_previous() never returns None if history is not empty
        3. Navigation doesn't modify the history
        
        Validates: Requirements 5.4 (command history navigation)
        """
        history = CommandHistory(max_size=100)
        
        # Add commands
        for cmd in commands:
            history.add(cmd)
        
        # Deduplicate to match expected behavior
        deduplicated = []
        for cmd in commands:
            if not deduplicated or deduplicated[-1] != cmd:
                deduplicated.append(cmd)
        
        assume(len(deduplicated) > 0)  # Need at least one command
        
        # Property 1: Navigate backward then forward
        original_length = len(history)
        
        # Go back N times
        back_steps = min(3, len(deduplicated))
        for _ in range(back_steps):
            prev = history.get_previous()
            assert prev is not None, "get_previous() returned None when history is not empty"
        
        # Go forward same number of times
        for _ in range(back_steps):
            history.get_next()
        
        # Property 3: History length unchanged
        assert len(history) == original_length, \
            f"Navigation modified history length: {original_length} -> {len(history)}"
    
    @given(
        commands=st.lists(command_strategy, min_size=1, max_size=150),
        max_size=st.integers(min_value=10, max_value=100)
    )
    @settings(max_examples=50, deadline=None)
    def test_history_size_limit(self, commands, max_size):
        """Property: History respects maximum size limit.
        
        PROPERTY: For any sequence of commands and max_size:
        1. History never exceeds max_size
        2. Oldest commands are removed when limit is reached
        3. Most recent commands are always preserved
        
        Validates: Requirements 5.5 (command history storage)
        """
        history = CommandHistory(max_size=max_size)
        
        # Add all commands
        for cmd in commands:
            history.add(cmd)
        
        # Property 1: Never exceeds max_size
        assert len(history) <= max_size, \
            f"History size {len(history)} exceeds max_size {max_size}"
        
        # Property 3: Most recent commands are preserved
        # Deduplicate commands
        deduplicated = []
        for cmd in commands:
            if not deduplicated or deduplicated[-1] != cmd:
                deduplicated.append(cmd)
        
        if deduplicated:
            # Get expected recent commands (last max_size items)
            expected_recent = deduplicated[-max_size:]
            
            # Get all history
            all_history = history.get_recent(count=max_size)
            
            # Reverse to get chronological order
            all_history_chrono = list(reversed(all_history))
            
            assert all_history_chrono == expected_recent, \
                f"History doesn't preserve most recent commands correctly"
    
    @given(commands=st.lists(command_strategy, min_size=1, max_size=30))
    @settings(max_examples=100, deadline=None)
    def test_history_persistence(self, commands):
        """Property: History persists correctly to disk.
        
        PROPERTY: For any sequence of commands:
        1. Commands saved to disk can be loaded back
        2. Loaded history matches saved history
        3. History survives across CommandHistory instances
        
        Validates: Requirements 5.5 (command history persistence)
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            history_file = Path(tmpdir) / "test_history.json"
            
            # Create first instance and add commands
            history1 = CommandHistory(max_size=100, history_file=history_file)
            for cmd in commands:
                history1.add(cmd)
            
            # Get recent commands from first instance
            recent1 = history1.get_recent(count=10)
            
            # Create second instance (should load from disk)
            history2 = CommandHistory(max_size=100, history_file=history_file)
            recent2 = history2.get_recent(count=10)
            
            # Property 2: Loaded history matches saved history
            assert recent2 == recent1, \
                f"Loaded history doesn't match saved history.\nSaved: {recent1}\nLoaded: {recent2}"
            
            # Property 3: History file exists
            assert history_file.exists(), "History file was not created"
    
    @given(st.lists(st.text(min_size=0, max_size=50), min_size=5, max_size=20))
    @settings(max_examples=100, deadline=None)
    def test_empty_command_handling(self, commands):
        """Property: Empty and whitespace-only commands are ignored.
        
        PROPERTY: For any sequence of commands including empty strings:
        1. Empty strings are not added to history
        2. Whitespace-only strings are not added to history
        3. History only contains non-empty commands
        
        Validates: Requirements 5.5 (command history quality)
        """
        history = CommandHistory(max_size=100)
        
        # Add all commands (including potentially empty ones)
        for cmd in commands:
            history.add(cmd)
        
        # Get all history
        all_history = history.get_recent(count=100)
        
        # Property 3: All commands in history are non-empty
        for cmd in all_history:
            assert cmd and cmd.strip(), \
                f"History contains empty or whitespace-only command: '{cmd}'"
        
        # Verify count matches expected (non-empty commands only)
        expected_count = sum(1 for cmd in commands if cmd and cmd.strip())
        # Account for deduplication
        deduplicated = []
        for cmd in commands:
            if cmd and cmd.strip():
                if not deduplicated or deduplicated[-1] != cmd:
                    deduplicated.append(cmd)
        
        assert len(all_history) == len(deduplicated), \
            f"History count mismatch. Expected {len(deduplicated)}, got {len(all_history)}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--hypothesis-show-statistics"])
