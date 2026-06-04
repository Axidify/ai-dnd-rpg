import {
  Sword,
  Sparkles,
  Crosshair,
  Cross,
  Target,
  Axe,
  Shield,
  Flame,
  Music,
  Hand,
  Leaf,
  Star,
  User,
} from 'lucide-react'

const CLASS_ICONS = {
  Fighter: Sword,
  Wizard: Sparkles,
  Rogue: Crosshair,
  Cleric: Cross,
  Ranger: Target,
  Barbarian: Axe,
  Paladin: Shield,
  Warlock: Flame,
  Bard: Music,
  Monk: Hand,
  Druid: Leaf,
  Sorcerer: Star,
}

export function getClassIcon(className) {
  return CLASS_ICONS[className] || User
}
