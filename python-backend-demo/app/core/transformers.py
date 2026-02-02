"""Data transformation utilities

This module provides utilities to transform data from MongoDB format
to the format expected by mobile clients.
"""

from typing import Any, Dict, List, Optional, Union


def to_multilingual(value: Union[str, Dict[str, str], None]) -> Dict[str, str]:
    """Convert a value to multilingual format.

    Args:
        value: Can be a string, a dict with language keys, or None

    Returns:
        Dict with 'en', 'es', 'pt' keys

    Examples:
        >>> to_multilingual("Coffee")
        {'en': 'Coffee', 'es': '', 'pt': ''}

        >>> to_multilingual({'en': 'Coffee', 'es': 'Café'})
        {'en': 'Coffee', 'es': 'Café', 'pt': ''}

        >>> to_multilingual(None)
        {'en': '', 'es': '', 'pt': ''}
    """
    if value is None:
        return {"en": "", "es": "", "pt": ""}

    if isinstance(value, str):
        return {"en": value, "es": "", "pt": ""}

    if isinstance(value, dict):
        return {
            "en": value.get("en", ""),
            "es": value.get("es", ""),
            "pt": value.get("pt", ""),
        }

    return {"en": "", "es": "", "pt": ""}


def transform_modifier_option(option: Dict[str, Any]) -> Dict[str, Any]:
    """Transform modifier option to expected format.

    Args:
        option: Raw modifier option from MongoDB

    Returns:
        Transformed modifier option with multilingual name
    """
    return {
        "id": option.get("id", ""),
        "name": to_multilingual(option.get("name")),
        "priceCents": option.get("priceCents", 0),
    }


def transform_modifier(modifier: Dict[str, Any]) -> Dict[str, Any]:
    """Transform modifier to expected format.

    Args:
        modifier: Raw modifier from MongoDB

    Returns:
        Transformed modifier with multilingual fields and defaults
    """
    return {
        "id": modifier.get("id", ""),
        "name": to_multilingual(modifier.get("name")),
        "type": modifier.get("type", "standard"),  # Default to "standard"
        "required": modifier.get("required", False),
        "selectionMode": modifier.get("selectionMode", "single"),  # Default to "single"
        "maxChoices": modifier.get("maxChoices", 1),  # Default to 1
        "freeChoices": modifier.get("freeChoices", 1),  # Default to 1
        "extraChoicePriceCents": modifier.get("extraChoicePriceCents", 0),
        "options": [transform_modifier_option(opt) for opt in modifier.get("options", [])],
    }


def transform_variant(variant: Dict[str, Any]) -> Dict[str, Any]:
    """Transform variant to expected format.

    Args:
        variant: Raw variant from MongoDB

    Returns:
        Transformed variant with string name (not multilingual)
    """
    return {
        "id": variant.get("id", ""),
        "name": variant.get("name", ""),  # Keep as string, not multilingual
        "priceCents": variant.get("priceCents", 0),
        "default": variant.get("default", False),
    }


def transform_menu_item(item: Dict[str, Any]) -> Dict[str, Any]:
    """Transform menu item to expected format.

    Args:
        item: Raw menu item from MongoDB

    Returns:
        Transformed menu item with multilingual fields
    """
    return {
        "id": item.get("id", ""),
        "name": to_multilingual(item.get("name")),
        "description": to_multilingual(item.get("description")),
        "imageUrls": item.get("imageUrls", []),
        "categoryId": item.get("categoryId", ""),
        "priceCents": item.get("priceCents", 0),
        "makingCostCents": item.get("makingCostCents", 0),
        "isAvailable": item.get("isAvailable", True),
        "stationTags": item.get("stationTags", []),
        "variants": [transform_variant(v) for v in item.get("variants", [])],
        "modifiers": [transform_modifier(m) for m in item.get("modifiers", [])],
    }


def transform_category(category: Dict[str, Any]) -> Dict[str, Any]:
    """Transform category to expected format.

    Args:
        category: Raw category from MongoDB

    Returns:
        Transformed category with multilingual fields
    """
    return {
        "id": category.get("id", ""),
        "name": to_multilingual(category.get("name")),
        "description": to_multilingual(category.get("description")),  # Always multilingual object, never None
        "sortOrder": category.get("sortOrder", 0),
        "emoji": category.get("emoji"),
    }


def transform_menu(menu: Dict[str, Any]) -> Dict[str, Any]:
    """Transform complete menu to expected format.

    Args:
        menu: Raw menu from MongoDB

    Returns:
        Transformed menu with all multilingual fields
    """
    return {
        "_id": menu.get("_id", ""),
        "restaurantId": menu.get("restaurantId", ""),
        "locationId": menu.get("locationId", ""),
        "menuSlug": menu.get("menuSlug", ""),
        "name": to_multilingual(menu.get("name")),
        "categories": [transform_category(c) for c in menu.get("categories", [])],
        "items": [transform_menu_item(i) for i in menu.get("items", [])],
        "salesTax": menu.get("salesTax", 0.0),
    }


def transform_menu_summary(menu: Dict[str, Any]) -> Dict[str, Any]:
    """Transform menu summary to expected format.

    Args:
        menu: Raw menu from MongoDB

    Returns:
        Transformed menu summary with multilingual name
    """
    return {
        "_id": menu.get("_id", ""),
        "menuSlug": menu.get("menuSlug", ""),
        "name": to_multilingual(menu.get("name")),
        "description": to_multilingual(menu.get("description")) if menu.get("description") else None,
    }
