"""
Property-based tests for dataclass serialization.

Tests:
- Property 20: Dataclass Serialization Round-Trip
- Property 21: Enum Serialization to String
- Property 22: JSON Output Validity
- Property 23: Required Field Validation

Validates Requirements 6.1, 6.2, 6.3, 6.5, 6.6, 6.7
"""

import json
import pytest
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import Optional, List, Dict, Any
from hypothesis import given, strategies as st, assume
from src.serializer import to_dict, from_dict, json_stringify


# --- Test Enums ---

class ColorMode(Enum):
    """Test enum for serialization testing."""
    OPTION_A = "option_a"
    OPTION_B = "option_b"
    OPTION_C = "option_c"


class Priority(Enum):
    """Test enum with auto() values."""
    FIRST = auto()
    SECOND = auto()
    THIRD = auto()


# --- Test Dataclasses ---

@dataclass
class SimpleDataclass:
    """Simple dataclass with primitive types."""
    name: str
    count: int
    enabled: bool
    ratio: float


@dataclass
class DataclassWithOptionals:
    """Dataclass with optional fields."""
    required_field: str
    optional_str: Optional[str] = None
    optional_int: Optional[int] = None
    optional_bool: Optional[bool] = None


@dataclass
class DataclassWithDefaults:
    """Dataclass with default values."""
    name: str
    count: int = 0
    enabled: bool = True
    tags: List[str] = field(default_factory=list)


@dataclass
class DataclassWithEnum:
    """Dataclass containing enum field."""
    name: str
    mode: ColorMode
    auto_mode: Priority


@dataclass
class DataclassWithPath:
    """Dataclass containing Path field."""
    name: str
    file_path: Path
    optional_path: Optional[Path] = None


@dataclass
class NestedInner:
    """Inner dataclass for nesting tests."""
    value: int
    label: str


@dataclass
class NestedOuter:
    """Outer dataclass containing nested dataclass."""
    name: str
    inner: NestedInner
    inner_list: List[NestedInner]


@dataclass
class DataclassWithCollections:
    """Dataclass with list and dict fields."""
    name: str
    tags: List[str]
    metadata: Dict[str, Any]
    numbers: List[int]


# --- Hypothesis Strategies ---

# Strategy for simple dataclasses
simple_dataclass_strategy = st.builds(
    SimpleDataclass,
    name=st.text(min_size=1, max_size=50),
    count=st.integers(min_value=-1000, max_value=1000),
    enabled=st.booleans(),
    ratio=st.floats(min_value=-100.0, max_value=100.0, allow_nan=False, allow_infinity=False)
)

# Strategy for dataclasses with optionals
dataclass_with_optionals_strategy = st.builds(
    DataclassWithOptionals,
    required_field=st.text(min_size=1, max_size=50),
    optional_str=st.one_of(st.none(), st.text(max_size=50)),
    optional_int=st.one_of(st.none(), st.integers(min_value=-100, max_value=100)),
    optional_bool=st.one_of(st.none(), st.booleans())
)

# Strategy for dataclasses with defaults
dataclass_with_defaults_strategy = st.builds(
    DataclassWithDefaults,
    name=st.text(min_size=1, max_size=50),
    count=st.integers(min_value=0, max_value=100),
    enabled=st.booleans(),
    tags=st.lists(st.text(min_size=1, max_size=20), max_size=10)
)

# Strategy for dataclasses with enums
dataclass_with_enum_strategy = st.builds(
    DataclassWithEnum,
    name=st.text(min_size=1, max_size=50),
    mode=st.sampled_from(ColorMode),
    auto_mode=st.sampled_from(Priority)
)

# Strategy for dataclasses with Path
dataclass_with_path_strategy = st.builds(
    DataclassWithPath,
    name=st.text(min_size=1, max_size=50),
    file_path=st.text(min_size=1, max_size=100).map(Path),
    optional_path=st.one_of(st.none(), st.text(min_size=1, max_size=100).map(Path))
)

# Strategy for nested dataclasses
nested_inner_strategy = st.builds(
    NestedInner,
    value=st.integers(min_value=0, max_value=1000),
    label=st.text(min_size=1, max_size=30)
)

