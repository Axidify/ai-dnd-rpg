"""
World memory: the facts the Game Master must stay consistent with.

The rules engine owns game state; the AI only narrates. This module turns
that state into the briefing the GM reads every turn, and gives the GM a
narrow, validated way to record what should be remembered:

    [REMEMBER: bram | Brenna promised to bring Lily home]
    [ATTITUDE: bram | +10 | grateful she took the job]

Both are checked by the server (the NPC must exist; facts are short;
attitude moves at most MAX_ATTITUDE_STEP per tag) and saved with the game.
Key events are also recorded deterministically (quests, recruitment,
victories) so memory never depends on the AI remembering to tag.

The chronicle is a persistent log of hard facts (who died, what was found,
what was promised) that every GM turn sees and that survives save/load.
"""

import re
from typing import Any, Dict, List, Optional, Tuple

MAX_NPC_MEMORIES = 12      # per NPC; oldest drop off first
MAX_FACT_LENGTH = 160
MAX_ATTITUDE_STEP = 15     # largest disposition change one tag can make
MAX_CHRONICLE = 40         # entries kept; the GM sees the most recent
CHRONICLE_IN_CONTEXT = 15

REMEMBER_PATTERN = re.compile(r'\[REMEMBER:\s*([^|\]]+?)\s*\|\s*([^\]]+?)\s*\]', re.IGNORECASE)
ATTITUDE_PATTERN = re.compile(
    r'\[ATTITUDE:\s*([^|\]]+?)\s*\|\s*([+-]?\d+)\s*(?:\|\s*([^\]]*?)\s*)?\]', re.IGNORECASE
)


# =============================================================================
# NPC MEMORY AND ATTITUDE
# =============================================================================

def resolve_npc(npc_manager, ref: str):
    """Find an NPC by id, full name, or a distinctive word of its name."""
    if not npc_manager or not ref:
        return None
    key = ref.strip().lower().replace(' ', '_')
    npc = npc_manager.get_npc(ref.strip()) or npc_manager.get_npc(key)         or npc_manager.get_npc_by_name(ref.strip())
    if npc:
        return npc
    words = ref.strip().lower().split()
    for candidate in npc_manager.get_all_npcs():
        name_words = [w for w in candidate.name.lower().split() if len(w) > 3]
        if any(w in name_words for w in words):
            return candidate
    return None


def remember(npc, fact: str) -> bool:
    """Add a memory to an NPC (deduplicated, trimmed, capped). True if stored."""
    fact = " ".join(str(fact).split())[:MAX_FACT_LENGTH].rstrip(" .") + "."
    if len(fact) < 4:
        return False
    if any(fact.lower() == m.lower() for m in npc.memories):
        return False
    npc.memories.append(fact)
    del npc.memories[:-MAX_NPC_MEMORIES]
    return True


def shift_attitude(npc, delta: int) -> int:
    """Move an NPC's disposition by a clamped step. Returns the applied change."""
    step = max(-MAX_ATTITUDE_STEP, min(MAX_ATTITUDE_STEP, int(delta)))
    before = npc.disposition
    npc.modify_disposition(step)
    return npc.disposition - before


def apply_memory_tags(session, narrator_text: str) -> List[Dict[str, Any]]:
    """
    Apply [REMEMBER] and [ATTITUDE] tags from the narrator's raw text.
    Tags naming unknown NPCs are ignored. Returns events (for the UI/log);
    these are never shown to the player as text.
    """
    events: List[Dict[str, Any]] = []
    manager = session.npc_manager
    if not manager or not narrator_text:
        return events

    for ref, fact in REMEMBER_PATTERN.findall(narrator_text):
        npc = resolve_npc(manager, ref)
        if npc and remember(npc, fact):
            events.append({"type": "npc_memory", "npc_id": npc.id, "fact": npc.memories[-1]})

    for ref, delta, reason in ATTITUDE_PATTERN.findall(narrator_text):
        npc = resolve_npc(manager, ref)
        if not npc:
            continue
        applied = shift_attitude(npc, int(delta))
        if applied:
            events.append({"type": "npc_attitude", "npc_id": npc.id, "change": applied,
                           "disposition": npc.disposition, "reason": reason.strip()})
            if reason.strip():
                remember(npc, f"{'Warmed to' if applied > 0 else 'Soured on'} the hero: {reason.strip()}")
    return events


# =============================================================================
# CHRONICLE
# =============================================================================

def chronicle(session, entry: str) -> None:
    """Record a hard fact the GM must never contradict (persisted with saves)."""
    entry = " ".join(str(entry).split())
    if not entry:
        return
    if not isinstance(getattr(session, "chronicle", None), list):
        session.chronicle = []
    log = session.chronicle
    if log and log[-1] == entry:
        return
    log.append(entry)
    del log[:-MAX_CHRONICLE]


