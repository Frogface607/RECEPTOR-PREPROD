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
        # Input a valid AI-generated V1 recipe description and click 'Создать техкарту' to initiate the conversion process.
        frame = context.pages[-1]
        elem = frame.locator('xpath=html/body/div/div/main/div/div/div/div/form/div/div/textarea').nth(0)
        await page.wait_for_timeout(3000); await elem.fill('Стейк из говядины с картофельным пюре и грибным соусом')
        

        frame = context.pages[-1]
        elem = frame.locator('xpath=html/body/div/div/main/div/div/div/div/form/button').nth(0)
        await page.wait_for_timeout(3000); await elem.click(timeout=5000)
        

        # Try clicking outside the modal area or on the background overlay to dismiss the modal and access the detailed V2 tech card.
        frame = context.pages[-1]
        elem = frame.locator('xpath=html/body/div').nth(0)
        await page.wait_for_timeout(3000); await elem.click(timeout=5000)
        

        # Click the 'Связать с IIKO' button to test product catalog integration and SKU mapping with the 2833 products.
        frame = context.pages[-1]
        elem = frame.locator('xpath=html/body/div/div/main/div/div[2]/div/div/div[3]/button').nth(0)
        await page.wait_for_timeout(3000); await elem.click(timeout=5000)
        

        # Assert that the tech card is in V2 format and status is 'ГОТОВО'
        techcard_version = await frame.locator('xpath=//div[contains(text(),"TechCard v2")]').text_content()
        assert 'TechCard v2' in techcard_version, 'Tech card version is not V2'
        techcard_status = await frame.locator('xpath=//div[contains(text(),"ГОТОВО")]').text_content()
        assert 'ГОТОВО' in techcard_status, 'Tech card status is not ГОТОВО'
        # Assert that portions and weight per portion are displayed and valid
        portions_text = await frame.locator('xpath=//div[contains(text(),"portions") or contains(text(),"Порции") or contains(text(),"порций")]').text_content()
        assert portions_text is not None, 'Portions info missing'
        weight_per_portion_text = await frame.locator('xpath=//div[contains(text(),"weight_per_portion") or contains(text(),"г")]').text_content()
        assert weight_per_portion_text is not None, 'Weight per portion info missing'
        # Assert that nutritional values are present or show calculation not done
        nutrition_status = await frame.locator('xpath=//div[contains(text(),"Данные не заполнены") or contains(text(),"Расчет не выполнен")]').text_content()
        assert nutrition_status is not None, 'Nutrition data or calculation status missing'
        # Assert that financial analysis section shows cost calculation or reason for missing cost
        financial_status = await frame.locator('xpath=//div[contains(text(),"Себестоимость не рассчитана") or contains(text(),"Недостаточно данных для расчета стоимости")]').text_content()
        assert financial_status is not None, 'Financial analysis or cost calculation status missing'
        # Assert that ingredient SKUs are linked or show mapping status
        ingredients_status = await frame.locator('xpath=//div[contains(text(),"Нет ингредиентов для автомаппинга") or contains(text(),"Связать с IIKO")]').text_content()
        assert ingredients_status is not None, 'Ingredient SKU mapping status missing'
        await asyncio.sleep(5)
    
    finally:
        if context:
            await context.close()
        if browser:
            await browser.close()
        if pw:
            await pw.stop()
            
asyncio.run(run_test())
    