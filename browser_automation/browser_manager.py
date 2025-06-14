import logging
from typing import Optional, Dict, Any
from playwright.async_api import async_playwright, Browser, BrowserContext, Page

logger = logging.getLogger(__name__)

class BrowserManager:
    def __init__(self, config: Dict[str, Any]):
        """Initialize browser manager with configuration"""
        self.config = config
        self.browser_config = config.get('browser', {})
        
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        
    async def start_browser(self):
        """Start the browser and create a new page"""
        try:
            playwright = await async_playwright().start()
            
            browser_type = self.browser_config.get('browser_type', 'chromium')
            headless = self.browser_config.get('headless', False)
            viewport = self.browser_config.get('viewport', {'width': 1280, 'height': 720})
            
            if browser_type == 'chromium':
                self.browser = await playwright.chromium.launch(
                    headless=headless,
                    args=[
                        '--disable-gpu',
                        '--disable-dev-shm-usage',
                        '--disable-setuid-sandbox',
                        '--no-sandbox',
                        '--disable-web-security',
                        '--disable-features=IsolateOrigins,site-per-process'
                    ]
                )
            elif browser_type == 'firefox':
                self.browser = await playwright.firefox.launch(headless=headless)
            elif browser_type == 'webkit':
                self.browser = await playwright.webkit.launch(headless=headless)
            else:
                raise ValueError(f"Unsupported browser type: {browser_type}")
            
            self.context = await self.browser.new_context(viewport=viewport)
            self.page = await self.context.new_page()
            
            logger.info(f"Browser started: {browser_type}")
            
        except Exception as e:
            logger.error(f"Error starting browser: {str(e)}")
            raise
    
    async def close_browser(self):
        """Close the browser"""
        try:
            if self.page:
                await self.page.close()
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            logger.info("Browser closed")
        except Exception as e:
            logger.error(f"Error closing browser: {str(e)}")
    
    async def navigate_to_url(self, url: str):
        """Navigate to a specific URL"""
        try:
            if not self.page:
                raise RuntimeError("Browser not started")
            
            await self.page.goto(url)
            await self.page.wait_for_load_state('networkidle')
            logger.info(f"Navigated to: {url}")
            
        except Exception as e:
            logger.error(f"Error navigating to {url}: {str(e)}")
            raise 