nested_outer_strategy = st.builds(
    NestedOuter,
    name=st.text(min_size=1, max_size=50),
    inner=nested_inner_strategy,
    inner_list=st.lists(nested_inner_strategy, min_size=0, max_size=5)
)

# Strategy for dataclasses with collections
dataclass_with_collections_strategy = st.builds(
    DataclassWithCollections,
    name=st.text(min_size=1, max_size=50),
    tags=st.lists(st.text(min_size=1, max_size=20), max_size=10),
    metadata=st.dictionaries(
        keys=st.text(min_size=1, max_size=20),
        values=st.one_of(
            st.text(max_size=50),
            st.integers(min_value=-100, max_value=100),
            st.booleans(),
            st.floats(min_value=-100.0, max_value=100.0, allow_nan=False, allow_infinity=False)
        ),
        max_size=10
    ),
    numbers=st.lists(st.integers(min_value=-100, max_value=100), max_size=20)
)


class TestDataclassSerializationRoundTrip:
    """Property 20: Dataclass Serialization Round-Trip
    
    For any dataclass instance, converting to dictionary with to_dict() and
    reconstructing with from_dict() should produce an equivalent object with
    all field values preserved.
    
    Validates: Requirements 6.1, 6.2, 6.6
    """
    
    @given(simple_dataclass_strategy)
    def test_simple_dataclass_round_trip(self, obj: SimpleDataclass):
        """Simple dataclasses should round-trip perfectly."""
        # Convert to dict and back
        dict_repr = to_dict(obj)
        reconstructed = from_dict(SimpleDataclass, dict_repr)
        
        # All fields should be preserved
        assert reconstructed.name == obj.name
        assert reconstructed.count == obj.count
        assert reconstructed.enabled == obj.enabled
        assert reconstructed.ratio == obj.ratio
    
    @given(dataclass_with_optionals_strategy)
    def test_dataclass_with_optionals_round_trip(self, obj: DataclassWithOptionals):
        """Dataclasses with optional fields should round-trip correctly."""
        dict_repr = to_dict(obj)
        reconstructed = from_dict(DataclassWithOptionals, dict_repr)
        
        assert reconstructed.required_field == obj.required_field
        assert reconstructed.optional_str == obj.optional_str
        assert reconstructed.optional_int == obj.optional_int
        assert reconstructed.optional_bool == obj.optional_bool
    
    @given(dataclass_with_defaults_strategy)
    def test_dataclass_with_defaults_round_trip(self, obj: DataclassWithDefaults):
        """Dataclasses with default values should round-trip correctly."""
        dict_repr = to_dict(obj)
        reconstructed = from_dict(DataclassWithDefaults, dict_repr)
        
        assert reconstructed.name == obj.name
        assert reconstructed.count == obj.count
        assert reconstructed.enabled == obj.enabled
        assert reconstructed.tags == obj.tags
    
    @given(dataclass_with_path_strategy)
    def test_dataclass_with_path_round_trip(self, obj: DataclassWithPath):
        """Dataclasses with Path fields should round-trip correctly.
        
        Path objects are serialized to strings and reconstructed as Path objects.
        """
        dict_repr = to_dict(obj)
        
        # Verify Path is converted to string in dict
        assert isinstance(dict_repr['file_path'], str)
        if obj.optional_path is not None:
            assert isinstance(dict_repr['optional_path'], str)
        
        # Reconstruct and verify
        reconstructed = from_dict(DataclassWithPath, dict_repr)
        
        assert reconstructed.name == obj.name
        assert reconstructed.file_path == obj.file_path
        assert reconstructed.optional_path == obj.optional_path
    
    @given(nested_outer_strategy)
    def test_nested_dataclass_round_trip(self, obj: NestedOuter):
        """Nested dataclasses should round-trip correctly.
        
        Validates: Requirement 6.2 (nested dataclass handling)
        """
        dict_repr = to_dict(obj)
        
        # Verify nested structure is converted to dicts
        assert isinstance(dict_repr['inner'], dict)
        assert isinstance(dict_repr['inner_list'], list)
        if dict_repr['inner_list']:
            assert isinstance(dict_repr['inner_list'][0], dict)
        
        # Reconstruct and verify
        reconstructed = from_dict(NestedOuter, dict_repr)
        
        assert reconstructed.name == obj.name
        assert reconstructed.inner.value == obj.inner.value
        assert reconstructed.inner.label == obj.inner.label
        assert len(reconstructed.inner_list) == len(obj.inner_list)
        
        for i, inner in enumerate(obj.inner_list):
            assert reconstructed.inner_list[i].value == inner.value
            assert reconstructed.inner_list[i].label == inner.label
    
    @given(dataclass_with_collections_strategy)
    def test_dataclass_with_collections_round_trip(self, obj: DataclassWithCollections):
        """Dataclasses with lists and dicts should round-trip correctly."""
        dict_repr = to_dict(obj)
        reconstructed = from_dict(DataclassWithCollections, dict_repr)
        
        assert reconstructed.name == obj.name
        assert reconstructed.tags == obj.tags
        assert reconstructed.metadata == obj.metadata
        assert reconstructed.numbers == obj.numbers


