from playwright.async_api import async_playwright
import asyncio

class BrowserTool:
    """
    Playwright-based browser automation.
    """
    
    def __init__(self):
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        
    async def initialize(self):
        if not self.playwright:
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(headless=True)
            self.context = await self.browser.new_context()
            self.page = await self.context.new_page()
            
    async def close(self):
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
        
    async def goto(self, url: str) -> str:
        """Navigates to a URL."""
        await self.initialize()
        try:
            await self.page.goto(url, wait_until="networkidle")
            return f"Successfully navigated to: {url}"
        except Exception as e:
            return f"Failed to navigate to {url}: {str(e)}"
        
    async def get_page_content(self) -> str:
        """Returns simplified text content of the page."""
        if not self.page:
            return "Error: Browser not initialized or no page open."
        try:
            # Extract plain text from body, removing scripts/styles
            text_content = await self.page.evaluate('''() => {
                const body = document.body;
                return body ? body.innerText : '';
            }''')
            # Truncate to avoid exploding the context window
            return text_content[:4000] if text_content else "Page is empty."
        except Exception as e:
            return f"Error extracting page content: {str(e)}"
            
    async def navigate_and_extract(self, url: str) -> str:
        """Helper to navigate and immediately extract text."""
        await self.initialize()
        try:
            await self.page.goto(url, wait_until="networkidle", timeout=15000)
            text_content = await self.page.evaluate('''() => {
                const body = document.body;
                return body ? body.innerText : '';
            }''')
            await self.close()
            return f"Content from {url}:\n" + (text_content[:4000] if text_content else "Page is empty.")
        except Exception as e:
            await self.close()
            return f"Error explicitly fetching {url}: {str(e)}"
