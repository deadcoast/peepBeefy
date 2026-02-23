"""Enhanced JSON serialization for dataclass-based configuration.

This module provides robust JSON serialization and deserialization for
dataclass instances with support for:
- Nested dataclass structures
- Enum types
- Path objects
- Custom type handlers
- Pretty-printed JSON output
"""

import json
from dataclasses import is_dataclass, fields, asdict
from enum import Enum
from pathlib import Path
from typing import Any, Type, TypeVar, get_origin, get_args
import logging

logger = logging.getLogger(__name__)

T = TypeVar('T')


def to_dict(obj: Any) -> dict | list | Any:
    """Convert dataclass to dictionary recursively.
    
    Handles nested dataclasses, enums, Path objects, and other complex types
    by converting them to JSON-compatible representations.
    
    Args:
        obj: Object to convert (dataclass, enum, Path, or primitive)
        
    Returns:
        Dictionary, list, or primitive value suitable for JSON serialization
        
    Example:
        >>> @dataclass
        ... class Config:
        ...     name: str
        ...     path: Path
        >>> to_dict(Config(name="test", path=Path("/tmp")))
        {'name': 'test', 'path': '/tmp'}
    """
    # Handle None
    if obj is None:
        return None
    
    # Handle dataclass instances
    if is_dataclass(obj) and not isinstance(obj, type):
        result = {}
        for field in fields(obj):
            value = getattr(obj, field.name)
            result[field.name] = to_dict(value)
        return result
    
    # Handle enums - convert to string representation
    if isinstance(obj, Enum):
        return obj.value if hasattr(obj, 'value') else obj.name
    
    # Handle Path objects - convert to string
    if isinstance(obj, Path):
        return str(obj)
    
    # Handle lists
    if isinstance(obj, list):
        return [to_dict(item) for item in obj]
    
    # Handle tuples - convert to lists for JSON compatibility
    if isinstance(obj, tuple):
        return [to_dict(item) for item in obj]
    
    # Handle dictionaries
    if isinstance(obj, dict):
        return {key: to_dict(value) for key, value in obj.items()}
    
    # Handle primitive types (str, int, float, bool)
    if isinstance(obj, (str, int, float, bool)):
        return obj
    
    # For other types, try to convert to string as fallback
    try:
        return str(obj)
    except Exception as e:
        logger.warning(f"Could not serialize object of type {type(obj).__name__}: {e}")
        return None


def from_dict(cls: Type[T], data: dict) -> T:
    """Reconstruct dataclass from dictionary.
    
    Validates required fields and converts nested dictionaries back to
    dataclass instances recursively.
    
    Args:
        cls: Dataclass type to reconstruct
        data: Dictionary containing field values
        
    Returns:
        Instance of cls with values from data
        
    Raises:
        TypeError: If cls is not a dataclass or data is not a dict
        ValueError: If required fields are missing
        
    Example:
        >>> @dataclass
        ... class Config:
        ...     name: str
        ...     count: int = 0
        >>> from_dict(Config, {'name': 'test'})
        Config(name='test', count=0)
    """
    if not is_dataclass(cls):
        raise TypeError(f"{cls.__name__} is not a dataclass")
    
    if not isinstance(data, dict):
        raise TypeError(f"Expected dict, got {type(data).__name__}")
    
    # Collect field values
    field_values = {}
    
    for field in fields(cls):
        field_name = field.name
        field_type = field.type
        
        # Check if field is present in data
        if field_name not in data:
            # Check if field has a default value
            if field.default is not field.default_factory:
                # Field has default, skip it
                continue
            elif field.default_factory is not field.default_factory:  # type: ignore
                # Field has default_factory, skip it
                continue
            else:
                # Required field is missing
                raise ValueError(f"Required field '{field_name}' missing from data")
        
        value = data[field_name]
        
        # Handle None values
        if value is None:
            field_values[field_name] = None
            continue
        
        # Get the origin type for generic types (e.g., List, Dict, Optional)
        origin = get_origin(field_type)
        
        # Handle Optional types (Union[X, None])
        if origin is type(None) or (hasattr(field_type, '__args__') and type(None) in get_args(field_type)):
            # Extract the non-None type from Optional
            args = get_args(field_type)
            if args:
                actual_type = args[0] if args[0] is not type(None) else (args[1] if len(args) > 1 else str)
                field_type = actual_type
                origin = get_origin(actual_type)
        
        # Handle nested dataclasses
        if is_dataclass(field_type) and isinstance(value, dict):
            field_values[field_name] = from_dict(field_type, value)
        
        # Handle Path objects
        elif field_type is Path or (origin is None and field_type.__name__ == 'Path'):
            field_values[field_name] = Path(value) if isinstance(value, str) else value
        
        # Handle lists
        elif origin is list:
            args = get_args(field_type)
            if args and is_dataclass(args[0]) and isinstance(value, list):
                # List of dataclasses
                field_values[field_name] = [from_dict(args[0], item) if isinstance(item, dict) else item for item in value]
            else:
                field_values[field_name] = value
        
        # Handle dictionaries
        elif origin is dict:
            field_values[field_name] = value
        
        # Handle primitive types
        else:
            field_values[field_name] = value
    
    # Create instance with collected field values
    try:
        return cls(**field_values)
    except TypeError as e:
        raise ValueError(f"Failed to construct {cls.__name__}: {e}") from e


def json_stringify(obj: Any, indent: int = 2) -> str:
    """Convert dataclass to pretty-printed JSON string.
    
    Converts the object to a dictionary using to_dict() and then
    serializes to JSON with configurable indentation.
    
    Args:
        obj: Object to serialize (typically a dataclass)
        indent: Number of spaces for indentation (default: 2)
        
    Returns:
        Pretty-printed JSON string
        
    Raises:
        TypeError: If object cannot be serialized to JSON
        
    Example:
        >>> @dataclass
        ... class Config:
        ...     name: str
        ...     enabled: bool
        >>> json_stringify(Config(name="test", enabled=True))
        '{\\n  "name": "test",\\n  "enabled": true\\n}'
    """
    try:
        dict_repr = to_dict(obj)
        return json.dumps(dict_repr, indent=indent, ensure_ascii=False)
    except (TypeError, ValueError) as e:
        logger.error(f"Failed to serialize object to JSON: {e}")
        raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable") from e