# =============================================================================
# THE GM'S STATE BRIEFING
# =============================================================================

def present_npc_ids(session) -> List[str]:
    """NPCs in the current scene: listed at this location, or placed here."""
    manager = session.location_manager
    here = manager.get_current_location() if manager else None
    if not here or not session.npc_manager:
        return []
    ids = []
    for ref in here.npcs:
        npc = session.npc_manager.get_npc(ref)
        if npc and npc.id not in ids:
            ids.append(npc.id)
    for npc in session.npc_manager.get_npcs_at_location(here.id):
        if npc.id not in ids:
            ids.append(npc.id)
    return ids


def _item_label(item) -> str:
    name = item.name if hasattr(item, "name") else str(item.get("name", item))
    qty = item.quantity if hasattr(item, "quantity") else item.get("quantity", 1)
    return f"{name} x{qty}" if qty and qty > 1 else name


def character_briefing(session) -> str:
    c = session.character
    if not c:
        return ""
    from character import XP_THRESHOLDS
    next_xp = XP_THRESHOLDS.get(c.level + 1)
    items = ", ".join(_item_label(i) for i in c.inventory) or "nothing"
    lines = [
        "CHARACTER (canonical - never contradict):",
        f"- {c.name}, level {c.level} {c.race} {c.char_class}",
        f"- HP {c.current_hp}/{c.max_hp}, AC {c.armor_class}, gold {c.gold}",
        f"- XP {c.experience}" + (f" (next level at {next_xp})" if next_xp else " (max level)"),
        f"- Wielding: {c.weapon or 'nothing'}; wearing: {c.equipped_armor or 'no armor'}",
        f"- Carrying ONLY: {items}",
    ]
    party = session.party.get_alive_members() if session.party else []
    if party:
        lines.append("- Companions: " + ", ".join(
            f"{m.name} ({m.char_class.value if hasattr(m.char_class, 'value') else m.char_class}, "
            f"HP {m.current_hp}/{m.max_hp})" for m in party))
    return "\n".join(lines)


def npc_briefing(session) -> str:
    manager = session.npc_manager
    if not manager:
        return ""
    present = present_npc_ids(session)
    party_ids = {m.id for m in session.party.members} if session.party else set()
    sections = []
    for npc_id in present:
        npc = manager.get_npc(npc_id)
        if not npc:
            continue
        lines = [f"[id: {npc.id}]", npc.get_context_for_dm()]
        if npc.memories:
            lines.append("Remembers about the hero:")
            lines.extend(f"  - {m}" for m in npc.memories)
        sections.append("\n".join(lines))

    others = [n for n in manager.get_all_npcs() if n.id not in present]
    brief = "\n".join(
        f"  - {n.name} [id: {n.id}] ({n.role.name.lower()}){' - in the party' if n.id in party_ids else ''}"
        f"{f' - remembers: {n.memories[-1]}' if n.memories else ''}"
        for n in others
    )
    out = ""
    if sections:
        out += "NPCS HERE (play them consistently with their personality, attitude and memories):\n"
        out += "\n\n".join(sections) + "\n"
    if brief:
        out += "\nOTHER KNOWN NPCS (not here; ONLY these exist - never invent new named characters):\n" + brief + "\n"
    return out


def quest_briefing(session) -> str:
    qm = session.quest_manager
    if not qm:
        return ""
    lines = []
    for q in qm.get_active_quests():
        lines.append(f"- {q.name}: {q.description}")
        for o in q.objectives:
            if not getattr(o, "hidden", False):
                lines.append(f"    [{'x' if o.completed else ' '}] {o.description}")
    done = [qm.available_quests[qid].name for qid in qm.completed_quests if qid in qm.available_quests]
    out = ""
    if lines:
        out += "ACTIVE QUESTS:\n" + "\n".join(lines) + "\n"
    if done:
        out += "COMPLETED QUESTS: " + ", ".join(done) + "\n"
    return out


def chronicle_briefing(session) -> str:
    if not getattr(session, "chronicle", None):
        return ""
    recent = session.chronicle[-CHRONICLE_IN_CONTEXT:]
    return ("WHAT HAS HAPPENED SO FAR (facts - never contradict; the dead stay dead):\n"
            + "\n".join(f"- {e}" for e in recent) + "\n")


def state_briefing(session) -> str:
    """Everything the GM must stay consistent with, as one block."""
    parts = [character_briefing(session), quest_briefing(session),
             npc_briefing(session), chronicle_briefing(session)]
    return "\n".join(p for p in parts if p)


def parse_memory_tags_for_test(text: str) -> Tuple[List[Tuple[str, str]], List[Tuple[str, str, str]]]:
    """Expose raw tag parsing (used by tests)."""
    return REMEMBER_PATTERN.findall(text), ATTITUDE_PATTERN.findall(text)
