"""
World model: the engine is the single source of truth.

The AI narrates; it never decides facts. This module does two jobs:

1. Premise check (before narration). Players often write actions that
   assume things: "I free Lily" (is she here?), "I drink my potion of giant
   strength" (do I have one?), "I search the fallen goblins" (did a fight
   happen?). analyze_action() resolves every person, creature and item the
   action refers to against the current scene and returns engine facts. The
   narrator is told those facts outrank the player's assumptions, and no
   dice are rolled for an action whose targets don't exist.

2. Grant validation (after narration). The narrator may only hand over
   things that exist: an item lying here, or a gift a present NPC can give.
   Gold and XP come from the engine (loot, quests, objectives, combat), never
   from narration. Purchases need a merchant present; recruits must be here.

Everything resolves against the same data the engine uses (locations, NPCs,
the item catalog), so prose can't create or contradict state.
"""

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from inventory import ITEMS, find_item_in_inventory, get_item
from text_match import has_any, has_phrase

TAKE_VERBS = ["take", "grab", "pick up", "loot", "pocket", "collect", "steal", "snatch", "gather"]
USE_VERBS = ["use", "drink", "quaff", "draw", "wield", "equip", "light", "read", "show", "give", "hand",
             "throw", "eat", "wear", "unlock", "brandish", "pull out", "hold up"]
DEATH_WORDS = ["fallen", "dead", "corpse", "corpses", "bodies", "body", "slain", "killed", "carcass", "remains"]
TALK_VERBS = ["ask", "tell", "talk", "speak", "say", "greet", "question", "answer"]
# Words that follow "my" without naming a possession worth checking
NOT_POSSESSIONS = {"way", "word", "words", "name", "father", "mother", "family", "friend", "friends", "life",
                   "promise", "oath", "hand", "hands", "head", "eyes", "mind", "heart", "back", "feet", "turn",
                   "best", "own", "time", "breath", "voice", "honor", "honour", "grave", "self", "throat"}


@dataclass
class Premise:
    """What the engine found when checking an action against the world."""
    facts: List[str] = field(default_factory=list)
    blocks_roll: bool = False
    refs: Dict[str, List[str]] = field(default_factory=dict)  # for tests and debugging

    def note(self, fact: str) -> None:
        if fact not in self.facts:
            self.facts.append(fact)


# =============================================================================
# WHO AND WHAT EXISTS
# =============================================================================

def _here(session):
    manager = session.location_manager
    return manager.get_current_location() if manager else None


def _actors(session) -> Dict[str, Dict[str, Any]]:
    scenario = session.scenario.active_scenario if session.scenario else None
    return getattr(scenario, "actors", None) or {}


def _actor_state(session, ref: str) -> Tuple[bool, bool]:
    """(here, alive) for a scenario actor such as 'goblins' or 'grotnak'."""
    here = _here(session)
    manager = session.location_manager
    homes = [loc for loc in manager.locations.values() if ref in loc.npcs] if manager else []
    # A combatant dies with its location's fixed encounter
    alive = not any(loc.encounter and loc.encounter_defeated for loc in homes)
    return bool(here and ref in here.npcs), alive


def people(session) -> List[Dict[str, Any]]:
    """Every person or creature the player could name, with where they stand."""
    from world_memory import present_npc_ids

    present = set(present_npc_ids(session))
    party = {m.id for m in session.party.get_alive_members()} if session.party else set()
    out = []
    if session.npc_manager:
        for npc in session.npc_manager.get_all_npcs():
            words = [npc.name.lower(), npc.id.replace("_", " ")] + [a.lower() for a in npc.aliases]
            out.append({"id": npc.id, "name": npc.name, "words": words, "kind": "npc",
                        "here": npc.id in present or npc.id in party, "alive": True})
    for ref, info in _actors(session).items():
        here, alive = _actor_state(session, ref)
        name = info.get("name", ref)
        words = [name.lower(), ref] + [a.lower() for a in info.get("aliases", [])]
        out.append({"id": ref, "name": name, "words": words, "kind": "actor", "here": here, "alive": alive})
    return out


def _item_names() -> List[Tuple[str, str]]:
    """(phrase, key) for every catalog item, longest phrases first."""
    pairs = set()
    for key, item in ITEMS.items():
        pairs.add((item.name.lower(), key))
        pairs.add((key.replace("_", " "), key))
    return sorted(pairs, key=lambda p: -len(p[0]))


ITEM_PHRASES = _item_names()


def carries(session, key: str) -> bool:
    c = session.character
    if not c:
        return False
    item = get_item(key)
    # The inventory holds display names ("Thieves' Tools" for lockpicks)
    if find_item_in_inventory(c.inventory, key) or (item and find_item_in_inventory(c.inventory, item.name)):
        return True
    equipped = {(c.weapon or "").lower(), (c.equipped_armor or "").lower()}
    return key in equipped or bool(item and item.name.lower() in equipped)


def items_here(session) -> List[str]:
    here = _here(session)
    return list(here.items) if here else []