class TestEnumSerialization:
    """Property 21: Enum Serialization to String
    
    For any dataclass containing enum fields, to_dict() should convert enum
    values to their string representations (enum.value or enum.name).
    
    Validates: Requirement 6.3
    """
    
    @given(dataclass_with_enum_strategy)
    def test_enum_serialization_to_string(self, obj: DataclassWithEnum):
        """Enums should be serialized to their string values."""
        dict_repr = to_dict(obj)
        
        # Enum with explicit values should use .value
        assert isinstance(dict_repr['mode'], str)
        assert dict_repr['mode'] == obj.mode.value
        
        # Enum with auto() should use .name (since auto() generates int values)
        assert isinstance(dict_repr['auto_mode'], str)
        # auto() enums serialize to their name since value is an int
        assert dict_repr['auto_mode'] in ['FIRST', 'SECOND', 'THIRD']
    
    @given(st.sampled_from(ColorMode))
    def test_standalone_enum_serialization(self, enum_value: ColorMode):
        """Standalone enum values should serialize to strings."""
        result = to_dict(enum_value)
        
        assert isinstance(result, str)
        assert result == enum_value.value
    
    @given(st.sampled_from(Priority))
    def test_auto_enum_serialization(self, enum_value: Priority):
        """Auto enums should serialize to their name."""
        result = to_dict(enum_value)
        
        assert isinstance(result, str)
        assert result == enum_value.name


