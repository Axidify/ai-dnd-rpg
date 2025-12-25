/**
 * Goblin Raid Scenario E2E Tests
 * 
 * Comprehensive tests for the Goblin Cave/Raid scenario including:
 * - Character creation with scenario selection
 * - Tavern interactions and NPC dialogue
 * - Party recruitment (Marcus the Sellsword)
 * - Travel and navigation
 * - Shop system
 * - Quest tracking
 * - Combat encounters
 */

import { test, expect, Page } from '@playwright/test';

// Screenshot directory for this test suite
const SCREENSHOT_DIR = 'e2e/screenshots/goblin-raid';

// Helper to log console messages with consistent format
async function log(category: string, message: string) {
  const timestamp = new Date().toTimeString().slice(0, 8);
  console.log(`[${timestamp}] [GOBLIN-${category}] ${message}`);
}

// Helper to take labeled screenshots
async function screenshot(page: Page, name: string) {
  await page.screenshot({ path: `${SCREENSHOT_DIR}/${name}.png` });
  await log('SCREENSHOT', `Captured: ${name}.png`);
}

// Helper to wait for DM response (AI-generated content)
async function waitForDMResponse(page: Page) {
  // Wait for loading spinner to appear and disappear
  await page.waitForTimeout(500);
  
  // Look for loading indicator to finish
  const loadingSpinner = page.locator('[class*="loading"], [class*="spinner"], .animate-spin');
  if (await loadingSpinner.count() > 0) {
    await loadingSpinner.first().waitFor({ state: 'hidden', timeout: 15000 });
  }
  
  // Additional wait for streaming response
  await page.waitForTimeout(2000);
}

// Helper to send an action and wait for response
async function sendAction(page: Page, action: string) {
  const input = page.locator('input[type="text"], textarea').first();
  await input.fill(action);
  await input.press('Enter');
  await log('ACTION', `Sent: "${action}"`);
  await waitForDMResponse(page);
}

// Helper to click a quick action button
async function clickQuickAction(page: Page, label: string) {
  // Quick actions have emoji prefixes, try multiple patterns
  const patterns = [
    new RegExp(label, 'i'),
    new RegExp(`.*${label}.*`, 'i'),
  ];
  
  for (const pattern of patterns) {
    const button = page.locator('button').filter({ hasText: pattern }).first();
    if (await button.isVisible().catch(() => false)) {
      await button.click();
      await log('CLICK', `Clicked: ${label}`);
      return true;
    }
  }
  
  // Try finding by partial match in all buttons
  const allButtons = await page.locator('button').all();
  for (const btn of allButtons) {
    const text = await btn.innerText().catch(() => '');
    if (text.toLowerCase().includes(label.toLowerCase()) && await btn.isVisible()) {
      await btn.click();
      await log('CLICK', `Clicked button with text: ${text.trim().substring(0, 30)}`);
      return true;
    }
  }
  
  await log('WARN', `Button not found: ${label}`);
  return false;
}

test.describe('Goblin Raid Scenario - Character Creation', () => {
  
  test('should create character and select Goblin Cave scenario', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    await screenshot(page, '01-initial');
    
    // Enter character name
    const nameInput = page.locator('input[type="text"]').first();
    await expect(nameInput).toBeVisible();
    await nameInput.fill('GoblinSlayer');
    await log('INPUT', 'Entered name: GoblinSlayer');
    
    // Select Fighter class
    const fighterButton = page.locator('button').filter({ hasText: 'Fighter' }).first();
    await fighterButton.click();
    await log('CLASS', 'Selected Fighter class');
    await screenshot(page, '02-class-selected');
    
    // Select Human race
    const humanButton = page.locator('button').filter({ hasText: 'Human' }).first();
    await humanButton.click();
    await log('RACE', 'Selected Human race');
    
    // Look for scenario selection - Goblin Cave/Raid
    const goblinScenario = page.locator('button, div').filter({ 
      hasText: /goblin.*cave|goblin.*raid|raiders/i 
    }).first();
    
    if (await goblinScenario.isVisible()) {
      await goblinScenario.click();
      await log('SCENARIO', 'Selected Goblin scenario');
      await screenshot(page, '03-scenario-selected');
    } else {
      await log('WARN', 'Goblin scenario button not found, using default');
    }
    
    // Click create/start button
    const startButton = page.locator('button').filter({ 
      hasText: /begin.*adventure|start|create.*character/i 
    }).first();
    await startButton.click();
    await log('START', 'Clicked start button');
    
    // Wait for game to load and AI to generate opening
    await waitForDMResponse(page);
    await screenshot(page, '04-game-started');
    
    // Verify we're in the game by checking for game UI elements
    // Look for action input, buttons, or any game content
    await page.waitForTimeout(1000);
    
    const hasInput = await page.locator('input[type="text"], textarea').count() > 0;
    const hasButtons = await page.locator('button').count() > 5;
    
    await log('VERIFY', `Has input: ${hasInput}, Has buttons: ${hasButtons}`);
    expect(hasInput || hasButtons).toBeTruthy();

    // Check for location indicator (should be tavern or village)
    const pageContent = await page.content();
    const hasTavern = /tavern|inn|rusty dragon/i.test(pageContent);
    const hasVillage = /village|willowbrook|square/i.test(pageContent);
    
    await log('LOCATION', `Has tavern: ${hasTavern}, Has village: ${hasVillage}`);
    expect(hasTavern || hasVillage).toBeTruthy();
  });
});