def _carried_names(session) -> List[str]:
    c = session.character
    if not c:
        return []
    names = [i.name.lower() for i in c.inventory]
    names += [(c.weapon or "").replace("_", " ").lower(), (c.equipped_armor or "").replace("_", " ").lower()]
    return [n for n in names if n]


# =============================================================================
# 1. PREMISE CHECK
# =============================================================================

def _be(name: str) -> str:
    """'is' or 'are': "Lily is", "the goblins are"."""
    return "are" if name.lower().startswith("the ") and name.endswith("s") or name.endswith("guards") else "is"


def _article(phrase: str) -> str:
    return "an" if phrase[:1] in "aeiou" else "a"


def _plain(text: str) -> str:
    """Lowercase without possessive 's, so "Lily's cage" mentions Lily."""
    return re.sub(r"['’]s(?![a-z])", "", (text or "").lower())


def _mentions(text: str, words: List[str]) -> bool:
    return any(w and has_phrase(text, _plain(w)) for w in words)


# (phrases, item key, how to name it): actions that need a tool they don't mention
IMPLIED_TOOLS = [
    (["pick the lock", "pick lock", "pick its lock", "pick a lock", "lockpick"], "lockpicks", "lockpicks"),
]

PHRASE_ENDS = {
    "and", "or", "but", "to", "at", "on", "into", "from", "with", "for", "as", "while", "then", "in", "over",
    "that", "which", "who", "i", "you", "he", "she", "it", "we", "they", "will", "would", "is", "are", "was",
    "were", "can", "could", "shall", "should", "so", "because", "if", "when", "before", "after", "until",
}


def _possessions_claimed(text: str) -> List[str]:
    """Phrases after 'my': 'my potion of giant strength' -> 'potion of giant strength'."""
    claims = []
    for m in re.finditer(r"\bmy ((?:[a-z'-]+ ){0,3}[a-z'-]+)", text):
        words = m.group(1).split()
        cut = []
        for w in words:
            if w in PHRASE_ENDS:
                break
            cut.append(w)
        if cut and cut[0] not in NOT_POSSESSIONS:
            claims.append(" ".join(cut))
    return claims


def _owns_phrase(phrase: str, carried: List[str]) -> bool:
    """Every content word of the phrase appears in one carried item's name."""
    words = [w for w in phrase.split() if w not in ("of", "the", "a", "an", "old", "trusty")]
    return any(all(w.rstrip("s") in name for w in words) for name in carried)


def _is_item_phrase(phrase: str) -> bool:
    nouns = {p.split()[-1] for p, _ in ITEM_PHRASES} | {
        "greatsword", "sword", "bow", "shield", "staff", "wand", "axe", "hammer", "map", "cloak", "flint",
        "picks", "tools", "potion", "ring", "amulet", "key", "keys", "scroll", "blade", "knife", "spear"}
    return any(w.rstrip("s") in nouns or w in nouns for w in phrase.split())


def analyze_action(session, action: str) -> Premise:
    """Resolve what the action refers to against the world; see module docs."""
    premise = Premise()
    text = _plain(action)
    if not text.strip():
        return premise

    hero = (session.character.name.lower() if session.character else "")
    present_refs, absent_refs = [], []

    # People and creatures
    for person in people(session):
        if hero and person["name"].lower() == hero:
            continue
        if not _mentions(text, person["words"]):
            continue
        name = person["name"]
        if person["here"] and person["alive"]:
            present_refs.append(person["id"])
            if person["kind"] == "actor" and has_any(text, DEATH_WORDS):
                premise.note(f"{name} here are ALIVE - no fight has happened, so there are no bodies.")
                premise.blocks_roll = True
        elif not person["alive"]:
            absent_refs.append(person["id"])
            premise.note(f"{name[:1].upper() + name[1:]} {_be(name)} dead and cannot act or speak.")
        else:
            absent_refs.append(person["id"])
            premise.note(f"{name[:1].upper() + name[1:]} {_be(name)} NOT here.")

    # Items named from the catalog
    taking, using = has_any(text, TAKE_VERBS), has_any(text, USE_VERBS)
    claimed_text = text
    seen_keys = set()
    for phrase, key in ITEM_PHRASES:
        if key in seen_keys or not has_phrase(claimed_text, phrase):
            continue
        seen_keys.add(key)
        claimed_text = claimed_text.replace(phrase, " ")  # don't re-match "potion" inside "healing potion"
        name = get_item(key).name if get_item(key) else phrase
        if key in items_here(session) or (carries(session, key) and not taking):
            present_refs.append(key)
        elif taking and carries(session, key):
            absent_refs.append(key)
            premise.note(f"There is no {name} here to take (the hero already carries their own).")
        else:
            absent_refs.append(key)
            premise.note(f"There is no {name} here, and the hero does not carry one."
                         if not taking else f"There is no {name} here to take.")

    # Tools an action needs without naming them ("I pick the lock")
    for phrases, key, label in IMPLIED_TOOLS:
        if has_any(text, phrases) and not carries(session, key) and key not in seen_keys:
            premise.note(f"The hero has no {label}, so they can't {phrases[0]}; "
                         f"don't narrate them using {label}.")

    # Possessions the player claims ("my enchanted greatsword")
    carried = _carried_names(session)
    for phrase in _possessions_claimed(text):
        if _is_item_phrase(phrase) and not _owns_phrase(phrase, carried):
            absent_refs.append(phrase)
            premise.note(f"The hero does NOT have {_article(phrase)} {phrase}. They carry only what the CHARACTER section lists.")
            if using or taking:
                premise.blocks_roll = True

    # No roll for an action aimed only at things that aren't there
    if absent_refs and not present_refs:
        nobody_here = not any(p["here"] and p["alive"] for p in people(session))
        aimed_at_items = (taking or using) and any(r in ITEMS for r in absent_refs)
        aimed_at_people = any(r not in ITEMS for r in absent_refs) and nobody_here
        if aimed_at_items or aimed_at_people:
            premise.blocks_roll = True

    premise.refs = {"present": present_refs, "absent": absent_refs}
    return premise


