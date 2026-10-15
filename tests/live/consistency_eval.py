"""
Consistency eval: play the Goblin Cave end to end with the live GM and flag
every place the narration contradicts the game state.

    .venv/Scripts/python.exe tests/live/consistency_eval.py [--no-judge] [--seed N]

Runs in-process (Flask test client, real LLM from .env). Each GM turn is
checked two ways:

  * Rule checks (deterministic): leaked tags, items used that aren't carried,
    gifts/gold/damage narrated without the state changing, unknown named
    characters, the dead acting, wrong location/level/quest claims.
  * Judge (optional, a second LLM call): given the canonical state before and
    after the turn, list contradictions. Judge findings are leads to review,
    not verdicts - the judge can hallucinate too.

Scripted probes also test refusals (using items you don't own, paying gold
you don't have) and memory (NPCs recalling earlier events, after a save/load).

Writes tests/live/consistency_report.json and consistency_report.md.
The hero is buffed (more HP) so a run reaches the end; this measures
consistency, not balance.
"""

import argparse
import json
import os
import random
import re
import sys
import time
from collections import Counter

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "src"))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
os.chdir(os.path.join(ROOT, "src"))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(os.path.join(ROOT, ".env"))

import api_server  # noqa: E402
from api_server import app, game_sessions  # noqa: E402
from inventory import ITEMS  # noqa: E402
from llm_client import CLASSIFIER_MAX_TOKENS, generate_text, is_llm_configured  # noqa: E402
from world_memory import state_briefing  # noqa: E402

REPORT_JSON = os.path.join(ROOT, "tests", "live", "consistency_report.json")
REPORT_MD = os.path.join(ROOT, "tests", "live", "consistency_report.md")