class TestJSONOutputValidity:
    """Property 22: JSON Output Validity
    
    For any dataclass instance, json_stringify() should produce valid JSON
    that can be parsed back into a dictionary.
    
    Validates: Requirement 6.5
    """
    
    @given(simple_dataclass_strategy)
    def test_json_output_is_valid(self, obj: SimpleDataclass):
        """JSON output should be valid and parseable."""
        json_str = json_stringify(obj)
        
        # Should be valid JSON
        parsed = json.loads(json_str)
        
        # Should be a dictionary
        assert isinstance(parsed, dict)
        
        # Should contain all fields
        assert 'name' in parsed
        assert 'count' in parsed
        assert 'enabled' in parsed
        assert 'ratio' in parsed
    
    @given(nested_outer_strategy)
    def test_nested_json_output_is_valid(self, obj: NestedOuter):
        """Nested dataclasses should produce valid JSON."""
        json_str = json_stringify(obj)
        
        # Should be valid JSON
        parsed = json.loads(json_str)
        
        # Should preserve nested structure
        assert isinstance(parsed, dict)
        assert isinstance(parsed['inner'], dict)
        assert isinstance(parsed['inner_list'], list)
    
    @given(dataclass_with_enum_strategy)
    def test_enum_json_output_is_valid(self, obj: DataclassWithEnum):
        """Dataclasses with enums should produce valid JSON."""
        json_str = json_stringify(obj)
        
        # Should be valid JSON
        parsed = json.loads(json_str)
        
        # Enums should be serialized as strings
        assert isinstance(parsed['mode'], str)
        assert isinstance(parsed['auto_mode'], str)
    
    @given(dataclass_with_path_strategy)
    def test_path_json_output_is_valid(self, obj: DataclassWithPath):
        """Dataclasses with Path fields should produce valid JSON."""
        json_str = json_stringify(obj)
        
        # Should be valid JSON
        parsed = json.loads(json_str)
        
        # Paths should be serialized as strings
        assert isinstance(parsed['file_path'], str)
        if obj.optional_path is not None:
            assert isinstance(parsed['optional_path'], str)
    
    @given(simple_dataclass_strategy, st.integers(min_value=0, max_value=8))
    def test_json_indentation_parameter(self, obj: SimpleDataclass, indent: int):
        """JSON output should respect indentation parameter."""
        json_str = json_stringify(obj, indent=indent)
        
        # Should be valid JSON regardless of indentation
        parsed = json.loads(json_str)
        assert isinstance(parsed, dict)
        
        # If indent > 0, should contain newlines
        if indent > 0:
            assert '\n' in json_str
    
    @given(dataclass_with_collections_strategy)
    def test_collections_json_output_is_valid(self, obj: DataclassWithCollections):
        """Dataclasses with collections should produce valid JSON."""
        json_str = json_stringify(obj)
        
        # Should be valid JSON
        parsed = json.loads(json_str)
        
        # Collections should be preserved
        assert isinstance(parsed['tags'], list)
        assert isinstance(parsed['metadata'], dict)
        assert isinstance(parsed['numbers'], list)


class TestRequiredFieldValidation:
    """Property 23: Required Field Validation
    
    For any dictionary missing required fields for a dataclass, from_dict()
    should raise a TypeError or ValueError indicating the missing field.
    
    Validates: Requirement 6.7
    """
    
    def test_missing_required_field_raises_error(self):
        """Missing required fields should raise ValueError."""
        # SimpleDataclass requires: name, count, enabled, ratio
        incomplete_dict = {
            'name': 'test',
            'count': 42,
            'enabled': True
            # Missing 'ratio'
        }
        
        with pytest.raises(ValueError, match="Required field 'ratio' missing"):
            from_dict(SimpleDataclass, incomplete_dict)
    
    def test_missing_multiple_required_fields_raises_error(self):
        """Missing multiple required fields should raise ValueError."""
        incomplete_dict = {
            'name': 'test'
            # Missing: count, enabled, ratio
        }
        
        with pytest.raises(ValueError, match="Required field"):
            from_dict(SimpleDataclass, incomplete_dict)
    
    def test_optional_fields_can_be_missing(self):
        """Optional fields can be omitted without error."""
        minimal_dict = {
            'required_field': 'test'
            # All optional fields omitted
        }
        
        # Should not raise
        obj = from_dict(DataclassWithOptionals, minimal_dict)
        
        assert obj.required_field == 'test'
        assert obj.optional_str is None
        assert obj.optional_int is None
        assert obj.optional_bool is None
    
    def test_fields_with_defaults_can_be_missing(self):
        """Fields with default values can be omitted."""
        minimal_dict = {
            'name': 'test'
            # count, enabled, tags have defaults
        }
        
        # Should not raise
        obj = from_dict(DataclassWithDefaults, minimal_dict)
        
        assert obj.name == 'test'
        assert obj.count == 0  # Default value
        assert obj.enabled is True  # Default value
        assert obj.tags == []  # Default factory
    
    def test_non_dict_input_raises_type_error(self):
        """Passing non-dict to from_dict should raise TypeError."""
        with pytest.raises(TypeError, match="Expected dict"):
            from_dict(SimpleDataclass, "not a dict")  # type: ignore
        
        with pytest.raises(TypeError, match="Expected dict"):
            from_dict(SimpleDataclass, [1, 2, 3])  # type: ignore
        
        with pytest.raises(TypeError, match="Expected dict"):
            from_dict(SimpleDataclass, 42)  # type: ignore
    
    def test_non_dataclass_type_raises_type_error(self):
        """Passing non-dataclass type to from_dict should raise TypeError."""
        with pytest.raises(TypeError, match="is not a dataclass"):
            from_dict(str, {'value': 'test'})  # type: ignore
        
        with pytest.raises(TypeError, match="is not a dataclass"):
            from_dict(int, {'value': 42})  # type: ignore
    
    @given(
        st.lists(
            st.sampled_from(['name', 'count', 'enabled', 'ratio']),
            min_size=1,
            max_size=3,
            unique=True
        )
    )
    def test_partial_dict_raises_error_for_missing_fields(self, present_fields: List[str]):
        """Any subset of required fields should raise error if incomplete."""
        # Create dict with only some fields
        all_values = {
            'name': 'test',
            'count': 42,
            'enabled': True,
            'ratio': 0.5
        }
        
        partial_dict = {field: all_values[field] for field in present_fields}
        
        # If we have all 4 fields, it should work
        if len(present_fields) == 4:
            obj = from_dict(SimpleDataclass, partial_dict)
            assert obj.name == 'test'
        else:
            # Otherwise should raise
            with pytest.raises(ValueError, match="Required field"):
                from_dict(SimpleDataclass, partial_dict)