test.describe('Goblin Raid Scenario - Tavern Phase', () => {
  
  // Setup: Create character and start game before each test
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    
    // Quick character creation
    await page.locator('input[type="text"]').first().fill('TestHero');
    await page.locator('button').filter({ hasText: 'Fighter' }).first().click();
    
    // Select Goblin scenario if available
    const goblinScenario = page.locator('button, div').filter({ 
      hasText: /goblin/i 
    }).first();
    if (await goblinScenario.isVisible()) {
      await goblinScenario.click();
    }
    
    // Start game
    await page.locator('button').filter({ 
      hasText: /begin|start|create/i 
    }).first().click();
    
    await waitForDMResponse(page);
  });
  
  test('should see the tavern environment', async ({ page }) => {
    await screenshot(page, '10-tavern-start');
    
    // Look around
    await sendAction(page, 'I look around the tavern');
    await screenshot(page, '11-tavern-look');
    
    // Get page content
    const content = await page.locator('body').innerText();
    
    // Should mention NPCs or tavern elements
    const hasNPCsOrEnv = /barkeep|bartender|patron|table|fire|hearth|drink/i.test(content);
    await log('VERIFY', `Has tavern content: ${hasNPCsOrEnv}`);
  });
  
  test('should interact with barkeep', async ({ page }) => {
    await sendAction(page, 'I approach the barkeep and ask for information');
    await screenshot(page, '12-barkeep-talk');
    
    const content = await page.locator('body').innerText();
    await log('CONTENT', `Response length: ${content.length} chars`);
  });
  
  test('should find Marcus the sellsword', async ({ page }) => {
    // Look for Marcus
    await sendAction(page, 'I look around for anyone who looks like a sellsword or mercenary');
    await screenshot(page, '13-find-marcus');
    
    // Try to approach Marcus
    await sendAction(page, 'I approach Marcus the sellsword');
    await screenshot(page, '14-approach-marcus');
    
    const content = await page.locator('body').innerText();
    const mentionsMarcus = /marcus|sellsword|mercenary|warrior/i.test(content);
    await log('NPC', `Marcus mentioned: ${mentionsMarcus}`);
  });
  
  test('should recruit Marcus to party', async ({ page }) => {
    // Approach and recruit Marcus
    await sendAction(page, 'I speak to Marcus about joining me');
    await screenshot(page, '15-talk-marcus');
    
    await sendAction(page, 'I offer Marcus to join my party for the goblin hunt');
    await screenshot(page, '16-offer-marcus');
    
    // Check party panel
    await clickQuickAction(page, 'Party');
    await page.waitForTimeout(1000);
    await screenshot(page, '17-party-panel');
    
    // Close panel if open
    const closeButton = page.locator('button').filter({ hasText: /close|×|x/i }).first();
    if (await closeButton.isVisible()) {
      await closeButton.click();
    }
  });
});

test.describe('Goblin Raid Scenario - Travel & Navigation', () => {
  
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    
    // Quick start
    await page.locator('input[type="text"]').first().fill('TravelHero');
    await page.locator('button').filter({ hasText: 'Fighter' }).first().click();
    await page.locator('button').filter({ hasText: /begin|start|create/i }).first().click();
    await waitForDMResponse(page);
  });
  
  test('should open World Map', async ({ page }) => {
    await clickQuickAction(page, 'World Map');
    await page.waitForTimeout(1000);
    await screenshot(page, '20-world-map');
    
    // Verify map modal is open
    const mapModal = page.locator('[class*="modal"], [class*="overlay"]').first();
    const isMapVisible = await mapModal.isVisible();
    await log('MAP', `World map visible: ${isMapVisible}`);
    
    // Close map
    const closeButton = page.locator('button').filter({ hasText: /close|×|x/i }).first();
    if (await closeButton.isVisible()) {
      await closeButton.click();
    }
  });
  
  test('should travel to different location', async ({ page }) => {
    // Open World Map
    await clickQuickAction(page, 'World Map');
    await page.waitForTimeout(1000);
    await screenshot(page, '21-map-open');
    
    // Look for travel buttons (locations)
    const travelButtons = page.locator('button').filter({ 
      hasText: /forest|road|cave|goblin|camp|village/i 
    });
    
    const buttonCount = await travelButtons.count();
    await log('TRAVEL', `Found ${buttonCount} travel destination buttons`);
    
    if (buttonCount > 0) {
      const firstDest = await travelButtons.first().innerText();
      await travelButtons.first().click();
      await log('TRAVEL', `Clicked travel to: ${firstDest}`);
      await waitForDMResponse(page);
      await screenshot(page, '22-after-travel');
    }
  });
});