# ---------------------------------------------------------------------------
# The script. ("act", text) is a GM turn; ("say", text) a Say-mode GM turn;
# ("go", exit) travels; ("probe", kind, text, expect) is a GM turn with an
# expectation; ("saveload",) saves and reloads mid-run.
# Probe kinds:
#   refuse   - the action should NOT happen (expect: regexes that must not match)
#   recall   - narration should mention one of the expected words
#   no_recall- narration should NOT claim the NPC remembers (expect: regexes)
# ---------------------------------------------------------------------------
SCRIPT = [
    ("act", "I look around the tavern."),
    ("act", "I walk over to the worried old farmer and ask what's wrong."),
    ("act", "I buy him a drink and swear on my sword that I will bring his daughter home. I accept."),
    ("probe", "refuse", "I drink my potion of giant strength.",
     [r"\byou (drink|down|quaff|gulp)\b", r"strength (surges|floods|courses)"]),
    ("probe", "refuse", "I draw my enchanted greatsword and show it to Bram.",
     [r"\byou draw (your|the) (enchanted )?greatsword", r"greatsword (gleams|glows|shines)"]),
    ("act", "I take the torch from the table."),
    ("go", "bar"),
    ("act", "I ask the barkeep what he knows about the goblins."),
    ("say", "Your ale tastes like goblin piss, barkeep."),
    ("probe", "refuse", "I pay the barkeep 500 gold for a map of the cave.",
     [r"\byou (hand|pay|slide|give)\b.{0,40}\b500\b", r"\btakes? (the|your) (500|gold)"]),
    ("go", "main room"),
    ("go", "outside"),
    ("act", "I look around the square."),
    ("probe", "refuse", "I pick the lock on Lily's cage and free her.",
     [r"(cage|lock|door) (opens|swings|clicks|gives)", r"lily (hugs|throws|clings|steps|stumbles|scrambles)"]),
    ("go", "forge"),
    ("probe", "no_recall", "I ask the blacksmith if he remembers me.",
     [r"\bof course i remember\b", r"\byou (were|came) here (before|yesterday|last)"]),
    ("act", "I ask what he has for sale."),
    ("go", "outside"),
    ("go", "east road"),
    ("act", "I search the path for goblin tracks."),
    ("go", "deeper"),
    ("act", "I search the clearing carefully for anything hidden."),
    ("act", "I greet the ranger and ask her about the cave."),
    ("go", "cave"),
    ("act", "I pick up the goblin ear and examine it."),
    ("go", "cave"),
    ("act", "I examine the cave entrance for tracks."),
    ("act", "I light my torch and peer into the darkness."),
    ("go", "inside"),
    ("go", "deeper"),
    ("act", "I listen carefully for goblins ahead."),
    ("saveload",),
    ("probe", "recall", "I think back on why I'm here. Whose daughter am I rescuing, and what did I promise?",
     ["bram", "lily", "daughter"]),
    ("go", "sneak left"),
    ("act", "I take the storage key and the dagger."),
    ("go", "camp"),
    # No fight has happened yet: there are no bodies to check
    ("probe", "refuse", "I check the fallen goblins. Is any of them still moving?",
     [r"\b(none|neither) of them (is|are) (breathing|moving)", r"\bthe (dead|fallen|slain) goblins\b",
      r"\bcorpses?\b", r"\blifeless\b"]),
    ("act", "I draw my longsword and attack the goblins!"),
    ("act", "I check the fallen goblins. Is any of them still moving?"),
    ("act", "I loot the camp."),
    ("go", "cages"),
    ("act", "I take the lockpicks."),
    ("act", "I pick the lock on Lily's cage and free her."),
    ("say", "Lily, your father sent me. We're going home."),
    ("go", "camp"),
    ("go", "storage"),
    ("act", "I take the silver locket and the family ring."),
    ("go", "camp"),
    ("go", "chief"),
    ("go", "lair"),
    ("act", "I charge at Chief Grotnak with my longsword!"),
    ("probe", "refuse", "I ask the goblin chief where he hid his treasure.",
     [r"(?<!no )\b(chief|grotnak|boss)\b[^.]{0,30}\b(says|growls|snarls|replies|answers|laughs)\b"]),
    ("go", "hidden alcove"),
    ("act", "I take everything in the alcove."),
    ("go", "out"),
    ("go", "leave cave"),
    ("go", "outside"),
    ("go", "village"),
    ("go", "tavern"),
    ("probe", "recall", "I bring Lily to her father. Bram, do you remember what I promised you?",
     ["promise", "swore", "drink", "daughter", "home"]),
    ("probe", "recall", "I ask the barkeep if he's still sore about what I said about his ale.",
     ["ale", "goblin", "insult", "piss"]),
    ("act", "I count my gold and tell the room how much I'm carrying."),
    ("act", "I show Bram the family ring I recovered."),
]

# ---------------------------------------------------------------------------
# Rule checks
# ---------------------------------------------------------------------------
MOMENT_MARKERS = ("💰", "📦", "⭐", "🛒", "💸", "🔍", "📜", "🏆", "🎉", "💭", "⚔", "⚠", "🎮", "---")
TAGS = ("ROLL", "COMBAT", "ITEM", "GOLD", "XP", "BUY", "PAY", "RECRUIT", "REMEMBER", "ATTITUDE")
COMMON_CAPS = {
    "The", "You", "Your", "He", "She", "It", "His", "Her", "They", "Their", "A", "An", "As", "At", "In",
    "On", "With", "But", "And", "Or", "If", "When", "What", "Where", "Who", "Why", "How", "This", "That",
    "There", "Then", "Thank", "Thanks", "Please", "Yes", "No", "Bless", "Gods", "Lady", "Sir", "Mister",
    "Rusty", "Dragon", "Tavern", "Village", "Square", "Forest", "Path", "Cave", "Darkhollow", "Goblin",
    "Goblins", "Chief", "Boss", "Cage", "Cages", "Camp", "Forge", "Blacksmith", "Clearing", "Hollow",
    "Approach", "Tunnel", "Lair", "Bar", "Main", "Room", "Wolf", "Ranger", "Barkeep", "Elf", "Dwarf",
    "Human", "Halfling", "Fighter", "Rogue", "Wizard", "Cleric", "Ranger", "Paladin", "Bard", "Not",
    "Well", "Aye", "Ah", "Oh", "Now", "Even", "Still", "So", "For", "From", "To", "By", "My", "Our",
    "We", "I", "Me", "Its", "Is", "Are", "Was", "Were", "Do", "Don't", "Can", "Will", "Would", "Should",
    "Here", "Every", "Each", "Some", "Any", "All", "One", "Two", "Three", "Four", "Five", "Mercenary",
}
SPEECH_VERBS = r"(says|said|replies|replied|growls|whispers|asks|asked|mutters|shouts|calls|answers|laughs|snarls)"
GIVE = (r"\b(hand(s|ing)?|giv(es?|ing)|toss(es|ing)|pass(es|ing)|press(es|ing)|slid(es|ing))\b[^.]{0,40}"
        r"\b(you|your hands?)\b|\byou (receive|pocket|pick up|take|grab|find|collect|claim)\b")


