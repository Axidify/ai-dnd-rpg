"""
Quest System for AI D&D Text RPG (Phase 3.3, Step 3.3.4)
Handles quest tracking, objectives, and rewards.

FEATURES:
- Quest dataclass with objectives and rewards
- QuestObjective dataclass with progress tracking
- ObjectiveType enum for different objective kinds
- QuestStatus enum for quest state
- QuestManager class for quest lifecycle
- Integration hooks for combat, inventory, location, NPC systems
"""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, List, Optional, Any, Callable


# =============================================================================
# ENUMS
# =============================================================================

class QuestStatus(Enum):
    """Status of a quest in the player's quest log."""
    NOT_STARTED = auto()  # Quest exists but not accepted
    ACTIVE = auto()       # Quest accepted, in progress
    COMPLETE = auto()     # All objectives done, rewards given
    FAILED = auto()       # Quest failed (time limit, wrong choice, etc.)


class QuestType(Enum):
    """Type/importance of a quest for disposition rewards."""
    MAIN = auto()    # Main story quest (+25 disposition on complete)
    SIDE = auto()    # Side quest (+15 disposition on complete)
    MINOR = auto()   # Minor/fetch quest (+10 disposition on complete)


class ObjectiveType(Enum):
    """Types of quest objectives."""
    KILL = auto()           # Defeat specific enemy type
    FIND_ITEM = auto()      # Pick up a specific item
    TALK_TO = auto()        # Speak with an NPC
    REACH_LOCATION = auto() # Arrive at a location
    COLLECT = auto()        # Gather multiple of an item type
    CUSTOM = auto()         # Custom objective (manually completed)


# =============================================================================
# QUEST OBJECTIVE DATACLASS
# =============================================================================

