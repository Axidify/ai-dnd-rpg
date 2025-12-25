/**
 * AI RPG E2E Test - Basic Game Flow
 * 
 * This test simulates a player:
 * 1. Creating a character
 * 2. Starting the game
 * 3. Taking some actions
 * 4. Checking the UI elements
 */

import { test, expect, Page } from '@playwright/test';

// Helper to log console messages to notes.log-compatible format
async function logGameEvent(category: string, message: string) {
  const timestamp = new Date().toTimeString().slice(0, 8);
  console.log(`[${timestamp}] [E2E-${category}] ${message}`);
}

test.describe('AI RPG Game Flow', () => {
  
  test('should load the game and create a character', async ({ page }) => {
    await logGameEvent('NAV', 'Navigating to game...');
    
    // Navigate to the game
    await page.goto('/');
    
    // Take screenshot of initial screen
    await page.screenshot({ path: 'e2e/screenshots/01-initial.png' });
    
    // Wait for the scenario selection or character creation screen
    await page.waitForLoadState('networkidle');
    
    await logGameEvent('LOAD', 'Page loaded');
    
    // Check if we're on character creation or game screen
    const pageContent = await page.content();
    
    if (pageContent.includes('Create Character') || pageContent.includes('Character Creation')) {
      await logGameEvent('UI', 'On character creation screen');
      await page.screenshot({ path: 'e2e/screenshots/02-character-creation.png' });
      
      // Fill in character name
      const nameInput = page.locator('input[type="text"]').first();
      if (await nameInput.isVisible()) {
        await nameInput.fill('TestHero');
        await logGameEvent('INPUT', 'Entered character name: TestHero');
      }
      
      // Look for start/create button
      const startButton = page.locator('button').filter({ hasText: /start|create|begin/i }).first();
      if (await startButton.isVisible()) {
        await startButton.click();
        await logGameEvent('ACTION', 'Clicked start button');
      }
    }
    
    await page.screenshot({ path: 'e2e/screenshots/03-after-start.png' });
  });

  test('should display game elements after starting', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    
    // Wait a moment for any animations
    await page.waitForTimeout(1000);
    
    // Take screenshot
    await page.screenshot({ path: 'e2e/screenshots/04-game-screen.png' });
    
    // Log what we see on the page
    const bodyText = await page.locator('body').innerText();
    await logGameEvent('CONTENT', `Page text length: ${bodyText.length} chars`);
    
    // Look for common game UI elements
    const hasChat = await page.locator('[class*="chat"], [class*="message"], [class*="narrative"]').count() > 0;
    const hasInput = await page.locator('input, textarea').count() > 0;
    const hasButtons = await page.locator('button').count();
    
    await logGameEvent('UI', `Chat area: ${hasChat}, Input: ${hasInput}, Buttons: ${hasButtons}`);
  });

  test('should be able to send a player action', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);
    
    // Find the input field for player actions
    const actionInput = page.locator('input[type="text"], textarea').first();
    
    if (await actionInput.isVisible()) {
      await actionInput.fill('I look around the room');
      await logGameEvent('ACTION', 'Typed: I look around the room');
      
      // Press Enter or find send button
      await actionInput.press('Enter');
      
      // Wait for response
      await page.waitForTimeout(3000);
      
      await page.screenshot({ path: 'e2e/screenshots/05-after-action.png' });
      await logGameEvent('RESPONSE', 'Action submitted, screenshot taken');
    } else {
      await logGameEvent('ERROR', 'Could not find action input field');
      await page.screenshot({ path: 'e2e/screenshots/05-no-input-found.png' });
    }
  });
});

test.describe('Game UI Components', () => {
  
  test('should capture full page screenshot', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000);
    
    // Full page screenshot
    await page.screenshot({ 
      path: 'e2e/screenshots/full-page.png',
      fullPage: true 
    });
    
    await logGameEvent('SCREENSHOT', 'Full page screenshot captured');
  });
  
  test('should list all visible buttons', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);
    
    const buttons = await page.locator('button').all();
    
    await logGameEvent('UI', `Found ${buttons.length} buttons:`);
    
    for (const button of buttons) {
      const text = await button.innerText();
      const isVisible = await button.isVisible();
      if (isVisible && text.trim()) {
        await logGameEvent('BUTTON', `  - "${text.trim()}"`);
      }
    }
  });
});