def item_vocabulary():
    names = set()
    for key, item in ITEMS.items():
        names.add(item.name.lower())
        names.add(key.replace("_", " "))
    return {n for n in names if len(n) > 3}


ITEM_NAMES = item_vocabulary()


def split_visible(message):
    paragraphs = re.split(r"\n{2,}", message or "")
    prose = [p for p in paragraphs if not p.strip().startswith(MOMENT_MARKERS)]
    moments = [p for p in paragraphs if p.strip().startswith(MOMENT_MARKERS)]
    return "\n\n".join(prose).strip(), moments


def snapshot(session):
    c = session.character
    return {
        "hp": c.current_hp, "max_hp": c.max_hp, "gold": c.gold, "xp": c.experience, "level": c.level,
        "items": sorted(f"{i.name.lower()} x{getattr(i, 'quantity', 1)}" for i in c.inventory),
        "weapon": (c.weapon or "").replace("_", " ").lower(),
        "armor": (c.equipped_armor or "").replace("_", " ").lower(),
        "location_id": session.current_location_id,
        "location": session.current_location,
        "in_combat": session.in_combat,
        "completed_quests": list(session.quest_manager.completed_quests),
        "active_quests": [q.id for q in session.quest_manager.get_active_quests()],
        "chronicle": list(session.chronicle),
        "world": {k: (dict(v) if isinstance(v, dict) else list(v))
                  for k, v in (getattr(session, "world", None) or {}).items()},
    }


def sentences(text):
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+|\n+", text) if s.strip()]


def owned(name, snap, location_items):
    name = name.lower()
    pool = snap["items"] + [snap["weapon"], snap["armor"]] + location_items
    return any(name in p or p in name for p in pool if p)