@dataclass
class QuestObjective:
    """
    Represents a single objective within a quest.
    
    Attributes:
        id: Unique identifier (e.g., "kill_goblins_5")
        description: Human-readable description
        objective_type: Type of objective (KILL, FIND_ITEM, etc.)
        target: The target ID (enemy_id, item_id, npc_id, location_id)
        required_count: How many needed to complete (default 1)
        current_count: Current progress toward required_count
        completed: Whether this objective is done
        optional: If True, not required for quest completion
        hidden: If True, not shown until discovered
    """
    id: str
    description: str
    objective_type: ObjectiveType
    target: str
    required_count: int = 1
    current_count: int = 0
    completed: bool = False
    optional: bool = False
    hidden: bool = False
    
    def __post_init__(self):
        """Validate objective data."""
        if not self.id:
            raise ValueError("QuestObjective must have an id")
        if not self.description:
            raise ValueError("QuestObjective must have a description")
        if self.required_count < 1:
            raise ValueError("required_count must be at least 1")
    
    def update_progress(self, count: int = 1) -> bool:
        """
        Add progress toward this objective.
        
        Args:
            count: Amount to add (default 1)
        
        Returns:
            True if objective was just completed, False otherwise
        """
        if self.completed:
            return False
        
        self.current_count = min(self.current_count + count, self.required_count)
        
        if self.current_count >= self.required_count:
            self.completed = True
            return True
        return False
    
    def get_progress_string(self) -> str:
        """Get a formatted progress string like '3/5' or 'Complete'."""
        if self.completed:
            return "✓ Complete"
        return f"{self.current_count}/{self.required_count}"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert objective to dictionary for saving."""
        return {
            "id": self.id,
            "description": self.description,
            "objective_type": self.objective_type.name,
            "target": self.target,
            "required_count": self.required_count,
            "current_count": self.current_count,
            "completed": self.completed,
            "optional": self.optional,
            "hidden": self.hidden
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'QuestObjective':
        """Create objective from dictionary (for loading)."""
        return cls(
            id=data["id"],
            description=data["description"],
            objective_type=ObjectiveType[data["objective_type"]],
            target=data["target"],
            required_count=data.get("required_count", 1),
            current_count=data.get("current_count", 0),
            completed=data.get("completed", False),
            optional=data.get("optional", False),
            hidden=data.get("hidden", False)
        )


# =============================================================================
# QUEST DATACLASS
# =============================================================================

@dataclass
class Quest:
    """
    Represents a quest that the player can accept and complete.
    
    Attributes:
        id: Unique identifier (e.g., "rescue_lily_main")
        name: Display name (e.g., "Rescue Lily Greenfield")
        description: Story context and goal description
        giver_npc_id: ID of NPC who gives this quest
        quest_type: Quest importance (MAIN, SIDE, MINOR) - affects disposition reward
        status: Current quest status
        objectives: List of objectives to complete
        rewards: Dict of rewards (gold, xp, items)
        prerequisites: Quest IDs that must be complete first
        time_limit: Turns before auto-fail (None = unlimited)
        turns_remaining: Countdown for time-limited quests
        on_accept_dialogue: NPC dialogue when accepting
        on_complete_dialogue: NPC dialogue when turning in
        on_fail_dialogue: NPC dialogue if quest fails
    """
    id: str
    name: str
    description: str
    giver_npc_id: str = ""
    quest_type: QuestType = QuestType.SIDE
    status: QuestStatus = QuestStatus.NOT_STARTED
    objectives: List[QuestObjective] = field(default_factory=list)
    rewards: Dict[str, Any] = field(default_factory=dict)
    prerequisites: List[str] = field(default_factory=list)
    time_limit: Optional[int] = None
    turns_remaining: Optional[int] = None
    on_accept_dialogue: str = ""
    on_complete_dialogue: str = ""
    on_fail_dialogue: str = ""
    
    def __post_init__(self):
        """Validate quest data."""
        if not self.id:
            raise ValueError("Quest must have an id")
        if not self.name:
            raise ValueError("Quest must have a name")
        if self.time_limit is not None and self.turns_remaining is None:
            self.turns_remaining = self.time_limit
    
    # =========================================================================
    # STATUS MANAGEMENT
    # =========================================================================
    
    def accept(self) -> bool:
        """
        Accept this quest, setting it to ACTIVE.
        
        Returns:
            True if quest was accepted, False if already active/complete/failed
        """
        if self.status != QuestStatus.NOT_STARTED:
            return False
        self.status = QuestStatus.ACTIVE
        return True
    
    def fail(self) -> bool:
        """
        Fail this quest.
        
        Returns:
            True if quest was failed, False if not active
        """
        if self.status != QuestStatus.ACTIVE:
            return False
        self.status = QuestStatus.FAILED
        return True
    
    def is_ready_to_complete(self) -> bool:
        """Check if all required objectives are done."""
        for obj in self.objectives:
            if not obj.optional and not obj.completed:
                return False
        return True
    
    def complete(self) -> bool:
        """
        Complete this quest (call after giving rewards).
        
        Returns:
            True if quest was completed, False if not ready
        """
        if self.status != QuestStatus.ACTIVE:
            return False
        if not self.is_ready_to_complete():
            return False
        self.status = QuestStatus.COMPLETE
        return True
    
    # =========================================================================
    # OBJECTIVE MANAGEMENT
    # =========================================================================
    
    def add_objective(self, objective: QuestObjective):
        """Add an objective to this quest."""
        self.objectives.append(objective)
    
    def get_objective(self, objective_id: str) -> Optional[QuestObjective]:
        """Get an objective by ID."""
        for obj in self.objectives:
            if obj.id == objective_id:
                return obj
        return None
    
    def check_objective(self, objective_type: ObjectiveType, target: str, count: int = 1) -> List[QuestObjective]:
        """
        Check and update objectives matching the given type and target.
        
        Args:
            objective_type: Type of action (KILL, FIND_ITEM, etc.)
            target: Target ID that was acted upon
            count: Progress to add (default 1)
        
        Returns:
            List of objectives that were just completed
        """
        if self.status != QuestStatus.ACTIVE:
            return []
        
        completed = []
        for obj in self.objectives:
            if obj.objective_type == objective_type and obj.target == target:
                if obj.update_progress(count):
                    completed.append(obj)
        return completed
    
    def get_required_objectives(self) -> List[QuestObjective]:
        """Get all required (non-optional) objectives."""
        return [obj for obj in self.objectives if not obj.optional]
    
    def get_visible_objectives(self) -> List[QuestObjective]:
        """Get all visible (non-hidden) objectives."""
        return [obj for obj in self.objectives if not obj.hidden]
    
    def get_completion_percentage(self) -> float:
        """Get percentage of required objectives completed."""
        required = self.get_required_objectives()
        if not required:
            return 100.0
        completed = sum(1 for obj in required if obj.completed)
        return (completed / len(required)) * 100
    
    # =========================================================================
    # TIME MANAGEMENT
    # =========================================================================
    
    def tick_time(self) -> bool:
        """
        Advance time by one turn for time-limited quests.
        
        Returns:
            True if quest just failed due to time, False otherwise
        """
        if self.turns_remaining is None or self.status != QuestStatus.ACTIVE:
            return False
        
        self.turns_remaining -= 1
        if self.turns_remaining <= 0:
            self.fail()
            return True
        return False
    
    # =========================================================================
    # DISPLAY
    # =========================================================================
    
    def get_summary(self) -> str:
        """Get a one-line summary for quest list display."""
        status_icons = {
            QuestStatus.NOT_STARTED: "○",
            QuestStatus.ACTIVE: "◉",
            QuestStatus.COMPLETE: "✓",
            QuestStatus.FAILED: "✗"
        }
        icon = status_icons[self.status]
        progress = f"({int(self.get_completion_percentage())}%)" if self.status == QuestStatus.ACTIVE else ""
        return f"{icon} {self.name} {progress}"
    
    def get_detailed_display(self) -> str:
        """Get detailed quest information for quest details view."""
        lines = [
            f"╔{'═' * 58}╗",
            f"║ 📜 {self.name:<54} ║",
            f"╠{'═' * 58}╣",
        ]
        
        # Description (word wrap at 54 chars)
        desc_lines = []
        words = self.description.split()
        current_line = ""
        for word in words:
            if len(current_line) + len(word) + 1 <= 54:
                current_line = f"{current_line} {word}".strip()
            else:
                desc_lines.append(current_line)
                current_line = word
        if current_line:
            desc_lines.append(current_line)
        
        for line in desc_lines:
            lines.append(f"║ {line:<56} ║")
        
        lines.append(f"╠{'═' * 58}╣")
        lines.append(f"║ {'OBJECTIVES:':<56} ║")
        
        for obj in self.get_visible_objectives():
            prefix = "  ○" if not obj.completed else "  ✓"
            optional_tag = " (optional)" if obj.optional else ""
            progress = f" [{obj.get_progress_string()}]" if obj.required_count > 1 else ""
            obj_line = f"{prefix} {obj.description}{optional_tag}{progress}"
            # Truncate if too long
            if len(obj_line) > 56:
                obj_line = obj_line[:53] + "..."
            lines.append(f"║ {obj_line:<56} ║")
        
        # Rewards
        if self.rewards:
            lines.append(f"╠{'═' * 58}╣")
            lines.append(f"║ {'REWARDS:':<56} ║")
            reward_parts = []
            if "gold" in self.rewards:
                reward_parts.append(f"{self.rewards['gold']}g")
            if "xp" in self.rewards:
                reward_parts.append(f"{self.rewards['xp']} XP")
            if "items" in self.rewards:
                reward_parts.append(f"{len(self.rewards['items'])} item(s)")
            reward_str = ", ".join(reward_parts)
            lines.append(f"║   💰 {reward_str:<52} ║")
        
        # Time limit
        if self.turns_remaining is not None and self.status == QuestStatus.ACTIVE:
            lines.append(f"╠{'═' * 58}╣")
            lines.append(f"║ ⏰ Time Remaining: {self.turns_remaining} turns{' ' * 32} ║")
        
        lines.append(f"╚{'═' * 58}╝")
        return "\n".join(lines)
    
    # =========================================================================
    # SERIALIZATION
    # =========================================================================
    
    def get_disposition_reward(self) -> int:
        """Get disposition reward for completing this quest based on type."""
        if self.quest_type == QuestType.MAIN:
            return 25
        elif self.quest_type == QuestType.SIDE:
            return 15
        else:  # MINOR
            return 10
    
    def get_disposition_penalty(self) -> int:
        """Get disposition penalty for failing this quest based on type."""
        if self.quest_type == QuestType.MAIN:
            return -15
        elif self.quest_type == QuestType.SIDE:
            return -10
        else:  # MINOR
            return -5
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert quest to dictionary for saving."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "giver_npc_id": self.giver_npc_id,
            "quest_type": self.quest_type.name,
            "status": self.status.name,
            "objectives": [obj.to_dict() for obj in self.objectives],
            "rewards": self.rewards.copy(),
            "prerequisites": self.prerequisites.copy(),
            "time_limit": self.time_limit,
            "turns_remaining": self.turns_remaining,
            "on_accept_dialogue": self.on_accept_dialogue,
            "on_complete_dialogue": self.on_complete_dialogue,
            "on_fail_dialogue": self.on_fail_dialogue
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Quest':
        """Create quest from dictionary (for loading)."""
        quest = cls(
            id=data["id"],
            name=data["name"],
            description=data["description"],
            giver_npc_id=data.get("giver_npc_id", ""),
            quest_type=QuestType[data.get("quest_type", "SIDE")],
            status=QuestStatus[data.get("status", "NOT_STARTED")],
            rewards=data.get("rewards", {}),
            prerequisites=data.get("prerequisites", []),
            time_limit=data.get("time_limit"),
            turns_remaining=data.get("turns_remaining"),
            on_accept_dialogue=data.get("on_accept_dialogue", ""),
            on_complete_dialogue=data.get("on_complete_dialogue", ""),
            on_fail_dialogue=data.get("on_fail_dialogue", "")
        )
        # Load objectives
        for obj_data in data.get("objectives", []):
            quest.objectives.append(QuestObjective.from_dict(obj_data))
        return quest


# =============================================================================
# QUEST MANAGER
# =============================================================================

class QuestManager:
    """
    Manages the player's quest log and quest lifecycle.
    
    Tracks active, completed, and failed quests.
    Provides methods for quest operations and objective checking.
    """
    
    def __init__(self):
        """Initialize empty quest manager."""
        self.available_quests: Dict[str, Quest] = {}  # Quest definitions
        self.active_quests: Dict[str, Quest] = {}     # Currently active quests
        self.completed_quests: List[str] = []         # Quest IDs completed
        self.failed_quests: List[str] = []            # Quest IDs failed
        self._objective_callbacks: List[Callable] = []  # Callbacks for objective completion
    
    # =========================================================================
    # QUEST REGISTRATION
    # =========================================================================
    
    def register_quest(self, quest: Quest):
        """
        Register a quest as available to accept.
        
        Args:
            quest: Quest definition to register
        """
        self.available_quests[quest.id] = quest
    
    def get_available_quest(self, quest_id: str) -> Optional[Quest]:
        """Get an available (not yet accepted) quest by ID."""
        return self.available_quests.get(quest_id)
    
    def get_available_quests_for_npc(self, npc_id: str) -> List[Quest]:
        """Get all available quests from a specific NPC."""
        quests = []
        for quest in self.available_quests.values():
            if quest.giver_npc_id == npc_id:
                if quest.id not in self.active_quests:
                    if quest.id not in self.completed_quests:
                        if quest.id not in self.failed_quests:
                            # Check prerequisites
                            prereqs_met = all(
                                prereq in self.completed_quests 
                                for prereq in quest.prerequisites
                            )
                            if prereqs_met:
                                quests.append(quest)
        return quests
    
    # =========================================================================
    # QUEST LIFECYCLE
    # =========================================================================
    
    def accept_quest(self, quest_id: str) -> Optional[Quest]:
        """
        Accept a quest, moving it from available to active.
        
        Args:
            quest_id: ID of quest to accept
        
        Returns:
            The accepted Quest object, or None if not available
        """
        if quest_id not in self.available_quests:
            return None
        if quest_id in self.active_quests:
            return None
        if quest_id in self.completed_quests or quest_id in self.failed_quests:
            return None
        
        quest = self.available_quests[quest_id]
        
        # Check prerequisites
        for prereq in quest.prerequisites:
            if prereq not in self.completed_quests:
                return None
        
        # Create a copy for tracking (keep original for re-acceptance after fail)
        import copy
        active_quest = copy.deepcopy(quest)
        active_quest.accept()
        self.active_quests[quest_id] = active_quest
        return active_quest
    
    def complete_quest(self, quest_id: str) -> Optional[tuple]:
        """
        Complete a quest and return its rewards and quest data.
        
        Args:
            quest_id: ID of quest to complete
        
        Returns:
            Tuple of (rewards dict, quest object) if successful, None if not ready.
            The quest object is returned for disposition handling (giver_npc_id, quest_type).
        """
        if quest_id not in self.active_quests:
            return None
        
        quest = self.active_quests[quest_id]
        if not quest.is_ready_to_complete():
            return None
        
        rewards = quest.rewards.copy()
        quest.complete()
        self.completed_quests.append(quest_id)
        del self.active_quests[quest_id]
        return (rewards, quest)
    
    def fail_quest(self, quest_id: str) -> bool:
        """
        Fail a quest.
        
        Args:
            quest_id: ID of quest to fail
        
        Returns:
            True if failed, False if not active
        """
        if quest_id not in self.active_quests:
            return False
        
        quest = self.active_quests[quest_id]
        quest.fail()
        self.failed_quests.append(quest_id)
        del self.active_quests[quest_id]
        return True
    
    def abandon_quest(self, quest_id: str) -> bool:
        """
        Abandon a quest (can be re-accepted later).
        
        Args:
            quest_id: ID of quest to abandon
        
        Returns:
            True if abandoned, False if not active
        """
        if quest_id not in self.active_quests:
            return False
        
        del self.active_quests[quest_id]
        return True
    
    # =========================================================================
    # OBJECTIVE TRACKING
    # =========================================================================
    
    def check_objective(self, objective_type: ObjectiveType, target: str, count: int = 1) -> List[tuple]:
        """
        Check all active quests for matching objectives.
        
        Args:
            objective_type: Type of action (KILL, FIND_ITEM, etc.)
            target: Target ID that was acted upon
            count: Progress to add (default 1)
        
        Returns:
            List of (quest_id, objective) tuples for newly completed objectives
        """
        completed = []
        for quest_id, quest in self.active_quests.items():
            quest_completed = quest.check_objective(objective_type, target, count)
            for obj in quest_completed:
                completed.append((quest_id, obj))
                # Trigger callbacks
                for callback in self._objective_callbacks:
                    callback(quest_id, obj)
        return completed
    
    def on_enemy_killed(self, enemy_id: str, count: int = 1) -> List[tuple]:
        """Hook for combat system - enemy defeated."""
        return self.check_objective(ObjectiveType.KILL, enemy_id, count)
    
    def on_item_acquired(self, item_id: str, count: int = 1) -> List[tuple]:
        """Hook for inventory system - item picked up."""
        results = self.check_objective(ObjectiveType.FIND_ITEM, item_id, count)
        results.extend(self.check_objective(ObjectiveType.COLLECT, item_id, count))
        return results
    
    def on_location_entered(self, location_id: str) -> List[tuple]:
        """Hook for location system - arrived at location."""
        return self.check_objective(ObjectiveType.REACH_LOCATION, location_id, 1)
    
    def on_npc_talked(self, npc_id: str) -> List[tuple]:
        """Hook for dialogue system - talked to NPC."""
        return self.check_objective(ObjectiveType.TALK_TO, npc_id, 1)
    
    def register_objective_callback(self, callback: Callable):
        """Register a callback to be called when objectives complete."""
        self._objective_callbacks.append(callback)
    
    # =========================================================================
    # TIME MANAGEMENT
    # =========================================================================
    
    def tick_all_quests(self) -> List[str]:
        """
        Advance time for all time-limited quests.
        
        Returns:
            List of quest IDs that just failed due to time
        """
        failed = []
        for quest_id in list(self.active_quests.keys()):
            quest = self.active_quests[quest_id]
            if quest.tick_time():
                self.failed_quests.append(quest_id)
                del self.active_quests[quest_id]
                failed.append(quest_id)
        return failed
    
    # =========================================================================
    # QUERIES
    # =========================================================================
    
    def get_quest(self, quest_id: str) -> Optional[Quest]:
        """Get any quest by ID (active, available, or from history)."""
        if quest_id in self.active_quests:
            return self.active_quests[quest_id]
        if quest_id in self.available_quests:
            return self.available_quests[quest_id]
        return None
    
    def get_active_quests(self) -> List[Quest]:
        """Get all currently active quests."""
        return list(self.active_quests.values())
    
    def get_completed_quests(self) -> List[Dict[str, Any]]:
        """Get list of completed quest info dicts (IDs only, quests are no longer stored)."""
        return [{"id": qid, "status": "completed"} for qid in self.completed_quests]
    
    def get_ready_to_complete(self) -> List[Quest]:
        """Get all active quests ready to be turned in."""
        return [q for q in self.active_quests.values() if q.is_ready_to_complete()]
    
    def is_quest_complete(self, quest_id: str) -> bool:
        """Check if a quest has been completed."""
        return quest_id in self.completed_quests
    
    def is_quest_failed(self, quest_id: str) -> bool:
        """Check if a quest has been failed."""
        return quest_id in self.failed_quests
    
    def is_quest_active(self, quest_id: str) -> bool:
        """Check if a quest is currently active."""
        return quest_id in self.active_quests
    
    def has_any_quest_from_npc(self, npc_id: str) -> bool:
        """Check if player has any active quest from an NPC."""
        for quest in self.active_quests.values():
            if quest.giver_npc_id == npc_id:
                return True
        return False
    
    # =========================================================================
    # DISPLAY
    # =========================================================================
    
    def format_quest_log(self) -> str:
        """Format the complete quest log for display."""
        lines = [
            "╔════════════════════════════════════════════════════════════╗",
            "║                     📜 QUEST LOG                           ║",
            "╠════════════════════════════════════════════════════════════╣"
        ]
        
        # Active quests
        active = self.get_active_quests()
        if active:
            lines.append("║ ACTIVE QUESTS:                                             ║")
            for quest in active:
                summary = quest.get_summary()
                if len(summary) > 56:
                    summary = summary[:53] + "..."
                lines.append(f"║   {summary:<56} ║")
        else:
            lines.append("║ No active quests.                                          ║")
        
        # Ready to complete
        ready = self.get_ready_to_complete()
        if ready:
            lines.append("╠════════════════════════════════════════════════════════════╣")
            lines.append("║ ✨ READY TO TURN IN:                                       ║")
            for quest in ready:
                lines.append(f"║   ➤ {quest.name:<54} ║")
        
        # Completed count
        if self.completed_quests:
            lines.append("╠════════════════════════════════════════════════════════════╣")
            lines.append(f"║ ✓ Completed: {len(self.completed_quests)} quest(s){' ' * 40} ║")
        
        lines.append("╚════════════════════════════════════════════════════════════╝")
        return "\n".join(lines)
    
    # =========================================================================
    # SERIALIZATION
    # =========================================================================
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert quest manager state to dictionary for saving."""
        return {
            "active_quests": {
                quest_id: quest.to_dict() 
                for quest_id, quest in self.active_quests.items()
            },
            "completed_quests": self.completed_quests.copy(),
            "failed_quests": self.failed_quests.copy()
        }
    
    def from_dict(self, data: Dict[str, Any]):
        """
        Load quest manager state from dictionary.
        Note: available_quests must be registered separately (from scenario).
        """
        self.active_quests = {}
        for quest_id, quest_data in data.get("active_quests", {}).items():
            self.active_quests[quest_id] = Quest.from_dict(quest_data)
        self.completed_quests = data.get("completed_quests", [])
        self.failed_quests = data.get("failed_quests", [])
    
    def restore_state(self, data: Dict[str, Any]):
        """
        Alias for from_dict for consistency with other managers.
        """
        self.from_dict(data)
    
    def clear(self):
        """Reset the quest manager to initial state."""
        self.available_quests.clear()
        self.active_quests.clear()
        self.completed_quests.clear()
        self.failed_quests.clear()
        self._objective_callbacks.clear()


