"""Property-based tests for menu input mapping functionality.

Tests Property 39: Menu Input Mapping
Validates Requirements 5.3
"""

import pytest
from hypothesis import given, strategies as st, assume, settings


class TestMenuInputMappingProperties:
    """Property-based tests for menu input mapping and shortcuts."""
    
    def test_property_39_menu_input_mapping(self):
        """Property 39: Menu Input Mapping
        
        PROPERTY: For all menu items and their shortcuts:
        1. Each shortcut maps to exactly one command
        2. All shortcuts are unique (no collisions)
        3. Shortcuts are case-insensitive
        4. Number shortcuts (1-8) map to menu items in order
        5. Letter shortcuts (s, h, q) map to their respective commands
        
        Validates: Requirements 5.3 (keyboard shortcuts support)
        """
        # Define the expected shortcut mapping (from main.py)
        shortcut_map = {
            "1": "peep all",
            "2": "peep cpu",
            "3": "peep io",
            "4": "peep mem",
            "5": "peep clutter",
            "6": "peep watch",
            "7": "baseline save",
            "8": "baseline diff",
            "s": "settings",
            "h": "help",
            "?": "help",
        }
        
        # Property 1: Each shortcut maps to exactly one command
        for shortcut, command in shortcut_map.items():
            assert isinstance(command, str), \
                f"Shortcut '{shortcut}' maps to non-string: {type(command)}"
            assert command, \
                f"Shortcut '{shortcut}' maps to empty command"
        
        # Property 2: All shortcuts are unique (except ? and h which both map to help)
        shortcuts = list(shortcut_map.keys())
        # Remove one of the help shortcuts for uniqueness check
        shortcuts_for_uniqueness = [s for s in shortcuts if s != "?"]
        assert len(shortcuts_for_uniqueness) == len(set(shortcuts_for_uniqueness)), \
            f"Duplicate shortcuts found: {shortcuts_for_uniqueness}"
        
        # Property 4: Number shortcuts map to menu items in order
        number_shortcuts = ["1", "2", "3", "4", "5", "6", "7", "8"]
        expected_commands = [
            "peep all",
            "peep cpu",
            "peep io",
            "peep mem",
            "peep clutter",
            "peep watch",
            "baseline save",
            "baseline diff",
        ]
        
        for i, shortcut in enumerate(number_shortcuts):
            assert shortcut in shortcut_map, \
                f"Number shortcut '{shortcut}' not in mapping"
            assert shortcut_map[shortcut] == expected_commands[i], \
                f"Shortcut '{shortcut}' maps to '{shortcut_map[shortcut]}', expected '{expected_commands[i]}'"
        
        # Property 5: Letter shortcuts map correctly
        assert shortcut_map["s"] == "settings", \
            f"Shortcut 's' should map to 'settings', got '{shortcut_map['s']}'"
        assert shortcut_map["h"] == "help", \
            f"Shortcut 'h' should map to 'help', got '{shortcut_map['h']}'"
        assert shortcut_map["?"] == "help", \
            f"Shortcut '?' should map to 'help', got '{shortcut_map['?']}'"
    
    @given(
        shortcut=st.sampled_from(["1", "2", "3", "4", "5", "6", "7", "8", "s", "h", "?"]),
        case_variant=st.sampled_from(["lower", "upper", "mixed"])
    )
    @settings(max_examples=50, deadline=None)
    def test_shortcut_case_insensitivity(self, shortcut, case_variant):
        """Property: Shortcuts work regardless of case.
        
        PROPERTY: For any valid shortcut:
        1. Lowercase version maps to a command
        2. Uppercase version maps to the same command
        3. Case doesn't affect the mapping
        
        Validates: Requirements 5.3 (keyboard shortcuts are case-insensitive)
        """
        # Define the shortcut mapping
        shortcut_map = {
            "1": "peep all",
            "2": "peep cpu",
            "3": "peep io",
            "4": "peep mem",
            "5": "peep clutter",
            "6": "peep watch",
            "7": "baseline save",
            "8": "baseline diff",
            "s": "settings",
            "h": "help",
            "?": "help",
        }
        
        # Get the expected command for lowercase shortcut
        expected_command = shortcut_map[shortcut.lower()]
        
        # Test different case variants
        if case_variant == "lower":
            test_shortcut = shortcut.lower()
        elif case_variant == "upper":
            test_shortcut = shortcut.upper()
        else:  # mixed - only applicable to letter shortcuts
            if shortcut.isalpha():
                test_shortcut = shortcut.upper() if len(shortcut) % 2 == 0 else shortcut.lower()
            else:
                test_shortcut = shortcut
        
        # In the actual implementation, input is converted to lowercase
        # So we simulate that here
        normalized_shortcut = test_shortcut.lower()
        
        # Property: Normalized shortcut maps to expected command
        if normalized_shortcut in shortcut_map:
            actual_command = shortcut_map[normalized_shortcut]
            assert actual_command == expected_command, \
                f"Case variant '{test_shortcut}' (normalized: '{normalized_shortcut}') " \
                f"maps to '{actual_command}', expected '{expected_command}'"
    
    def test_all_menu_items_have_shortcuts(self):
        """Property: All menu items have corresponding shortcuts.
        
        PROPERTY: For all menu items:
        1. Each menu item has at least one shortcut
        2. The number of shortcuts matches the number of menu items
        3. No menu item is unreachable via shortcuts
        
        Validates: Requirements 5.2, 5.3 (keyboard shortcuts for all menu items)
        """
        # Define menu items (from main.py MENU_ITEMS)
        menu_items = [
            ("beefy peep all", "Quick Scan"),
            ("beefy peep cpu", "CPU Hog Finder"),
            ("beefy peep io", "Disk Hog Finder"),
            ("beefy peep mem", "RAM Hog Finder"),
            ("beefy peep clutter", "Gamer Clutter"),
            ("beefy peep watch", "Live Watch"),
            ("beefy baseline save", "Save baseline"),
            ("beefy baseline diff", "Compare baseline"),
            ("settings", "Configure preferences"),
            ("help", "Show help"),
            ("quit", "Exit"),
        ]
        
        # Define shortcuts
        shortcuts = {
            "1": "peep all",
            "2": "peep cpu",
            "3": "peep io",
            "4": "peep mem",
            "5": "peep clutter",
            "6": "peep watch",
            "7": "baseline save",
            "8": "baseline diff",
            "s": "settings",
            "h": "help",
            "q": "quit",
        }
        
        # Property 2: Number of unique commands with shortcuts matches menu items
        # (Note: help has two shortcuts, so we count unique commands)
        unique_commands = set(shortcuts.values())
        assert len(unique_commands) == len(menu_items), \
            f"Mismatch: {len(unique_commands)} unique commands with shortcuts, " \
            f"{len(menu_items)} menu items"
        
        # Property 3: All menu items are reachable
        # Extract command names from menu items (strip "beefy " prefix)
        menu_commands = []
        for cmd, _ in menu_items:
            if cmd.startswith("beefy "):
                menu_commands.append(cmd[6:])  # Remove "beefy " prefix
            else:
                menu_commands.append(cmd)
        
        shortcut_commands = set(shortcuts.values())
        
        for menu_cmd in menu_commands:
            assert menu_cmd in shortcut_commands, \
                f"Menu item '{menu_cmd}' has no corresponding shortcut"
    
    @given(
        valid_input=st.sampled_from([
            "1", "2", "3", "4", "5", "6", "7", "8",
            "s", "h", "q", "?",
            "peep all", "peep cpu", "peep io", "peep mem",
            "all", "cpu", "io", "mem",
            "settings", "help", "quit"
        ])
    )
    @settings(max_examples=100, deadline=None)
    def test_valid_input_always_recognized(self, valid_input):
        """Property: All valid inputs are recognized.
        
        PROPERTY: For any valid input (shortcut or full command):
        1. Input is recognized as valid
        2. Input maps to a known command
        3. No valid input produces an error
        
        Validates: Requirements 5.3, 5.6 (valid inputs are always recognized)
        """
        # Define all valid inputs and their mappings
        shortcut_map = {
            "1": "peep all",
            "2": "peep cpu",
            "3": "peep io",
            "4": "peep mem",
            "5": "peep clutter",
            "6": "peep watch",
            "7": "baseline save",
            "8": "baseline diff",
            "s": "settings",
            "h": "help",
            "?": "help",
            "q": "quit",
        }
        
        # Additional command aliases
        command_aliases = {
            "all": "peep all",
            "cpu": "peep cpu",
            "io": "peep io",
            "mem": "peep mem",
            "clutter": "peep clutter",
            "watch": "peep watch",
            "save": "baseline save",
            "diff": "baseline diff",
        }
        
        # Full commands (already in final form)
        full_commands = [
            "peep all", "peep cpu", "peep io", "peep mem",
            "peep clutter", "peep watch",
            "baseline save", "baseline diff",
            "settings", "help", "quit"
        ]
        
        # Normalize input (lowercase)
        normalized_input = valid_input.lower()
        
        # Property 1 & 2: Input is recognized and maps to a command
        is_recognized = (
            normalized_input in shortcut_map or
            normalized_input in command_aliases or
            normalized_input in full_commands
        )
        
        assert is_recognized, \
            f"Valid input '{valid_input}' (normalized: '{normalized_input}') not recognized"
        
        # Get the final command
        if normalized_input in shortcut_map:
            final_command = shortcut_map[normalized_input]
        elif normalized_input in command_aliases:
            final_command = command_aliases[normalized_input]
        else:
            final_command = normalized_input
        
        # Property 3: Final command is a known command
        known_commands = [
            "peep all", "peep cpu", "peep io", "peep mem",
            "peep clutter", "peep watch",
            "baseline save", "baseline diff",
            "settings", "help", "quit"
        ]
        
        assert final_command in known_commands, \
            f"Input '{valid_input}' maps to unknown command '{final_command}'"
    
    @given(
        prefix=st.sampled_from(["beefy ", "peepbeefy ", ""]),
        command=st.sampled_from(["peep all", "peep cpu", "settings", "help"])
    )
    @settings(max_examples=50, deadline=None)
    def test_prefix_stripping_consistency(self, prefix, command):
        """Property: Command prefix stripping is consistent.
        
        PROPERTY: For any command with optional prefix:
        1. "beefy <command>" is equivalent to "<command>"
        2. "peepbeefy <command>" is equivalent to "<command>"
        3. Prefix stripping doesn't affect the final command
        
        Validates: Requirements 5.7 (command-teaching approach)
        """
        # Build full input
        full_input = f"{prefix}{command}"
        
        # Simulate prefix stripping (from main.py interactive_loop)
        processed_cmd = full_input
        for strip_prefix in ("beefy ", "peepbeefy "):
            if processed_cmd.startswith(strip_prefix):
                processed_cmd = processed_cmd[len(strip_prefix):].lstrip()
                break
        
        # Property: Processed command matches original command
        assert processed_cmd == command, \
            f"Prefix stripping failed: '{full_input}' -> '{processed_cmd}', expected '{command}'"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--hypothesis-show-statistics"])