test.describe('Goblin Raid Scenario - Inventory & Shop', () => {
  
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    
    // Quick start
    await page.locator('input[type="text"]').first().fill('ShopHero');
    await page.locator('button').filter({ hasText: 'Fighter' }).first().click();
    await page.locator('button').filter({ hasText: /begin|start|create/i }).first().click();
    await waitForDMResponse(page);
  });
  
  test('should open and view inventory', async ({ page }) => {
    await clickQuickAction(page, 'Inventory');
    await page.waitForTimeout(1000);
    await screenshot(page, '30-inventory-open');
    
    // Check for inventory content
    const inventoryModal = page.locator('[class*="modal"], [class*="inventory"]').first();
    const isVisible = await inventoryModal.isVisible();
    await log('INVENTORY', `Inventory modal visible: ${isVisible}`);
    
    // Look for items
    const itemList = page.locator('[class*="item"], li').filter({ hasText: /gold|potion|sword|armor/i });
    const itemCount = await itemList.count();
    await log('INVENTORY', `Found ${itemCount} visible items`);
    
    // Close
    await page.keyboard.press('Escape');
  });
  
  test('should open and browse shop', async ({ page }) => {
    await clickQuickAction(page, 'Shop');
    await page.waitForTimeout(1000);
    await screenshot(page, '31-shop-open');
    
    // Check for shop content
    const pageContent = await page.locator('body').innerText();
    const hasShopContent = /buy|sell|gold|price|potion|weapon/i.test(pageContent);
    await log('SHOP', `Has shop content: ${hasShopContent}`);
    
    // Close
    await page.keyboard.press('Escape');
  });
});

test.describe('Goblin Raid Scenario - Quest Journal', () => {
  
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    
    // Quick start with Goblin scenario if available
    await page.locator('input[type="text"]').first().fill('QuestHero');
    await page.locator('button').filter({ hasText: 'Fighter' }).first().click();
    
    const goblinScenario = page.locator('button, div').filter({ hasText: /goblin/i }).first();
    if (await goblinScenario.isVisible()) {
      await goblinScenario.click();
    }
    
    await page.locator('button').filter({ hasText: /begin|start|create/i }).first().click();
    await waitForDMResponse(page);
  });
  
  test('should view quest journal', async ({ page }) => {
    await clickQuickAction(page, 'Quests');
    await page.waitForTimeout(1000);
    await screenshot(page, '40-quests-open');
    
    // Check for quest content
    const pageContent = await page.locator('body').innerText();
    const hasQuestContent = /quest|objective|goblin|reward|accept/i.test(pageContent);
    await log('QUEST', `Has quest content: ${hasQuestContent}`);
    
    // Close
    await page.keyboard.press('Escape');
  });
  
  test('should accept goblin quest from barkeep', async ({ page }) => {
    // Ask about work/quests
    await sendAction(page, 'I ask the barkeep if there is any work available');
    await screenshot(page, '41-ask-work');
    
    // Accept quest
    await sendAction(page, 'I accept the quest to deal with the goblins');
    await screenshot(page, '42-accept-quest');
    
    // Check quest journal
    await clickQuickAction(page, 'Quests');
    await page.waitForTimeout(1000);
    await screenshot(page, '43-quests-after-accept');
    
    // Close
    await page.keyboard.press('Escape');
  });
});