def rule_checks(session, before, after, prose, visible_full, location_items, known_names, fallen):
    issues = []

    def flag(kind, detail, quote=""):
        issues.append({"source": "rule", "kind": kind, "detail": detail, "quote": quote[:220]})

    for tag in TAGS:
        if re.search(rf"\[{tag}\b", visible_full, re.IGNORECASE):
            flag("tag_leak", f"[{tag}] visible to the player")

    lower = prose.lower()
    inv_changed = before["items"] != after["items"]
    gold_delta = after["gold"] - before["gold"]

    for s in sentences(prose):
        sl = s.lower()
        # Using an item the hero doesn't have
        for m in re.finditer(r"\byour ([a-z' -]{3,40})", sl):
            phrase = m.group(1)
            for name in ITEM_NAMES:
                if re.search(rf"\b{re.escape(name)}\b", phrase) and not (
                        owned(name, before, location_items) or owned(name, after, location_items)):
                    flag("unowned_item", f"refers to 'your {name}' but the hero doesn't carry it", s)
        # Gifts/finds narrated without the inventory changing
        if re.search(GIVE, sl):
            for name in ITEM_NAMES:
                if re.search(rf"\b{re.escape(name)}\b", sl) and not inv_changed and not owned(name, before, []):
                    flag("gift_without_state", f"narrates getting '{name}' but inventory didn't change", s)
        # Gold claims
        # Only the number right after the verb ("you count only 12 gold, far short of 500" is fine)
        for m in re.finditer(r"\byou (?:now )?(?:have|carry|count|hold)(?: only| just)? (\d{1,4}) ?(?:gold|gp|coins)", sl):
            if int(m.group(1)) != after["gold"]:
                flag("gold_claim", f"says the hero has {m.group(1)} gold; state says {after['gold']}", s)
        for m in re.finditer(r"\byou (?:receive|earn|gain|pocket|are paid) (\d{1,4}) ?(?:gold|gp|coins)", sl):
            if int(m.group(1)) != gold_delta:
                flag("gold_claim", f"narrates receiving {m.group(1)} gold; gold changed by {gold_delta}", s)
        # Damage or healing outside the rules
        if not before["in_combat"]:
            if re.search(r"\byou (take|suffer|lose) (\d+)\b", sl) and after["hp"] == before["hp"]:
                flag("hp_claim", "narrates numeric damage but HP didn't change", s)
            if re.search(r"\b(heal|restore)s? (\d+)\b", sl) and after["hp"] == before["hp"]:
                flag("hp_claim", "narrates numeric healing but HP didn't change", s)
        # Level claims
        m = re.search(r"\byou (are now|reach|have reached) level (\d)\b", sl)
        if m and int(m.group(2)) != after["level"]:
            flag("level_claim", f"claims level {m.group(2)}; state says {after['level']}", s)
        # Quest completion claims
        if re.search(r"\bquest (is )?(complete|completed|fulfilled)\b", sl) and \
                after["completed_quests"] == before["completed_quests"]:
            flag("quest_claim", "narrates a quest completing but none completed", s)

    # Unknown named characters
    candidates = set(re.findall(r"\bnamed ([A-Z][a-z]{2,})", prose))
    candidates |= set(m[0] for m in re.findall(rf"\b([A-Z][a-z]{{2,}}) {SPEECH_VERBS}\b", prose))
    candidates |= set(m[1] for m in re.findall(rf"\b{SPEECH_VERBS} ([A-Z][a-z]{{2,}})\b", prose))
    for name in sorted(candidates):
        if name not in known_names and name not in COMMON_CAPS:
            flag("unknown_npc", f"named character '{name}' isn't in the scenario", name)

    # The dead acting
    for name in fallen:
        if re.search(rf"\b{re.escape(name.lower())}\b[^.]{{0,25}}\b(says|attacks|lunges|roars|laughs|growls|"
                     rf"snarls|charges|swings|stands up|rises)\b", lower):
            flag("dead_acts", f"'{name}' acts after dying", name)
    return issues


# ---------------------------------------------------------------------------
# Judge
# ---------------------------------------------------------------------------
JUDGE_PROMPT = """You audit an AI game master for CONSISTENCY with the game's canonical state.
The game engine (not the narrator) owns HP, gold, items, XP, quests and who is alive. The narrator
may only describe changes the engine actually made this turn (listed under ENGINE CHANGES).

Flag ONLY clear contradictions, for example:
- the hero uses, holds or shows an item they do not carry
- the narration says the hero gains/loses items, gold or HP that ENGINE CHANGES does not show
- a dead character acts or speaks; a character not in the known lists is named as a person
- the narration places the hero somewhere other than the current location
- an NPC's attitude or memories are contradicted (e.g. a hostile NPC is warm without reason,
  or an NPC "remembers" something not in their memories and not in this conversation)
- the narration states facts that contradict WHAT HAS HAPPENED
Do NOT flag: atmosphere, unnamed extras ("a patron"), the narrator declining an impossible action,
minor flavour objects (a mug, a chair), or things the engine changes list confirms.

Respond with JSON only:
{"contradictions": [{"kind": "item|gold|hp|npc|death|location|memory|quest|other",
  "severity": "high|medium|low", "quote": "exact words", "why": "short reason"}]}

STATE BEFORE THE TURN:
%s

PLAYER ACTION: %s

ENGINE CHANGES THIS TURN: %s

NARRATION:
%s
"""