# =============================================================================
# QUEST FACTORY HELPERS
# =============================================================================

def create_kill_objective(obj_id: str, description: str, enemy_id: str, 
                         count: int = 1, optional: bool = False) -> QuestObjective:
    """Helper to create a KILL objective."""
    return QuestObjective(
        id=obj_id,
        description=description,
        objective_type=ObjectiveType.KILL,
        target=enemy_id,
        required_count=count,
        optional=optional
    )


def create_find_objective(obj_id: str, description: str, item_id: str,
                         optional: bool = False, hidden: bool = False) -> QuestObjective:
    """Helper to create a FIND_ITEM objective."""
    return QuestObjective(
        id=obj_id,
        description=description,
        objective_type=ObjectiveType.FIND_ITEM,
        target=item_id,
        required_count=1,
        optional=optional,
        hidden=hidden
    )


def create_talk_objective(obj_id: str, description: str, npc_id: str,
                         optional: bool = False) -> QuestObjective:
    """Helper to create a TALK_TO objective."""
    return QuestObjective(
        id=obj_id,
        description=description,
        objective_type=ObjectiveType.TALK_TO,
        target=npc_id,
        required_count=1,
        optional=optional
    )


def create_location_objective(obj_id: str, description: str, location_id: str,
                             optional: bool = False) -> QuestObjective:
    """Helper to create a REACH_LOCATION objective."""
    return QuestObjective(
        id=obj_id,
        description=description,
        objective_type=ObjectiveType.REACH_LOCATION,
        target=location_id,
        required_count=1,
        optional=optional
    )


def create_collect_objective(obj_id: str, description: str, item_id: str,
                            count: int, optional: bool = False) -> QuestObjective:
    """Helper to create a COLLECT objective."""
    return QuestObjective(
        id=obj_id,
        description=description,
        objective_type=ObjectiveType.COLLECT,
        target=item_id,
        required_count=count,
        optional=optional
    )
