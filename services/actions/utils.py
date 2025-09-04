from typing import Any, Text, Optional
from rasa_sdk import Tracker
import logging

logger = logging.getLogger(__name__)

def extract_entity(tracker: Tracker, entity_name: Text) -> Optional[Any]:
    """
    Extracts the value of an entity from the latest user message.
    Args:
        tracker (Tracker): The Rasa tracker object.
        entity_name (Text): The name of the entity to extract.
    Returns:
        Optional[Any]: The value of the entity if found, else None.
    """
    try:
        for entity in tracker.latest_message.get("entities", []):
            if entity.get("entity") == entity_name:
                return entity.get("value")
    except Exception as e:
        logger.error(f"Failed to extract entity '{entity_name}': {e}")
    return None

def validate_slot_value(slot_name: Text, value: Any) -> bool:
    """
    Validates the value of a slot based on custom logic.
    Args:
        slot_name (Text): The name of the slot.
        value (Any): The value to validate.
    Returns:
        bool: True if valid, False otherwise.
    """
    if value is None:
        return False
    # Add custom validation logic for each slot as needed
    if slot_name == "location" and not isinstance(value, str):
        return False
    if slot_name == "date" and not isinstance(value, str):
        return False
    # Extend with more slot-specific validation as needed
    return True
