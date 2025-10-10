import asyncio
from playwright import async_api

async def run_test():
    pw = None
    browser = None
    context = None
    
    try:
        # Start a Playwright session in asynchronous mode
        pw = await async_api.async_playwright().start()
        
        # Launch a Chromium browser in headless mode with custom arguments
        browser = await pw.chromium.launch(
            headless=True,
            args=[
                "--window-size=1280,720",         # Set the browser window size
                "--disable-dev-shm-usage",        # Avoid using /dev/shm which can cause issues in containers
                "--ipc=host",                     # Use host-level IPC for better stability
                "--single-process"                # Run the browser in a single process mode
            ],
        )
        
        # Create a new browser context (like an incognito window)
        context = await browser.new_context()
        context.set_default_timeout(5000)
        
        # Open a new page in the browser context
        page = await context.new_page()
        
        # Navigate to your target URL and wait until the network request is committed
        await page.goto("http://localhost:3000", wait_until="commit", timeout=10000)
        
        # Wait for the main page to reach DOMContentLoaded state (optional for stability)
        try:
            await page.wait_for_load_state("domcontentloaded", timeout=3000)
        except async_api.Error:
            pass
        
        # Iterate through all iframes and wait for them to load as well
        for frame in page.frames:
            try:
                await frame.wait_for_load_state("domcontentloaded", timeout=3000)
            except async_api.Error:
                pass
        
        # Interact with the page elements to simulate user flow
        # Click the 'ВОЙТИ' button to log in.
        frame = context.pages[-1]
        elem = frame.locator('xpath=html/body/div/div/header/div/div/div[2]/div[2]/button').nth(0)
        await page.wait_for_timeout(3000); await elem.click(timeout=5000)
        

        # Input the email '607orlov@gmail.com' into the email field.
        frame = context.pages[-1]
        elem = frame.locator('xpath=html/body/div/div/div/div/form/div/input').nth(0)
        await page.wait_for_timeout(3000); await elem.fill('607orlov@gmail.com')
        

        # Click the 'Войти' button to submit login form.
        frame = context.pages[-1]
        elem = frame.locator('xpath=html/body/div/div/div/div/form/div[2]/button[2]').nth(0)
        await page.wait_for_timeout(3000); await elem.click(timeout=5000)
        

        # Click on the 'AI-КУХНЯ' tab to navigate to the AI Kitchen recipe generation section.
        frame = context.pages[-1]
        elem = frame.locator('xpath=html/body/div/div/header/div/div/div[2]/nav/button[3]').nth(0)
        await page.wait_for_timeout(3000); await elem.click(timeout=5000)
        

        # Input a valid dish name into the recipe name input field.
        frame = context.pages[-1]
        elem = frame.locator('xpath=html/body/div/div/main/div/div[2]/div/div[2]/div/input').nth(0)
        await page.wait_for_timeout(3000); await elem.fill('Spicy Thai Basil Chicken')
        

        # Click the 'СОЗДАТЬ РЕЦЕПТ' button to trigger AI recipe generation.
        frame = context.pages[-1]
        elem = frame.locator('xpath=html/body/div/div/main/div/div[2]/div/div[2]/button').nth(0)
        await page.wait_for_timeout(3000); await elem.click(timeout=5000)
        

        # Assertion: Verify that recipe text is generated and contains rich descriptions and emojis.
        recipe_description = await frame.locator('xpath=//div[contains(text(),"Spicy Thai Basil Chicken")]/following-sibling::div').inner_text()
        assert recipe_description, "Recipe description should be present."
        assert any(emoji in recipe_description for emoji in ['🍽️', '🌶️', '🍗', '🥢', '🍜', '🔥', '✨', '😋', '🍴', '🍳', '🍲', '🍛', '🍤', '🍣', '🍱', '🍚', '🍙', '🍘', '🍥', '🥗', '🥘', '🥙', '🥪', '🥫', '🥓', '🥩', '🥚', '🥞', '🧀', '🍞', '🥖', '🥨', '🥯', '🥐', '🍔', '🍟', '🍕', '🌮', '🌯', '🥗', '🥙', '🥚', '🌶️']), "Recipe description should contain emojis."
        # Assertion: Verify no error messages are displayed.
        error_elements = await frame.locator('xpath=//div[contains(@class, "error") or contains(text(), "error") or contains(text(), "ошибка")]').count()
        assert error_elements == 0, "No error messages should be displayed on the page."]}  
        await asyncio.sleep(5)
    
    finally:
        if context:
            await context.close()
        if browser:
            await browser.close()
        if pw:
            await pw.stop()
            
asyncio.run(run_test())
    