test.describe('Goblin Raid Scenario - Combat', () => {
  
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    
    // Quick start
    await page.locator('input[type="text"]').first().fill('CombatHero');
    await page.locator('button').filter({ hasText: 'Fighter' }).first().click();
    await page.locator('button').filter({ hasText: /begin|start|create/i }).first().click();
    await waitForDMResponse(page);
  });
  
  test('should initiate combat by attacking', async ({ page }) => {
    // Navigate towards goblins (or trigger combat scenario)
    await sendAction(page, 'I venture out looking for goblins to fight');
    await screenshot(page, '50-seek-combat');
    
    await sendAction(page, 'I attack the nearest goblin!');
    await screenshot(page, '51-attack-command');
    
    // Check if combat UI appeared
    const pageContent = await page.locator('body').innerText();
    const inCombat = /attack|damage|hit|roll|initiative|combat|hp/i.test(pageContent);
    await log('COMBAT', `Combat indicators found: ${inCombat}`);
    
    // Look for combat action buttons
    const attackButton = page.locator('button').filter({ hasText: /attack/i }).first();
    const defendButton = page.locator('button').filter({ hasText: /defend/i }).first();
    const fleeButton = page.locator('button').filter({ hasText: /flee/i }).first();
    
    await log('COMBAT', `Attack btn: ${await attackButton.isVisible()}, Defend btn: ${await defendButton.isVisible()}, Flee btn: ${await fleeButton.isVisible()}`);
    
    await screenshot(page, '52-combat-ui');
  });
  
  test('should use combat action buttons', async ({ page }) => {
    // First trigger combat
    await sendAction(page, 'I attack something!');
    await screenshot(page, '53-trigger-combat');
    
    // Try clicking attack button if visible
    const attackButton = page.locator('button').filter({ hasText: /⚔️.*attack/i }).first();
    if (await attackButton.isVisible()) {
      await attackButton.click();
      await log('COMBAT', 'Clicked Attack button');
      await waitForDMResponse(page);
      await screenshot(page, '54-after-attack');
    }
  });
});

test.describe('Goblin Raid Scenario - Full Playthrough', () => {
  
  test('complete tavern to goblin cave journey', async ({ page }) => {
    // Increase timeout for full playthrough
    test.setTimeout(120000);
    
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    
    // Create character
    await page.locator('input[type="text"]').first().fill('HeroOfWillowbrook');
    await page.locator('button').filter({ hasText: 'Fighter' }).first().click();
    await page.locator('button').filter({ hasText: 'Human' }).first().click();
    
    // Select Goblin scenario
    const goblinScenario = page.locator('button, div').filter({ hasText: /goblin/i }).first();
    if (await goblinScenario.isVisible()) {
      await goblinScenario.click();
    }
    
    await page.locator('button').filter({ hasText: /begin|start|create/i }).first().click();
    await waitForDMResponse(page);
    await screenshot(page, '60-playthrough-start');
    
    // 1. Explore tavern
    await sendAction(page, 'I look around the tavern to get my bearings');
    await screenshot(page, '61-explore-tavern');
    
    // 2. Talk to barkeep
    await sendAction(page, 'I approach the barkeep and ask about the goblin problem');
    await screenshot(page, '62-talk-barkeep');
    
    // 3. Accept quest
    await sendAction(page, 'I will help deal with the goblins. Where can I find them?');
    await screenshot(page, '63-accept-quest');
    
    // 4. Find and recruit Marcus
    await sendAction(page, 'I look for Marcus the sellsword to recruit him');
    await screenshot(page, '64-find-marcus');
    
    await sendAction(page, 'Marcus, will you join me on this goblin hunt? I could use a skilled warrior.');
    await screenshot(page, '65-recruit-marcus');
    
    // 5. Check party
    await clickQuickAction(page, 'Party');
    await page.waitForTimeout(1000);
    await screenshot(page, '66-check-party');
    await page.keyboard.press('Escape');
    
    // 6. Prepare at shop
    await clickQuickAction(page, 'Shop');
    await page.waitForTimeout(1000);
    await screenshot(page, '67-visit-shop');
    await page.keyboard.press('Escape');
    
    // 7. Set out
    await sendAction(page, 'I leave the tavern and head towards the goblin cave');
    await screenshot(page, '68-leave-tavern');
    
    // 8. Travel using world map
    await clickQuickAction(page, 'World Map');
    await page.waitForTimeout(1000);
    await screenshot(page, '69-world-map');
    
    // Try to travel to goblin-related location
    const goblinLocation = page.locator('button').filter({ 
      hasText: /goblin|cave|forest|camp/i 
    }).first();
    
    if (await goblinLocation.isVisible()) {
      const destName = await goblinLocation.innerText();
      await goblinLocation.click();
      await log('TRAVEL', `Traveling to: ${destName}`);
      await waitForDMResponse(page);
    } else {
      await page.keyboard.press('Escape');
    }
    
    await screenshot(page, '70-playthrough-end');
    
    // Final status check
    await log('COMPLETE', 'Full playthrough completed');
    
    // Capture final page content for analysis
    const finalContent = await page.locator('body').innerText();
    await log('FINAL', `Final content length: ${finalContent.length} chars`);
  });
});
