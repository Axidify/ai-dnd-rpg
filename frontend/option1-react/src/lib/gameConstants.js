export const XP_THRESHOLDS = { 1: 0, 2: 100, 3: 300, 4: 600, 5: 1000 }

export function getXpProgress(character) {
  const currentXP = character?.experience ?? character?.xp ?? 0
  const level = character?.level || 1
  const currentThreshold = XP_THRESHOLDS[level] || 0
  const nextThreshold = XP_THRESHOLDS[level + 1] || XP_THRESHOLDS[5]
  const xpInLevel = currentXP - currentThreshold
  const xpNeeded = nextThreshold - currentThreshold
  const progress = level >= 5 ? 100 : (xpInLevel / xpNeeded) * 100
  const canLevelUp = level < 5 && currentXP >= nextThreshold
  return { currentXP, level, nextThreshold, progress, canLevelUp }
}

export function getCharacterHp(character) {
  const current = character?.current_hp ?? character?.hp ?? character?.health ?? 20
  const max = character?.max_hp || 20
  return { current, max, pct: max > 0 ? Math.min(100, (current / max) * 100) : 0 }
}
