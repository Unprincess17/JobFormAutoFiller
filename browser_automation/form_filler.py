import logging
import asyncio
from typing import Dict, Any
from playwright.async_api import Page

logger = logging.getLogger(__name__)

class FormFiller:
    def __init__(self, page: Page, config: Dict[str, Any]):
        """Initialize form filler with page reference and configuration"""
        self.page = page
        self.automation_config = config.get('automation', {})
        self.typing_delay = self.automation_config.get('typing_delay', 100)
        self.action_delay = self.automation_config.get('action_delay', 1000)
        
    async def fill_form_field(self, selector: str, value: str, field_type: str) -> bool:
        """Fill a specific form field"""
        try:
            await self._wait_and_delay()
            
            element = await self.page.wait_for_selector(selector, timeout=5000)
            if not element:
                logger.warning(f"Element not found: {selector}")
                return False
            
            # Scroll element into view
            await element.scroll_into_view_if_needed()
            await self._wait_and_delay()
            
            if field_type in ['text', 'email', 'tel', 'password', 'textarea']:
                # Clear existing content
                await element.click()
                await element.fill('')
                await self._wait_and_delay()
                
                # Type with human-like delay
                await element.type(value, delay=self.typing_delay)
                
            elif field_type == 'radio':
                # For radio buttons, we need to find the right option
                await self._select_radio_option(selector, value)
                
            elif field_type == 'checkbox':
                # Handle checkbox selection
                await self._handle_checkbox(selector, value)
                
            elif field_type == 'select':
                # Handle dropdown selection
                await element.select_option(value)
            
            logger.info(f"Filled field {selector} with value: {value[:50]}...")
            return True
            
        except Exception as e:
            logger.error(f"Error filling field {selector}: {str(e)}")
            return False
    
    async def _select_radio_option(self, base_selector: str, value: str):
        """Select radio button option based on value"""
        try:
            # Find all radio buttons with the same name
            radio_buttons = await self.page.query_selector_all(f"{base_selector}")
            
            for radio in radio_buttons:
                label_text = await self.page.evaluate("""
                    (radio) => {
                        const label = radio.closest('label') || 
                                     document.querySelector(`label[for="${radio.id}"]`) ||
                                     radio.nextElementSibling;
                        return label ? label.textContent.trim().toLowerCase() : '';
                    }
                """, radio)
                
                if value.lower() in label_text or label_text in value.lower():
                    await radio.click()
                    return
            
        except Exception as e:
            logger.error(f"Error selecting radio option: {str(e)}")
    
    async def _handle_checkbox(self, selector: str, value: str):
        """Handle checkbox based on value"""
        try:
            element = await self.page.wait_for_selector(selector)
            
            # Determine if checkbox should be checked
            should_check = value.lower() in ['yes', 'true', '1', 'on', 'checked']
            is_checked = await element.is_checked()
            
            if should_check and not is_checked:
                await element.check()
            elif not should_check and is_checked:
                await element.uncheck()
                
        except Exception as e:
            logger.error(f"Error handling checkbox: {str(e)}")
    
    async def _wait_and_delay(self):
        """Add human-like delay between actions"""
        await asyncio.sleep(self.action_delay / 1000) 