class TestEdgeCases:
    """Test edge cases for serialization."""
    
    def test_none_values_serialize_correctly(self):
        """None values should serialize to None."""
        obj = DataclassWithOptionals(
            required_field='test',
            optional_str=None,
            optional_int=None,
            optional_bool=None
        )
        
        dict_repr = to_dict(obj)
        
        assert dict_repr['optional_str'] is None
        assert dict_repr['optional_int'] is None
        assert dict_repr['optional_bool'] is None
    
    def test_empty_collections_serialize_correctly(self):
        """Empty lists and dicts should serialize correctly."""
        obj = DataclassWithCollections(
            name='test',
            tags=[],
            metadata={},
            numbers=[]
        )
        
        dict_repr = to_dict(obj)
        
        assert dict_repr['tags'] == []
        assert dict_repr['metadata'] == {}
        assert dict_repr['numbers'] == []
    
    def test_nested_empty_list_serializes_correctly(self):
        """Nested dataclass with empty list should serialize correctly."""
        obj = NestedOuter(
            name='test',
            inner=NestedInner(value=42, label='test'),
            inner_list=[]
        )
        
        dict_repr = to_dict(obj)
        reconstructed = from_dict(NestedOuter, dict_repr)
        
        assert reconstructed.inner_list == []
    
    def test_tuple_converts_to_list(self):
        """Tuples should be converted to lists for JSON compatibility."""
        # Create a simple object with a tuple
        tuple_data = (1, 2, 3)
        result = to_dict(tuple_data)
        
        # Should be converted to list
        assert isinstance(result, list)
        assert result == [1, 2, 3]
    
    def test_deeply_nested_structures(self):
        """Deeply nested structures should serialize correctly."""
        @dataclass
        class Level3:
            value: int
        
        @dataclass
        class Level2:
            level3: Level3
        
        @dataclass
        class Level1:
            level2: Level2
        
        obj = Level1(level2=Level2(level3=Level3(value=42)))
        
        dict_repr = to_dict(obj)
        reconstructed = from_dict(Level1, dict_repr)
        
        assert reconstructed.level2.level3.value == 42
    
    def test_special_characters_in_strings(self):
        """Strings with special characters should serialize correctly."""
        obj = SimpleDataclass(
            name='test\n\t"quotes"',
            count=42,
            enabled=True,
            ratio=0.5
        )
        
        json_str = json_stringify(obj)
        parsed = json.loads(json_str)
        
        assert parsed['name'] == 'test\n\t"quotes"'
    
    def test_unicode_strings_serialize_correctly(self):
        """Unicode strings should serialize correctly."""
        obj = SimpleDataclass(
            name='测试 🎉 café',
            count=42,
            enabled=True,
            ratio=0.5
        )
        
        json_str = json_stringify(obj)
        parsed = json.loads(json_str)
        
        assert parsed['name'] == '测试 🎉 café'