def judge(briefing, action, changes, prose):
    if not is_llm_configured():
        return []
    text = generate_text(JUDGE_PROMPT % (briefing, action, changes, prose),
                         temperature=0.0, max_tokens=CLASSIFIER_MAX_TOKENS, json_mode=True, max_retries=2)
    try:
        data = json.loads(re.search(r"\{.*\}", text or "", re.S).group(0))
        return [{"source": "judge", **c} for c in data.get("contradictions", [])]
    except Exception:
        return [{"source": "judge", "kind": "judge_error", "severity": "low", "quote": "", "why": (text or "")[:120]}]


def describe_changes(before, after, moments):
    parts = []
    for key in ("hp", "gold", "xp", "level"):
        if before[key] != after[key]:
            parts.append(f"{key} {before[key]} -> {after[key]}")
    gained = sorted(set(after["items"]) - set(before["items"]))
    lost = sorted(set(before["items"]) - set(after["items"]))
    if gained:
        parts.append("items gained: " + ", ".join(gained))
    if lost:
        parts.append("items lost: " + ", ".join(lost))
    if before["location_id"] != after["location_id"]:
        parts.append(f"moved to {after['location']}")
    done = set(after["completed_quests"]) - set(before["completed_quests"])
    if done:
        parts.append("quests completed: " + ", ".join(done))
    started = set(after["active_quests"]) - set(before["active_quests"])
    if started:
        parts.append("quests accepted: " + ", ".join(started))
    world_before, world_after = before.get("world", {}), after.get("world", {})
    for npc_id, status in (world_after.get("npc_status") or {}).items():
        if (world_before.get("npc_status") or {}).get(npc_id) != status:
            parts.append(f"{npc_id} is now {status}")
    for npc_id in set(world_after.get("followers") or []) - set(world_before.get("followers") or []):
        parts.append(f"{npc_id} now travels with the hero")
    parts += [m.strip() for m in moments if m.strip().startswith(("💭", "🎉"))]
    return "; ".join(parts) or "none"


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------
class Run:
    def __init__(self, use_judge):
        self.client = app.test_client()
        self.use_judge = use_judge
        self.turns = []
        self.events = Counter()
        body = self.client.post("/api/game/start", json={
            "character": {"name": "Brenna", "race": "Human", "class": "Fighter"},
            "scenario_id": "goblin_cave"}).get_json()
        self.sid = body["session_id"]
        hero = self.session.character
        hero.max_hp = hero.current_hp = 80  # reach the end; this run measures consistency
        self.turns.append({"step": "start", "action": "[GAME START]", "prose": split_visible(body.get("message"))[0],
                           "issues": []})

    @property
    def session(self):
        return game_sessions[self.sid]

    def known_names(self):
        s = self.session
        names = {s.character.name}
        for n in s.npc_manager.get_all_npcs():
            names.update(w for w in re.findall(r"[A-Z][a-z]+", n.name))
        for loc in s.location_manager.locations.values():
            names.update(re.findall(r"[A-Z][a-z]+", loc.name))
            for ref in loc.npcs:
                names.add(ref.capitalize())
        names.update({"Grotnak", "Lily", "Bram", "Marcus", "Elira", "Shade", "Gavin"})
        return names

    def fallen(self):
        names = []
        for entry in self.session.chronicle:
            m = re.search(r"killed: (.+?)\. They", entry)
            if m:
                names += [n.strip() for n in m.group(1).split(",")]
        return sorted(set(n for n in names if n and n.lower() not in ("goblin",)))

    def fight(self):
        rounds = 0
        while self.session.in_combat and rounds < 40:
            hero = self.session.character
            hero.current_hp = max(hero.current_hp, 30)  # keep the run going; this measures consistency
            status = self.client.get(f"/api/combat/status?session_id={self.sid}").get_json() or {}
            alive = [i for i, e in enumerate(status.get("enemies") or []) if not e.get("is_dead")]
            payload = {"session_id": self.sid}
            if alive:
                payload["target"] = alive[0]
            self.client.post("/api/combat/attack", json=payload)
            rounds += 1
        self.events["fights"] += 1
        self.events["combat_rounds"] += rounds

    def gm_turn(self, action, step, probe=None):
        s = self.session
        before = snapshot(s)
        briefing = state_briefing(s)
        here = s.location_manager.get_current_location()
        location_items = [i.replace("_", " ").lower() for i in (getattr(here, "items", None) or [])]
        t0 = time.time()
        body = self.client.post("/api/game/action", json={"session_id": self.sid, "action": action}).get_json()
        elapsed = time.time() - t0
        message = body.get("message", "") or ""
        prose, moments = split_visible(message)
        after = snapshot(self.session)
        if body.get("dm_unavailable") or self.session.dm_unavailable:
            self.events["dm_unavailable"] += 1

        issues = rule_checks(self.session, before, after, prose, message, location_items,
                             self.known_names(), self.fallen())
        if probe:
            issues += self.check_probe(probe, prose)
        changes = describe_changes(before, after, moments)
        if self.use_judge and prose:
            issues += judge(briefing, action, changes, prose)

        roll = body.get("roll_result")
        self.turns.append({
            "step": step, "action": action, "probe": probe and {"kind": probe[0], "expect": probe[1]},
            "location": before["location"], "seconds": round(elapsed, 1),
            "roll": roll and f"{roll.get('skill')} {roll.get('total')} vs DC {roll.get('dc')} "
                             f"{'success' if roll.get('success') else 'fail'}",
            "changes": changes, "prose": prose, "moments": moments, "issues": issues,
        })
        print(f"[{step:>2}] {action[:70]:<70} {elapsed:4.1f}s  issues={len(issues)}")
        for i in issues:
            print(f"       - {i['source']}:{i['kind']}: {i.get('detail') or i.get('why')}")
        if self.session.in_combat:
            self.fight()

    def check_probe(self, probe, prose):
        kind, expect = probe
        low = prose.lower()
        if kind == "refuse":
            hits = [p for p in expect if re.search(p, low)]
            return [{"source": "probe", "kind": "probe_refuse_failed",
                     "detail": f"impossible action went through ({hits[0]})"}] if hits else []
        if kind == "no_recall":
            hits = [p for p in expect if re.search(p, low)]
            return [{"source": "probe", "kind": "probe_false_memory",
                     "detail": f"NPC claims a memory that doesn't exist ({hits[0]})"}] if hits else []
        if kind == "recall":
            if not any(w in low for w in expect):
                return [{"source": "probe", "kind": "probe_recall_failed",
                         "detail": f"none of {expect} mentioned"}]
        return []

    def travel(self, exit_name, step):
        body = self.client.post("/api/travel", json={"session_id": self.sid, "destination": exit_name}).get_json()
        ok = body.get("success", "error" not in body)
        print(f"[{step:>2}] go {exit_name:<66} -> {self.session.current_location}"
              f"{'' if ok else '  (BLOCKED: ' + str(body.get('message') or body.get('error'))[:60] + ')'}")
        self.turns.append({"step": step, "action": f"go {exit_name}", "travel_ok": ok,
                           "location": self.session.current_location, "issues": []})
        if not ok:
            self.events["travel_blocked"] += 1
        if self.session.in_combat:
            self.fight()

    def save_load(self, step):
        saved = self.client.post("/api/game/save", json={"session_id": self.sid, "slot": 9}).get_json()
        loaded = self.client.post("/api/game/load", json={"name": saved["name"]}).get_json()
        os.remove(saved["save_path"])
        self.sid = loaded["session_id"]
        print(f"[{step:>2}] -- saved and reloaded --")
        self.turns.append({"step": step, "action": "[SAVE + LOAD]", "issues": []})

    def play(self):
        for step, entry in enumerate(SCRIPT, start=1):
            if self.session.game_over:
                print("GAME OVER:", self.session.game_over_reason)
                self.events["game_over"] += 1
                break
            kind = entry[0]
            if kind == "act":
                self.gm_turn(entry[1], step)
            elif kind == "say":
                self.gm_turn(f'I say: "{entry[1]}"', step)
            elif kind == "go":
                self.travel(entry[1], step)
            elif kind == "probe":
                self.gm_turn(entry[2], step, probe=(entry[1], entry[3]))
            elif kind == "saveload":
                self.save_load(step)


