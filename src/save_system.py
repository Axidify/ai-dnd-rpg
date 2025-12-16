"""
Save/Load System for AI D&D Text RPG (Phase 3, Step 3.1)
Handles game state persistence using JSON files.

MULTI-PLATFORM NOTES:
- Uses dict/JSON format for API compatibility (Phase 5)
- StorageBackend abstraction allows swapping local/cloud storage
- character_to_dict() / dict_to_character() ready for REST API
- Save data structure compatible with database storage (Phase 5.3)

ERROR HANDLING:
- Custom exception hierarchy for granular error handling
- Validation before save/load operations
- Detailed error messages with recovery suggestions
- Logging support for debugging
"""

import os
import json
import logging
from abc import ABC, abstractmethod
from datetime import datetime
from dataclasses import asdict
from typing import Optional, Dict, Any, List, Tuple
from enum import Enum

# Configure logging
logger = logging.getLogger(__name__)

# Default save directory
SAVES_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "saves")


# =============================================================================
# CUSTOM EXCEPTIONS (for granular error handling)
# =============================================================================

class SaveSystemError(Exception):
    """Base exception for save system errors."""
    def __init__(self, message: str, recovery_hint: str = ""):
        self.message = message
        self.recovery_hint = recovery_hint
        super().__init__(self.message)
    
    def __str__(self):
        if self.recovery_hint:
            return f"{self.message}\n💡 Hint: {self.recovery_hint}"
        return self.message


class SaveFileNotFoundError(SaveSystemError):
    """Raised when a save file cannot be found."""
    def __init__(self, filepath: str):
        super().__init__(
            f"Save file not found: {filepath}",
            "Use 'saves' command to list available saves."
        )
        self.filepath = filepath


class SaveFileCorruptedError(SaveSystemError):
    """Raised when a save file is corrupted or invalid."""
    def __init__(self, filepath: str, details: str = ""):
        super().__init__(
            f"Corrupted save file: {filepath}" + (f" ({details})" if details else ""),
            "The save file may be damaged. Try loading a different save or creating a new game."
        )
        self.filepath = filepath
        self.details = details


class SaveVersionMismatchError(SaveSystemError):
    """Raised when save file version is incompatible."""
    def __init__(self, file_version: str, current_version: str):
        super().__init__(
            f"Save version mismatch: file is v{file_version}, game requires v{current_version}",
            "This save was created with an older/newer game version. A migration may be needed."
        )
        self.file_version = file_version
        self.current_version = current_version


class SavePermissionError(SaveSystemError):
    """Raised when there's no permission to read/write saves."""
    def __init__(self, operation: str, filepath: str):
        super().__init__(
            f"Permission denied: Cannot {operation} save file: {filepath}",
            "Check file permissions or try running as administrator."
        )
        self.operation = operation
        self.filepath = filepath


class SaveValidationError(SaveSystemError):
    """Raised when save data fails validation."""
    def __init__(self, field: str, issue: str):
        super().__init__(
            f"Invalid save data: {field} - {issue}",
            "The save file may be corrupted or manually edited incorrectly."
        )
        self.field = field
        self.issue = issue


class SaveDiskSpaceError(SaveSystemError):
    """Raised when there's not enough disk space to save."""
    def __init__(self):
        super().__init__(
            "Not enough disk space to save the game.",
            "Free up some disk space and try again."
        )


# Current save format version
SAVE_VERSION = "1.1"

# Supported versions for migration
SUPPORTED_VERSIONS = ["1.0", "1.1"]


# =============================================================================
# STORAGE BACKEND ABSTRACTION (for multi-platform support)
# =============================================================================

class StorageBackend(ABC):
    """
    Abstract base class for save storage backends.
    
    Allows swapping between:
    - LocalFileBackend (current, for CLI)
    - CloudBackend (Phase 5.3, for mobile/web)
    - DatabaseBackend (Phase 5, for user accounts)
    """
    
    @abstractmethod
    def save(self, save_id: str, data: Dict[str, Any]) -> bool:
        """Save game data. Returns True on success."""
        pass
    
    @abstractmethod
    def load(self, save_id: str) -> Optional[Dict[str, Any]]:
        """Load game data. Returns None if not found."""
        pass
    
    @abstractmethod
    def delete(self, save_id: str) -> bool:
        """Delete a save. Returns True on success."""
        pass
    
    @abstractmethod
    def list_saves(self) -> List[Dict[str, Any]]:
        """List all saves with metadata."""
        pass


