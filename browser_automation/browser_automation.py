import logging
import asyncio
from typing import Dict, Any, Optional
from playwright.async_api import Page

from .browser_manager import BrowserManager
from .ui_injector import UIInjector
from .form_finder import FormFinder
from .form_filler import FormFiller
from .utils import get_default_value, extract_question_from_element

logger = logging.getLogger(__name__)

class BrowserAutomation:
    def __init__(self, config: Dict[str, Any]):
        """Initialize browser automation with configuration"""
        self.config = config
        self.browser_manager = BrowserManager(config)
        self.ui_injector: Optional[UIInjector] = None
        self.form_finder: Optional[FormFinder] = None
        self.form_filler: Optional[FormFiller] = None
        
    async def start_browser(self):
        """Start the browser and initialize components"""
        await self.browser_manager.start_browser()
        self.ui_injector = UIInjector(self.browser_manager.page)
        self.form_finder = FormFinder(self.browser_manager.page)
        self.form_filler = FormFiller(self.browser_manager.page, self.config)
        
        # Add page load listener to re-inject UI
        self.browser_manager.page.on('load', lambda: asyncio.create_task(self.ui_injector.inject_ui_scripts()))
        
        # Initial UI injection
        await self.ui_injector.inject_ui_scripts()
    
    async def close_browser(self):
        """Close the browser"""
        await self.browser_manager.close_browser()
    
    async def navigate_to_url(self, url: str):
        """Navigate to a specific URL"""
        await self.browser_manager.navigate_to_url(url)
    
    async def wait_for_form_selection(self) -> str:
        """Wait for user to select a form area"""
        selected_area = await self.ui_injector.wait_for_form_selection()
        self.form_finder.selected_form_area = selected_area
        return selected_area
    
    async def wait_for_autofill_start(self):
        """Wait for user to click start auto-fill"""
        await self.ui_injector.wait_for_autofill_start()
    
    async def auto_fill_form(self, resume_data: Dict[str, Any], ai_expansion) -> Dict[str, Any]:
        """Automatically fill the entire form"""
        results = {
            'filled_fields': 0,
            'total_fields': 0,
            'errors': [],
            'success': True
        }
        
        try:
            await self.ui_injector.update_status("Analyzing form fields...")
            
            # Get all form elements
            form_elements = await self.form_finder.get_form_elements()
            results['total_fields'] = len(form_elements)
            
            await self.ui_injector.update_status(f"Found {len(form_elements)} fields. Starting auto-fill...")
            
            for element in form_elements:
                try:
                    logger.info(f"Processing element: {element}")
                    if not element['visible']:
                        continue
                    
                    # Determine what value to fill
                    question = extract_question_from_element(element)
                    value = await self._get_field_value(question, element, resume_data, ai_expansion)
                    
                    if value:
                        success = await self.form_filler.fill_form_field(
                            element['selector'], 
                            value, 
                            element['type']
                        )
                        
                        if success:
                            results['filled_fields'] += 1
                            await self.ui_injector.update_status(f"Filled {results['filled_fields']}/{results['total_fields']} fields")
                        else:
                            results['errors'].append(f"Failed to fill {element['selector']}")
                    else:
                        logger.warning(f"Cannot find value for {element['selector']}")
                    
                except Exception as e:
                    error_msg = f"Error processing element {element.get('selector', 'unknown')}: {str(e)}"
                    results['errors'].append(error_msg)
                    logger.error(error_msg)
            
            await self.ui_injector.update_status(f"Completed! Filled {results['filled_fields']}/{results['total_fields']} fields")
            
        except Exception as e:
            results['success'] = False
            results['errors'].append(f"Form filling failed: {str(e)}")
            logger.error(f"Auto-fill form error: {str(e)}")
        
        return results
    
    async def _get_field_value(self, question: str, element: Dict[str, Any], resume_data: Dict[str, Any], ai_expansion) -> str:
        """Get the appropriate value for a form field"""
        try:
            # First try to get direct answer from resume data
            direct_answer = ai_expansion.get_direct_answer(question, resume_data)
            if direct_answer:
                return direct_answer
            
            # Check if it's an abstract question that needs AI expansion
            if ai_expansion.is_abstract_question(question, element['type']):
                return ai_expansion.generate_answer(question, resume_data)
            
            # Default fallback based on field type
            return get_default_value(element, resume_data)
            
        except Exception as e:
            logger.error(f"Error getting field value for '{question}': {str(e)}")
            return ""
    
    async def ask_continue_filling(self) -> bool:
        """Ask user if they want to fill another form area"""
        return await self.ui_injector.ask_continue_filling() 