def write_reports(run, args):
    gm_turns = [t for t in run.turns if "prose" in t and t["step"] != "start"]
    issues = [dict(i, step=t["step"], action=t["action"]) for t in run.turns for i in t["issues"]]
    by_kind = Counter(f"{i['source']}:{i['kind']}" for i in issues)
    s = run.session
    summary = {
        "date": time.strftime("%Y-%m-%d %H:%M"), "seed": args.seed, "judge": not args.no_judge,
        "gm_turns": len(gm_turns), "turns_with_issues": sum(1 for t in gm_turns if t["issues"]),
        "issues_by_kind": dict(by_kind), "events": dict(run.events),
        "avg_seconds": round(sum(t["seconds"] for t in gm_turns) / max(1, len(gm_turns)), 1),
        "final": {"location": s.current_location, "hp": s.character.current_hp, "gold": s.character.gold,
                  "level": s.character.level, "completed_quests": list(s.quest_manager.completed_quests),
                  "chronicle": s.chronicle,
                  "memories": {n.id: n.memories for n in s.npc_manager.get_all_npcs() if n.memories}},
    }
    with open(REPORT_JSON, "w", encoding="utf-8") as f:
        json.dump({"summary": summary, "turns": run.turns}, f, indent=1, ensure_ascii=False)

    lines = [f"# Consistency eval - {summary['date']}", "",
             f"- GM turns: {summary['gm_turns']}, with issues: {summary['turns_with_issues']}",
             f"- Avg GM latency: {summary['avg_seconds']}s",
             f"- Events: {summary['events']}",
             f"- Final: {summary['final']['location']}, HP {summary['final']['hp']}, gold {summary['final']['gold']}, "
             f"quests done {summary['final']['completed_quests']}", "",
             "## Issues by kind", ""]
    lines += [f"- {k}: {v}" for k, v in by_kind.most_common()] or ["- none"]
    lines += ["", "## Issues", ""]
    for i in issues:
        lines.append(f"- **[{i['step']}] {i['source']}:{i['kind']}** ({i.get('severity', '-')}) - "
                     f"{i.get('detail') or i.get('why')}  ")
        lines.append(f"  action: _{i['action']}_  ")
        if i.get("quote"):
            lines.append(f"  quote: \"{i['quote']}\"")
    lines += ["", "## Transcript", ""]
    for t in run.turns:
        lines.append(f"### [{t['step']}] {t['action']}")
        if t.get("roll"):
            lines.append(f"_roll: {t['roll']}_")
        if t.get("changes"):
            lines.append(f"_changes: {t['changes']}_")
        if t.get("prose"):
            lines += ["", t["prose"], ""]
        for m in t.get("moments") or []:
            lines.append(f"> {m.strip()}")
        lines.append("")
    with open(REPORT_MD, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return summary


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-judge", action="store_true", help="skip the LLM judge (rule checks only)")
    parser.add_argument("--seed", type=int, default=7, help="dice seed (LLM output still varies)")
    args = parser.parse_args()
    if not is_llm_configured():
        sys.exit("No LLM configured in .env - this eval needs the live GM.")
    random.seed(args.seed)
    api_server.app.config["TESTING"] = True
    run = Run(use_judge=not args.no_judge)
    run.play()
    summary = write_reports(run, args)
    print("\n" + json.dumps({k: summary[k] for k in ("gm_turns", "turns_with_issues", "issues_by_kind",
                                                       "events", "avg_seconds")}, indent=1))
    print(f"\nReport: {REPORT_MD}")


if __name__ == "__main__":
    main()