class LocalFileBackend(StorageBackend):
    """Local filesystem storage backend (default for CLI) with robust error handling."""
    
    def __init__(self, saves_dir: Optional[str] = None):
        self.saves_dir = saves_dir or SAVES_DIR
        self._ensure_saves_directory()
    
    def _ensure_saves_directory(self) -> None:
        """Create saves directory with proper error handling."""
        try:
            if not os.path.exists(self.saves_dir):
                os.makedirs(self.saves_dir)
                logger.info(f"Created saves directory: {self.saves_dir}")
        except PermissionError:
            raise SavePermissionError("create", self.saves_dir)
        except OSError as e:
            logger.error(f"Failed to create saves directory: {e}")
            raise SaveSystemError(
                f"Cannot create saves directory: {self.saves_dir}",
                "Check that the path is valid and you have write permissions."
            )
    
    def _get_filepath(self, save_id: str) -> str:
        """Get the full filepath for a save ID, with validation."""
        # Sanitize save_id to prevent directory traversal
        safe_id = "".join(c for c in save_id if c.isalnum() or c in ('_', '-'))
        if safe_id != save_id:
            logger.warning(f"Sanitized save_id: {save_id} -> {safe_id}")
        return os.path.join(self.saves_dir, f"{safe_id}.json")
    
    def save(self, save_id: str, data: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Save game data with comprehensive error handling.
        
        Returns:
            Tuple of (success: bool, message: str)
        """
        filepath = self._get_filepath(save_id)
        
        try:
            # Check disk space (basic check)
            if hasattr(os, 'statvfs'):  # Unix
                stats = os.statvfs(self.saves_dir)
                free_space = stats.f_bavail * stats.f_frsize
                if free_space < 1024 * 1024:  # Less than 1MB
                    raise SaveDiskSpaceError()
            
            # Write to temp file first, then rename (atomic operation)
            temp_filepath = filepath + ".tmp"
            with open(temp_filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            # Rename temp to final (atomic on most systems)
            if os.path.exists(filepath):
                os.replace(temp_filepath, filepath)
            else:
                os.rename(temp_filepath, filepath)
            
            logger.info(f"Saved game to: {filepath}")
            return (True, f"Game saved successfully: {os.path.basename(filepath)}")
            
        except PermissionError:
            logger.error(f"Permission denied saving to: {filepath}")
            raise SavePermissionError("write", filepath)
        except OSError as e:
            if "No space left" in str(e) or e.errno == 28:
                raise SaveDiskSpaceError()
            logger.error(f"OS error saving game: {e}")
            return (False, f"Failed to save: {e}")
        except Exception as e:
            logger.error(f"Unexpected error saving game: {e}")
            return (False, f"Failed to save: {e}")
    
    def load(self, save_id: str) -> Tuple[Optional[Dict[str, Any]], str]:
        """
        Load game data with comprehensive error handling.
        
        Returns:
            Tuple of (data: Optional[Dict], message: str)
        """
        filepath = self._get_filepath(save_id)
        
        try:
            if not os.path.exists(filepath):
                raise SaveFileNotFoundError(filepath)
            
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Validate basic structure
            if not isinstance(data, dict):
                raise SaveFileCorruptedError(filepath, "Not a valid save format")
            
            # Version check
            file_version = data.get('version', '1.0')
            if file_version not in SUPPORTED_VERSIONS:
                raise SaveVersionMismatchError(file_version, SAVE_VERSION)
            
            logger.info(f"Loaded game from: {filepath}")
            return (data, "Game loaded successfully")
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error in {filepath}: {e}")
            raise SaveFileCorruptedError(filepath, f"Invalid JSON at line {e.lineno}")
        except PermissionError:
            raise SavePermissionError("read", filepath)
        except (SaveFileNotFoundError, SaveFileCorruptedError, SaveVersionMismatchError):
            raise
        except Exception as e:
            logger.error(f"Unexpected error loading game: {e}")
            raise SaveSystemError(f"Failed to load save: {e}")
    
    def delete(self, save_id: str) -> Tuple[bool, str]:
        """
        Delete a save file with comprehensive error handling.
        
        Returns:
            Tuple of (success: bool, message: str)
        """
        filepath = self._get_filepath(save_id)
        
        try:
            if not os.path.exists(filepath):
                return (False, f"Save file not found: {save_id}")
            
            os.remove(filepath)
            logger.info(f"Deleted save: {filepath}")
            return (True, f"Save deleted: {save_id}")
            
        except PermissionError:
            logger.error(f"Permission denied deleting: {filepath}")
            return (False, "Permission denied. Cannot delete save file.")
        except Exception as e:
            logger.error(f"Error deleting save: {e}")
            return (False, f"Failed to delete save: {e}")
    
    def list_saves(self) -> Tuple[List[Dict[str, Any]], List[str]]:
        """
        List all saves with comprehensive error handling.
        
        Returns:
            Tuple of (saves: List[Dict], errors: List[str])
            - saves: List of valid save file metadata
            - errors: List of warning messages for corrupted saves
        """
        saves = []
        errors = []
        
        try:
            if not os.path.exists(self.saves_dir):
                logger.warning(f"Saves directory does not exist: {self.saves_dir}")
                return ([], ["No saves directory found."])
            
            for filename in os.listdir(self.saves_dir):
                if filename.endswith('.json') and filename.startswith('save_'):
                    filepath = os.path.join(self.saves_dir, filename)
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                        
                        # Validate minimum required fields
                        if 'character' not in data:
                            errors.append(f"⚠️ {filename}: Missing character data")
                            continue
                        
                        save_id = filename[:-5]  # Remove .json
                        saves.append({
                            'save_id': save_id,
                            'filename': filename,
                            'filepath': filepath,
                            'timestamp': data.get('timestamp', 'Unknown'),
                            'version': data.get('version', '1.0'),
                            'character_name': data.get('character', {}).get('name', 'Unknown'),
                            'character_level': data.get('character', {}).get('level', 1),
                            'character_class': data.get('character', {}).get('char_class', 'Unknown'),
                            'description': data.get('description', ''),
                            'has_scenario': data.get('scenario') is not None,
                        })
                    except json.JSONDecodeError as e:
                        errors.append(f"⚠️ {filename}: Corrupted JSON (line {e.lineno})")
                        logger.warning(f"Corrupted save file: {filename} - {e}")
                    except Exception as e:
                        errors.append(f"⚠️ {filename}: Cannot read ({e})")
                        logger.warning(f"Cannot read save file: {filename} - {e}")
            
            saves.sort(key=lambda x: x['timestamp'], reverse=True)
            logger.info(f"Listed {len(saves)} saves, {len(errors)} errors")
            
        except PermissionError:
            errors.append("Permission denied reading saves directory.")
            logger.error(f"Permission denied listing saves: {self.saves_dir}")
        except Exception as e:
            errors.append(f"Error listing saves: {e}")
            logger.error(f"Error listing saves: {e}")
        
        return (saves, errors)


# Default backend (can be swapped for cloud backend in Phase 5)
_default_backend: Optional[StorageBackend] = None

def get_storage_backend() -> StorageBackend:
    """Get the current storage backend (singleton)."""
    global _default_backend
    if _default_backend is None:
        _default_backend = LocalFileBackend()
    return _default_backend

def set_storage_backend(backend: StorageBackend):
    """Set a custom storage backend (for cloud saves, testing, etc.)."""
    global _default_backend
    _default_backend = backend


# =============================================================================
# VALIDATION FUNCTIONS
# =============================================================================

def validate_character_data(data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate character data before saving or after loading.
    
    Returns:
        Tuple of (is_valid: bool, errors: List[str])
    """
    errors = []
    
    # Required fields
    required = ['name', 'race', 'char_class', 'level']
    for field in required:
        if field not in data:
            errors.append(f"Missing required field: {field}")
    
    # Type validation
    if 'name' in data and not isinstance(data['name'], str):
        errors.append("Character name must be a string")
    
    if 'level' in data:
        level = data['level']
        if not isinstance(level, int) or level < 1 or level > 5:
            errors.append(f"Level must be an integer between 1 and 5, got: {level}")
    
    # HP validation
    if 'current_hp' in data and 'max_hp' in data:
        if data['current_hp'] > data['max_hp']:
            errors.append(f"Current HP ({data['current_hp']}) exceeds max HP ({data['max_hp']})")
    
    # Ability score validation
    abilities = ['strength', 'dexterity', 'constitution', 'intelligence', 'wisdom', 'charisma']
    for ability in abilities:
        if ability in data:
            score = data[ability]
            if not isinstance(score, int) or score < 1 or score > 30:
                errors.append(f"{ability.title()} must be 1-30, got: {score}")
    
    # Gold validation
    if 'gold' in data and (not isinstance(data['gold'], int) or data['gold'] < 0):
        errors.append(f"Gold must be a non-negative integer, got: {data['gold']}")
    
    # XP validation
    if 'experience' in data and (not isinstance(data['experience'], int) or data['experience'] < 0):
        errors.append(f"Experience must be a non-negative integer, got: {data['experience']}")
    
    return (len(errors) == 0, errors)


def validate_save_data(data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate complete save data structure.
    
    Returns:
        Tuple of (is_valid: bool, errors: List[str])
    """
    errors = []
    
    # Version check
    version = data.get('version', '1.0')
    if version not in SUPPORTED_VERSIONS:
        errors.append(f"Unsupported save version: {version}")
    
    # Character data is required
    if 'character' not in data:
        errors.append("Missing character data")
    else:
        char_valid, char_errors = validate_character_data(data['character'])
        if not char_valid:
            errors.extend([f"Character: {e}" for e in char_errors])
    
    # Timestamp validation
    if 'timestamp' in data:
        try:
            datetime.fromisoformat(data['timestamp'].replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            errors.append(f"Invalid timestamp format: {data.get('timestamp')}")
    
    return (len(errors) == 0, errors)


# =============================================================================
# SERIALIZATION FUNCTIONS (API-ready for Phase 5)
# These functions convert game objects to/from dictionaries.
# The dict format is designed to be:
# - JSON serializable (for local storage)
# - REST API compatible (for backend endpoints)
# - Database storable (for cloud saves)
# =============================================================================

def ensure_saves_dir():
    """Create saves directory if it doesn't exist."""
    try:
        if not os.path.exists(SAVES_DIR):
            os.makedirs(SAVES_DIR)
            logger.info(f"Created saves directory: {SAVES_DIR}")
    except Exception as e:
        logger.error(f"Failed to create saves directory: {e}")
        raise SaveSystemError(
            f"Cannot create saves directory: {SAVES_DIR}",
            "Check disk permissions and available space."
        )


def generate_save_filename(character_name: str, slot: Optional[int] = None) -> str:
    """Generate a save filename."""
    safe_name = "".join(c if c.isalnum() else "_" for c in character_name.lower())
    if slot is not None:
        return f"save_{safe_name}_slot{slot}.json"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"save_{safe_name}_{timestamp}.json"


def generate_save_id(character_name: str, slot: Optional[int] = None) -> str:
    """Generate a save ID (without .json extension)."""
    safe_name = "".join(c if c.isalnum() else "_" for c in character_name.lower())
    if slot is not None:
        return f"save_{safe_name}_slot{slot}"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"save_{safe_name}_{timestamp}"


def character_to_dict(character) -> Dict[str, Any]:
    """
    Convert a Character object to a dictionary for JSON serialization.
    
    This format is designed to be:
    - Sent via REST API to backend (Phase 5.4)
    - Stored in database (Phase 5.3)
    - Used by Flutter app (Phase 6)
    """
    return {
        # Basic Info
        'name': character.name,
        'race': character.race,
        'char_class': character.char_class,
        'level': character.level,
        
        # Ability Scores
        'strength': character.strength,
        'dexterity': character.dexterity,
        'constitution': character.constitution,
        'intelligence': character.intelligence,
        'wisdom': character.wisdom,
        'charisma': character.charisma,
        
        # Derived Stats
        'max_hp': character.max_hp,
        'current_hp': character.current_hp,
        'armor_class': character.armor_class,
        
        # Equipment
        'weapon': character.weapon,
        'equipped_armor': character.equipped_armor,
        
        # Inventory (serialize items)
        'inventory': [item_to_dict(item) for item in character.inventory],
        'gold': character.gold,
        
        # Experience
        'experience': character.experience,
    }


def item_to_dict(item) -> Dict[str, Any]:
    """Convert an Item object to a dictionary."""
    return {
        'name': item.name,
        'description': item.description,
        'item_type': item.item_type.value,  # Convert enum to string
        'rarity': item.rarity.value if hasattr(item, 'rarity') else 'common',
        'value': item.value,
        'stackable': item.stackable,
        'quantity': item.quantity,
        'damage_dice': item.damage_dice,
        'finesse': item.finesse if hasattr(item, 'finesse') else False,
        'ac_bonus': item.ac_bonus,
        'heal_amount': item.heal_amount if hasattr(item, 'heal_amount') else None,
        'effect': item.effect if hasattr(item, 'effect') else None,
    }


def dict_to_character(data: Dict[str, Any], Character) -> Any:
    """
    Reconstruct a Character from a dictionary with validation.
    
    Raises:
        SaveValidationError: If character data is invalid
    """
    from inventory import get_item, Item, ItemType
    
    # Validate first
    is_valid, errors = validate_character_data(data)
    if not is_valid:
        logger.warning(f"Character data validation warnings: {errors}")
        # Continue with defaults for missing fields, but log the issues
    
    try:
        # Create base character with core stats (with safe defaults)
        character = Character(
            name=str(data.get('name', 'Unknown Hero'))[:50],  # Limit name length
            race=str(data.get('race', 'Human')),
            char_class=str(data.get('char_class', 'Fighter')),
            level=max(1, min(5, int(data.get('level', 1)))),  # Clamp 1-5
            strength=max(1, min(30, int(data.get('strength', 10)))),  # Clamp 1-30
            dexterity=max(1, min(30, int(data.get('dexterity', 10)))),
            constitution=max(1, min(30, int(data.get('constitution', 10)))),
            intelligence=max(1, min(30, int(data.get('intelligence', 10)))),
            wisdom=max(1, min(30, int(data.get('wisdom', 10)))),
            charisma=max(1, min(30, int(data.get('charisma', 10)))),
        )
        
        # Override derived stats (don't recalculate) with validation
        max_hp = data.get('max_hp', character.max_hp)
        current_hp = data.get('current_hp', character.current_hp)
        
        character.max_hp = max(1, int(max_hp)) if max_hp else character.max_hp
        character.current_hp = min(character.max_hp, max(0, int(current_hp))) if current_hp else character.current_hp
        character.armor_class = max(0, int(data.get('armor_class', character.armor_class)))
        
        # Equipment
        character.weapon = str(data.get('weapon', 'longsword'))
        character.equipped_armor = str(data.get('equipped_armor', ''))
        
        # Gold (non-negative)
        character.gold = max(0, int(data.get('gold', 0)))
        
        # Experience (non-negative)
        character.experience = max(0, int(data.get('experience', 0)))
        
        # Reconstruct inventory with error tracking
        character.inventory = []
        inventory_errors = 0
        for i, item_data in enumerate(data.get('inventory', [])):
            try:
                item = dict_to_item(item_data)
                if item:
                    character.inventory.append(item)
            except Exception as e:
                inventory_errors += 1
                logger.warning(f"Could not restore inventory item {i}: {e}")
        
        if inventory_errors > 0:
            logger.warning(f"Skipped {inventory_errors} invalid inventory items")
        
        logger.info(f"Restored character: {character.name} (L{character.level} {character.char_class})")
        return character
        
    except Exception as e:
        logger.error(f"Failed to restore character: {e}")
        raise SaveValidationError("character", str(e))


def dict_to_item(data: Dict[str, Any]) -> Optional[Any]:
    """
    Reconstruct an Item from a dictionary with validation.
    
    Returns None if item cannot be restored, logs warning.
    """
    from inventory import Item, ItemType, Rarity
    
    if not isinstance(data, dict):
        logger.warning(f"Invalid item data type: {type(data)}")
        return None
    
    try:
        # Validate and sanitize item type
        item_type_str = str(data.get('item_type', 'misc')).lower()
        try:
            item_type = ItemType(item_type_str)
        except ValueError:
            logger.warning(f"Unknown item type '{item_type_str}', defaulting to misc")
            item_type = ItemType.MISC
        
        # Validate and sanitize rarity
        rarity_str = str(data.get('rarity', 'common')).lower()
        try:
            rarity = Rarity(rarity_str)
        except ValueError:
            logger.warning(f"Unknown rarity '{rarity_str}', defaulting to common")
            rarity = Rarity.COMMON
        
        return Item(
            name=str(data.get('name', 'Unknown Item'))[:100],  # Limit name length
            item_type=item_type,
            description=str(data.get('description', ''))[:500],  # Limit description
            rarity=rarity,
            value=max(0, int(data.get('value', 0))),  # Non-negative
            stackable=bool(data.get('stackable', False)),
            quantity=max(1, int(data.get('quantity', 1))),  # At least 1
            damage_dice=data.get('damage_dice'),
            finesse=bool(data.get('finesse', False)),
            ac_bonus=data.get('ac_bonus'),
            heal_amount=data.get('heal_amount'),
            effect=data.get('effect'),
        )
    except Exception as e:
        logger.warning(f"Could not restore item '{data.get('name', 'unknown')}': {e}")
        return None


def scenario_to_dict(scenario_manager) -> Optional[Dict[str, Any]]:
    """
    Serialize scenario state for full game continuity.
    
    Captures:
    - Current scenario ID and completion state
    - Current scene ID
    - All scene states (exchange_count, objectives_complete, status)
    - Location manager state (current location, visited locations)
    
    This allows resuming a game mid-scenario at the exact point.
    """
    if not scenario_manager or not scenario_manager.active_scenario:
        return None
    
    scenario = scenario_manager.active_scenario
    
    # Serialize individual scene states
    scene_states = {}
    for scene_id, scene in scenario.scenes.items():
        scene_states[scene_id] = {
            'status': scene.status.value,  # SceneStatus enum to string
            'exchange_count': scene.exchange_count,
            'objectives_complete': list(scene.objectives_complete),
        }
    
    # Serialize location manager state (Phase 3.2)
    location_state = None
    if scenario.location_manager:
        location_state = scenario.location_manager.to_dict()
    
    return {
        'id': scenario.id,
        'current_scene_id': scenario.current_scene_id,
        'is_complete': scenario.is_complete,
        'scene_states': scene_states,
        'location_state': location_state,  # Phase 3.2
    }


def restore_scenario(scenario_manager, data: Dict[str, Any]) -> bool:
    """
    Restore scenario state from saved data for full game continuity.
    
    Restores:
    - Scenario completion state
    - Current scene ID
    - All scene states (exchange_count, objectives_complete, status)
    - Location manager state (current location, visited locations)
    """
    from scenario import SceneStatus
    
    if not data or not scenario_manager:
        return False
    
    scenario_id = data.get('id')
    if not scenario_id:
        return False
    
    # Start the scenario (this creates fresh scene objects)
    try:
        scenario_manager.start_scenario(scenario_id)
    except Exception:
        return False
    
    if not scenario_manager.active_scenario:
        return False
    
    # Restore scenario-level state
    scenario = scenario_manager.active_scenario
    scenario.current_scene_id = data.get('current_scene_id')
    scenario.is_complete = data.get('is_complete', False)
    
    # Restore individual scene states
    scene_states = data.get('scene_states', {})
    for scene_id, state in scene_states.items():
        if scene_id in scenario.scenes:
            scene = scenario.scenes[scene_id]
            # Restore status enum
            status_str = state.get('status', 'locked')
            try:
                scene.status = SceneStatus(status_str)
            except ValueError:
                scene.status = SceneStatus.LOCKED
            # Restore progress
            scene.exchange_count = state.get('exchange_count', 0)
            scene.objectives_complete = state.get('objectives_complete', [])
    
    # Restore location manager state (Phase 3.2)
    location_state = data.get('location_state')
    if location_state and scenario.location_manager:
        scenario.location_manager.restore_state(location_state)
    
    return True


class SaveManager:
    """
    Manages save/load operations for the game with comprehensive error handling.
    
    Provides:
    - Atomic saves (temp file + rename)
    - Validation before save/load
    - Detailed error messages with recovery hints
    - Logging for debugging
    """
    
    def __init__(self, saves_dir: Optional[str] = None):
        self.saves_dir = saves_dir or SAVES_DIR
        self._error_log: List[str] = []  # Track errors for debugging
        ensure_saves_dir()
    
    def get_last_errors(self) -> List[str]:
        """Get list of errors from recent operations."""
        return self._error_log.copy()
    
    def clear_errors(self) -> None:
        """Clear the error log."""
        self._error_log = []
    
    def save_game(
        self,
        character,
        scenario_manager=None,
        chat_history: Optional[list] = None,
        slot: Optional[int] = None,
        description: str = "",
        game_stats: Optional[Dict[str, Any]] = None
    ) -> Tuple[str, str]:
        """
        Save the current game state to a JSON file for full continuity.
        
        Args:
            character: The player's Character object
            scenario_manager: ScenarioManager with active scenario (optional)
            chat_history: List of chat messages for context (optional)
            slot: Save slot number (1-5) or None for timestamped save
            description: Optional description for the save
            game_stats: Optional game statistics (enemies_defeated, etc.)
            
        Returns:
            Tuple of (filepath: str, message: str)
            - filepath is empty string on failure
            - message describes success or error
            
        Raises:
            SavePermissionError: If no write permission
            SaveDiskSpaceError: If disk is full
            SaveValidationError: If character data is invalid
        """
        self.clear_errors()
        
        # Validate character data
        if character is None:
            error = "Cannot save: No character provided"
            self._error_log.append(error)
            logger.error(error)
            return ("", error)
        
        try:
            # Validate character before serialization
            char_dict = character_to_dict(character)
            is_valid, errors = validate_character_data(char_dict)
            if not is_valid:
                for e in errors:
                    self._error_log.append(f"Validation: {e}")
                logger.warning(f"Character validation warnings: {errors}")
                # Continue anyway - these are warnings not blockers
            
            # Get scenario info for auto-description
            scenario_info = ""
            if scenario_manager and scenario_manager.active_scenario:
                scene = scenario_manager.active_scenario.get_current_scene()
                if scene:
                    scenario_info = f" - {scene.name}"
            
            # Auto-generate description if empty
            if not description and character:
                description = f"L{character.level} {character.char_class}, {character.current_hp}/{character.max_hp} HP{scenario_info}"
            
            save_data = {
                # Metadata
                'version': SAVE_VERSION,
                'timestamp': datetime.now().isoformat(),
                'description': description,
                
                # Character data (complete state)
                'character': char_dict,
                
                # Scenario data (complete with scene states)
                'scenario': scenario_to_dict(scenario_manager),
                
                # Chat history (expanded to 50 messages for better AI context)
                'chat_history': chat_history[-50:] if chat_history else [],
                
                # Game statistics for progress tracking
                'game_stats': game_stats or {
                    'enemies_defeated': 0,
                    'gold_earned': 0,
                    'items_found': 0,
                    'skill_checks_passed': 0,
                    'skill_checks_failed': 0,
                },
            }
            
            # Generate filename and paths
            filename = generate_save_filename(character.name, slot)
            filepath = os.path.join(self.saves_dir, filename)
            temp_filepath = filepath + ".tmp"
            
            # Write to temp file first (atomic save)
            try:
                with open(temp_filepath, 'w', encoding='utf-8') as f:
                    json.dump(save_data, f, indent=2, ensure_ascii=False)
            except PermissionError:
                raise SavePermissionError("write", temp_filepath)
            except OSError as e:
                if e.errno == 28:  # No space left
                    raise SaveDiskSpaceError()
                raise
            
            # Rename temp to final (atomic operation)
            try:
                if os.path.exists(filepath):
                    os.replace(temp_filepath, filepath)
                else:
                    os.rename(temp_filepath, filepath)
            except Exception as e:
                # Clean up temp file
                if os.path.exists(temp_filepath):
                    try:
                        os.remove(temp_filepath)
                    except:
                        pass
                raise
            
            logger.info(f"Saved game to: {filepath}")
            return (filepath, f"💾 Game saved: {filename}")
            
        except (SavePermissionError, SaveDiskSpaceError, SaveValidationError):
            raise
        except Exception as e:
            error = f"❌ Error saving game: {e}"
            self._error_log.append(error)
            logger.error(error)
            return ("", error)
    
    def load_game(self, filepath: str, Character, ScenarioManager=None) -> Optional[Dict[str, Any]]:
        """
        Load a game from a JSON file for full continuity.
        
        Args:
            filepath: Path to the save file
            Character: Character class to instantiate
            ScenarioManager: ScenarioManager class to instantiate (optional)
            
        Returns:
            Dict with keys: 'character', 'scenario_manager', 'chat_history', 
            'game_stats', 'errors', or None on critical error
            
        Raises:
            SaveFileNotFoundError: If file doesn't exist
            SaveFileCorruptedError: If file is invalid JSON
            SaveVersionMismatchError: If version is incompatible
        """
        self.clear_errors()
        
        try:
            # Check file exists
            if not os.path.exists(filepath):
                raise SaveFileNotFoundError(filepath)
            
            # Read and parse JSON
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    save_data = json.load(f)
            except json.JSONDecodeError as e:
                raise SaveFileCorruptedError(filepath, f"Invalid JSON at line {e.lineno}")
            except PermissionError:
                raise SavePermissionError("read", filepath)
            
            # Validate save structure
            is_valid, errors = validate_save_data(save_data)
            if not is_valid:
                # Log warnings but continue if possible
                for e in errors:
                    self._error_log.append(f"Validation: {e}")
                logger.warning(f"Save validation warnings: {errors}")
            
            # Version check
            file_version = save_data.get('version', '1.0')
            if file_version not in SUPPORTED_VERSIONS:
                raise SaveVersionMismatchError(file_version, SAVE_VERSION)
            
            result = {
                'character': None,
                'scenario_manager': None,
                'chat_history': [],
                'description': save_data.get('description', ''),
                'timestamp': save_data.get('timestamp', ''),
                'game_stats': save_data.get('game_stats', {
                    'enemies_defeated': 0,
                    'gold_earned': 0,
                    'items_found': 0,
                    'skill_checks_passed': 0,
                    'skill_checks_failed': 0,
                }),
                'version': file_version,
                'errors': [],  # Track non-fatal errors
            }
            
            # Restore character
            char_data = save_data.get('character')
            if char_data:
                try:
                    result['character'] = dict_to_character(char_data, Character)
                except SaveValidationError as e:
                    result['errors'].append(f"Character: {e.message}")
                    logger.error(f"Failed to restore character: {e}")
            else:
                result['errors'].append("No character data in save file")
            
            # Restore scenario
            scenario_data = save_data.get('scenario')
            if scenario_data and ScenarioManager:
                try:
                    scenario_manager = ScenarioManager()
                    if restore_scenario(scenario_manager, scenario_data):
                        result['scenario_manager'] = scenario_manager
                    else:
                        result['errors'].append("Failed to restore scenario progress")
                except Exception as e:
                    result['errors'].append(f"Scenario: {e}")
                    logger.warning(f"Failed to restore scenario: {e}")
            
            # Restore chat history
            result['chat_history'] = save_data.get('chat_history', [])
            
            # Log any errors
            if result['errors']:
                for e in result['errors']:
                    self._error_log.append(e)
            
            logger.info(f"Loaded game from: {filepath} (v{file_version})")
            return result
            
        except (SaveFileNotFoundError, SaveFileCorruptedError, 
                SaveVersionMismatchError, SavePermissionError):
            raise
        except Exception as e:
            error = f"❌ Error loading game: {e}"
            self._error_log.append(error)
            logger.error(error)
            return None
    
    def list_saves(self) -> Tuple[List[Dict[str, Any]], List[str]]:
        """
        List all available save files with error tracking.
        
        Returns:
            Tuple of (saves: List[Dict], errors: List[str])
            - saves: List of valid save file metadata
            - errors: List of warning messages for problematic files
        """
        saves = []
        errors = []
        
        try:
            if not os.path.exists(self.saves_dir):
                return ([], ["No saves directory found"])
            
            for filename in os.listdir(self.saves_dir):
                if filename.endswith('.json') and filename.startswith('save_'):
                    filepath = os.path.join(self.saves_dir, filename)
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                        
                        # Validate minimum structure
                        if 'character' not in data:
                            errors.append(f"⚠️ {filename}: Missing character data (skipped)")
                            continue
                        
                        saves.append({
                            'filename': filename,
                            'filepath': filepath,
                            'timestamp': data.get('timestamp', 'Unknown'),
                            'version': data.get('version', '1.0'),
                            'character_name': data.get('character', {}).get('name', 'Unknown'),
                            'character_level': data.get('character', {}).get('level', 1),
                            'character_class': data.get('character', {}).get('char_class', 'Unknown'),
                            'description': data.get('description', ''),
                            'has_scenario': data.get('scenario') is not None,
                        })
                    except json.JSONDecodeError as e:
                        errors.append(f"⚠️ {filename}: Corrupted JSON (line {e.lineno})")
                        logger.warning(f"Corrupted save: {filename} - {e}")
                    except PermissionError:
                        errors.append(f"⚠️ {filename}: Permission denied")
                    except Exception as e:
                        errors.append(f"⚠️ {filename}: Cannot read ({e})")
                        logger.warning(f"Cannot read save: {filename} - {e}")
            
            # Sort by timestamp (newest first)
            saves.sort(key=lambda x: x['timestamp'], reverse=True)
            
        except PermissionError:
            errors.append("Permission denied reading saves directory")
            logger.error(f"Permission denied listing saves: {self.saves_dir}")
        except Exception as e:
            errors.append(f"Error listing saves: {e}")
            logger.error(f"Error listing saves: {e}")
        
        return (saves, errors)
    
    def delete_save(self, filepath: str) -> Tuple[bool, str]:
        """
        Delete a save file with error handling.
        
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            if not os.path.exists(filepath):
                return (False, f"Save file not found: {os.path.basename(filepath)}")
            
            os.remove(filepath)
            logger.info(f"Deleted save: {filepath}")
            return (True, f"🗑️ Save deleted: {os.path.basename(filepath)}")
            
        except PermissionError:
            return (False, "Permission denied. Cannot delete save file.")
        except Exception as e:
            logger.error(f"Error deleting save: {e}")
            return (False, f"Error deleting save: {e}")
    
    def get_quick_save_path(self, character_name: str) -> str:
        """Get the path for quick save (slot 0)."""
        filename = generate_save_filename(character_name, 0)
        return os.path.join(self.saves_dir, filename)


def format_saves_list(saves: list, errors: Optional[List[str]] = None) -> str:
    """
    Format the saves list for display.
    
    Args:
        saves: List of save metadata dicts
        errors: Optional list of error messages to display
    """
    lines = []
    
    if not saves:
        lines.append("📂 No saved games found.")
    else:
        lines.append("📂 SAVED GAMES")
        lines.append("=" * 50)
        
        for i, save in enumerate(saves, 1):
            timestamp = save['timestamp'][:16].replace('T', ' ') if save.get('timestamp') else 'Unknown'
            char_info = f"{save['character_name']} (L{save['character_level']} {save['character_class']})"
            desc = f" - {save['description']}" if save.get('description') else ""
            
            lines.append(f"  [{i}] {char_info}")
            lines.append(f"      Saved: {timestamp}{desc}")
        
        lines.append("=" * 50)
    
    # Show any errors/warnings
    if errors:
        lines.append("")
        lines.append("⚠️ Issues detected:")
        for err in errors[:5]:  # Limit to 5 errors
            lines.append(f"  {err}")
        if len(errors) > 5:
            lines.append(f"  ... and {len(errors) - 5} more")
    
    return "\n".join(lines)


def quick_save(character, scenario_manager=None, chat_history=None) -> Tuple[bool, str]:
    """
    Quick save the current game state.
    
    Returns:
        Tuple of (success: bool, message: str)
    """
    if not character:
        return (False, "❌ No character to save")
    
    try:
        manager = SaveManager()
        filepath, message = manager.save_game(
            character,
            scenario_manager,
            chat_history,
            slot=0,
            description="Quick Save"
        )
        if filepath:
            return (True, f"💾 Game saved: {os.path.basename(filepath)}")
        return (False, message)
    except SaveSystemError as e:
        return (False, str(e))
    except Exception as e:
        logger.error(f"Quick save failed: {e}")
        return (False, f"❌ Save failed: {e}")


def quick_load(Character, ScenarioManager=None) -> Tuple[Optional[Dict[str, Any]], str]:
    """
    Quick load the most recent save for any character.
    
    Returns:
        Tuple of (result: Optional[Dict], message: str)
    """
    try:
        manager = SaveManager()
        saves, errors = manager.list_saves()
        
        if not saves:
            return (None, "❌ No saves found.")
        
        # Load the most recent save
        result = manager.load_game(saves[0]['filepath'], Character, ScenarioManager)
        if result and result.get('character'):
            char = result['character']
            return (result, f"✅ Loaded: {char.name} (L{char.level} {char.char_class})")
        return (None, "❌ Failed to load save")
        
    except SaveFileNotFoundError as e:
        return (None, str(e))
    except SaveFileCorruptedError as e:
        return (None, str(e))
    except SaveVersionMismatchError as e:
        return (None, str(e))
    except Exception as e:
        logger.error(f"Quick load failed: {e}")
        return (None, f"❌ Load failed: {e}")
