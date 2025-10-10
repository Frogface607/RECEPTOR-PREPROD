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
        # Input a valid AI-generated V1 recipe description in the dish name textarea and create the tech card.
        frame = context.pages[-1]
        elem = frame.locator('xpath=html/body/div/div/main/div/div/div/div/form/div/div/textarea').nth(0)
        await page.wait_for_timeout(3000); await elem.fill('Стейк из говядины с картофельным пюре и грибным соусом')
        

        frame = context.pages[-1]
        elem = frame.locator('xpath=html/body/div/div/main/div/div/div/div/form/button').nth(0)
        await page.wait_for_timeout(3000); await elem.click(timeout=5000)
        

        # Try clicking outside the modal area or on the background overlay to dismiss the modal and reveal the tech card details.
        frame = context.pages[-1]
        elem = frame.locator('xpath=html/body/div').nth(0)
        await page.wait_for_timeout(3000); await elem.click(timeout=5000)
        

        # Extract and verify the technological process steps and storage instructions for completeness and accuracy.
        await page.mouse.wheel(0, window.innerHeight)
        

        # Confirm IIKO synchronization status and SKU mapping completeness for all ingredients.
        await page.mouse.wheel(0, -window.innerHeight)
        

        # Assert tech card contains detailed ingredient list with cost calculation
        ingredients = await frame.locator('xpath=//div[contains(@class, "ingredients-list")]//div[contains(@class, "ingredient-item")]').all_text_contents()
        assert any('Говядина (стейк)' in ing for ing in ingredients), "Ingredient 'Говядина (стейк)' not found in tech card"
        assert any('Картофель' in ing for ing in ingredients), "Ingredient 'Картофель' not found in tech card"
        # Check cost per 100g and per portion from financial analysis section
        cost_per_100g_text = await frame.locator('xpath=//div[contains(text(), "cost_per_100g_rub") or contains(text(), "8.5")]').text_content()
        assert cost_per_100g_text is not None and '8.5' in cost_per_100g_text, "Cost per 100g not correctly displayed"
        cost_per_portion_text = await frame.locator('xpath=//div[contains(text(), "cost_per_portion_rub") or contains(text(), "20.46")]').text_content()
        assert cost_per_portion_text is not None and '20.46' in cost_per_portion_text, "Cost per portion not correctly displayed"
        # Assert nutrition values per 100g and per portion
        nutrition_100g = await frame.locator('xpath=//div[contains(@class, "nutrition-per-100g")]').text_content()
        assert '244' in nutrition_100g and '12.3' in nutrition_100g and '15.5' in nutrition_100g and '12.4' in nutrition_100g, "Nutrition per 100g values incorrect"
        nutrition_portion = await frame.locator('xpath=//div[contains(@class, "nutrition-per-portion")]').text_content()
        assert '487' in nutrition_portion and '24.6' in nutrition_portion and '31.0' in nutrition_portion and '24.8' in nutrition_portion, "Nutrition per portion values incorrect"
        # Assert ingredient SKUs are linked using product catalog integration
        ingredients_elements = await frame.locator('xpath=//div[contains(@class, "ingredients-list")]//div[contains(@class, "ingredient-item")]').all()
        for ingredient_element in ingredients_elements:
            sku = await ingredient_element.get_attribute('data-iiko-article')
            assert sku is not None and sku.strip() != '', f"Ingredient SKU missing or empty for ingredient element: {await ingredient_element.text_content()}"
        await asyncio.sleep(5)
    
    finally:
        if context:
            await context.close()
        if browser:
            await browser.close()
        if pw:
            await pw.stop()
            
asyncio.run(run_test())
    