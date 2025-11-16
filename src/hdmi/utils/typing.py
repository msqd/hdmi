from typing import Any, Type, get_origin, get_args


def extract_type_from_optional(type_hint: Any) -> Type | None:
    """Extract the actual type from an Optional/Union type hint.

    Args:
        type_hint: The type hint to analyze (e.g., Config | None, Optional[Config])

    Returns:
        The extracted type if it's an Optional/Union, or the original type if not.
        Returns None if the union contains only None or multiple non-None types.

    Examples:
        >>> extract_type_from_optional(str | None)
        <class 'str'>
        >>> extract_type_from_optional(int)
        <class 'int'>
        >>> extract_type_from_optional(str | int)  # Multiple non-None types
        None
    """
    # Check if it's a Union type (including Optional which is Union[T, None])
    origin = get_origin(type_hint)
    if origin is not None:
        # It's a generic type, check if it's a Union
        args = get_args(type_hint)
        if args:
            # Filter out NoneType from the union
            non_none_types = [arg for arg in args if arg is not type(None)]

            # If there's exactly one non-None type, return it
            if len(non_none_types) == 1:
                return non_none_types[0]
            # Multiple non-None types or all None - can't determine single type
            return None

    # Not a union type, return as-is
    return type_hint