def premise_instruction(premise: Premise) -> str:
    """The block the narrator reads before narrating this action."""
    if not premise.facts:
        return ""
    lines = "\n".join(f"- {f}" for f in premise.facts)
    return (
        "\n[ENGINE CHECK - facts about this action. They OVERRIDE what the player's words assume. "
        "Narrate the attempt meeting reality (the person isn't here, the item doesn't exist, the "
        "goblins are alive); never make the assumed thing true.]\n" + lines
    )


# =============================================================================
# 2. WHAT THE NARRATOR MAY GRANT
# =============================================================================

def present_npcs(session) -> List[Any]:
    from world_memory import present_npc_ids

    ids = set(present_npc_ids(session))
    if session.party:
        ids |= {m.id for m in session.party.get_alive_members()}
    return [n for n in (session.npc_manager.get_all_npcs() if session.npc_manager else []) if n.id in ids]


def grantable(session) -> Dict[str, str]:
    """Item key -> where it comes from ('here' or the giving NPC's id)."""
    out = {key: "here" for key in items_here(session)}
    for npc in present_npcs(session):
        for key in npc.gifts:
            out.setdefault(key, npc.id)
    return out


def grants_briefing(session) -> str:
    """Tell the narrator exactly what it may hand over this turn."""
    options = grantable(session)
    if not options:
        return ("ITEMS YOU MAY GRANT WITH [ITEM]: none here. Do not narrate the hero receiving or finding "
                "items; gold and XP are awarded by the game, never by narration.")
    parts = []
    for key, source in options.items():
        item = get_item(key)
        label = item.name if item else key
        parts.append(f"{key} ({label}, lying here)" if source == "here" else
                     f"{key} ({label}, {source} can give it)")
    return ("ITEMS YOU MAY GRANT WITH [ITEM]: " + "; ".join(parts) +
            ". Nothing else exists to be found or given. Gold and XP are awarded by the game, never by narration.")


def _catalog_key(item_name: str) -> Optional[str]:
    item = get_item(item_name)
    if not item:
        return None
    for key, catalog_item in ITEMS.items():
        if catalog_item.name == item.name:
            return key
    return item_name.lower().replace(" ", "_")


def claim_item(session, item_name: str) -> Tuple[bool, Optional[str]]:
    """
    May the narrator's [ITEM] go through? Consumes the source (the item leaves
    the location, or the NPC's gift is used up). Returns (allowed, key).
    """
    key = _catalog_key(item_name)
    if not key:
        return False, None
    for npc in present_npcs(session):
        if key in npc.gifts:
            npc.gifts.remove(key)
            return True, key
    here = _here(session)
    if here and key in here.items:
        here.items.remove(key)
        return True, key
    return False, key


def npc_is_here(session, npc_id: str) -> bool:
    ref = (npc_id or "").strip().lower()
    return any(n.id == ref or n.name.lower() == ref for n in present_npcs(session))


def merchant_here(session) -> bool:
    return any(n.role.name == "MERCHANT" for n in present_npcs(session))


def fair_price(item_name: str, price: int) -> bool:
    item = get_item(item_name)
    return bool(item) and price >= max(1, item.value)


SPEECH_WORDS = ["say", "ask", "tell", "talk", "speak", "greet", "hello", "call out", "whisper", "shout",
                "reply", "answer", "promise", "reassure", "comfort", "thank", "introduce"]


def npcs_addressed(session, action: str) -> List[str]:
    """
    NPCs the hero speaks to this turn: they must be here, named (or by
    alias), and the action must be speech ('I say: "Lily, ..."', 'ask the
    farmer', 'tell Bram'). Someone who isn't here can't be talked to.
    """
    text = _plain(action)
    speaking = has_any(text, SPEECH_WORDS) or text.lstrip().startswith(("i say", '"'))
    if not speaking:
        return []
    return [p["id"] for p in people(session)
            if p["kind"] == "npc" and p["here"] and _mentions(text, p["words"])]
