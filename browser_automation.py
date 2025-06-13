import asyncio
import logging
import time
from typing import Dict, List, Any, Optional, Tuple
from playwright.async_api import async_playwright, Page, Browser, BrowserContext, ElementHandle
import json
import re

logger = logging.getLogger(__name__)

class BrowserAutomation:
    def __init__(self, config: Dict[str, Any]):
        """Initialize browser automation with configuration"""
        self.config = config
        self.browser_config = config.get('browser', {})
        self.automation_config = config.get('automation', {})
        
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        
        self.typing_delay = self.automation_config.get('typing_delay', 100)
        self.action_delay = self.automation_config.get('action_delay', 1000)
        self.max_retries = self.automation_config.get('max_retries', 3)
        
        self.selected_form_area: Optional[str] = None
        
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
            
            # Inject JavaScript for form area selection
            await self._inject_ui_scripts()
            
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
    
    async def _inject_ui_scripts(self):
        """Inject JavaScript for the floating UI panel"""
        ui_script = """
        // Create floating UI panel
        (function() {
            if (document.getElementById('job-form-autofiller-panel')) return;
            
            // Create panel
            const panel = document.createElement('div');
            panel.id = 'job-form-autofiller-panel';
            panel.style.cssText = `
                position: fixed;
                top: 20px;
                right: 20px;
                width: 250px;
                background: #ffffff;
                border: 2px solid #4CAF50;
                border-radius: 8px;
                box-shadow: 0 4px 12px rgba(0,0,0,0.15);
                padding: 15px;
                z-index: 10000;
                font-family: Arial, sans-serif;
                font-size: 14px;
            `;
            
            panel.innerHTML = `
                <div style="margin-bottom: 10px; font-weight: bold; color: #4CAF50;">
                    Job Form AutoFiller
                </div>
                <button id="select-form-area-btn" style="
                    width: 100%;
                    padding: 8px;
                    background: #4CAF50;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    cursor: pointer;
                    margin-bottom: 8px;
                ">Select Form Area</button>
                <button id="start-autofill-btn" style="
                    width: 100%;
                    padding: 8px;
                    background: #2196F3;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    cursor: pointer;
                    margin-bottom: 8px;
                " disabled>Start Auto-Fill</button>
                <div id="status-text" style="font-size: 12px; color: #666;">
                    Ready to select form area
                </div>
            `;
            
            document.body.appendChild(panel);
            
            // Form area selection functionality
            let isSelecting = false;
            let selectedArea = null;
            
            document.getElementById('select-form-area-btn').addEventListener('click', function() {
                if (isSelecting) {
                    stopSelection();
                } else {
                    startSelection();
                }
            });
            
            document.getElementById('start-autofill-btn').addEventListener('click', function() {
                window.jobFormAutoFiller = window.jobFormAutoFiller || {};
                window.jobFormAutoFiller.startAutofill = true;
            });
            
            function startSelection() {
                isSelecting = true;
                document.getElementById('select-form-area-btn').textContent = 'Cancel Selection';
                document.getElementById('select-form-area-btn').style.background = '#f44336';
                document.getElementById('status-text').textContent = 'Click on the form area to select it';
                
                document.addEventListener('mouseover', highlightElement);
                document.addEventListener('click', selectElement);
                document.body.style.cursor = 'crosshair';
            }
            
            function stopSelection() {
                isSelecting = false;
                document.getElementById('select-form-area-btn').textContent = 'Select Form Area';
                document.getElementById('select-form-area-btn').style.background = '#4CAF50';
                
                document.removeEventListener('mouseover', highlightElement);
                document.removeEventListener('click', selectElement);
                document.body.style.cursor = 'default';
                
                // Remove all highlights
                document.querySelectorAll('.autofiller-highlight').forEach(el => {
                    el.classList.remove('autofiller-highlight');
                });
            }
            
            function highlightElement(e) {
                if (!isSelecting) return;
                if (e.target.closest('#job-form-autofiller-panel')) return;
                
                // Remove previous highlights
                document.querySelectorAll('.autofiller-highlight').forEach(el => {
                    el.classList.remove('autofiller-highlight');
                });
                
                // Add highlight to current element
                e.target.classList.add('autofiller-highlight');
            }
            
            function selectElement(e) {
                if (!isSelecting) return;
                if (e.target.closest('#job-form-autofiller-panel')) return;
                
                e.preventDefault();
                e.stopPropagation();
                
                selectedArea = e.target;
                window.jobFormAutoFiller = window.jobFormAutoFiller || {};
                window.jobFormAutoFiller.selectedArea = e.target;
                
                // Mark as selected
                selectedArea.style.outline = '3px solid #4CAF50';
                
                stopSelection();
                
                document.getElementById('start-autofill-btn').disabled = false;
                document.getElementById('start-autofill-btn').style.background = '#2196F3';
                document.getElementById('status-text').textContent = 'Form area selected. Ready to auto-fill!';
            }
            
            // Add CSS for highlighting
            const style = document.createElement('style');
            style.textContent = `
                .autofiller-highlight {
                    outline: 2px solid #ff9800 !important;
                    outline-offset: 2px !important;
                }
            `;
            document.head.appendChild(style);
        })();
        """
        
        await self.page.add_script_tag(content=ui_script)
    
    async def wait_for_form_selection(self) -> str:
        """Wait for user to select a form area"""
        try:
            logger.info("Waiting for form area selection...")
            
            # Wait for the form area to be selected
            await self.page.wait_for_function(
                "window.jobFormAutoFiller && window.jobFormAutoFiller.selectedArea",
                timeout=300000  # 5 minutes timeout
            )
            
            # Get the selector for the selected area
            selected_element = await self.page.evaluate("""
                () => {
                    const element = window.jobFormAutoFiller.selectedArea;
                    const generateSelector = (el) => {
                        if (el.id) return '#' + el.id;
                        if (el.className) return '.' + el.className.split(' ').join('.');
                        return el.tagName.toLowerCase();
                    };
                    return generateSelector(element);
                }
            """)
            
            self.selected_form_area = selected_element
            logger.info(f"Form area selected: {selected_element}")
            return selected_element
            
        except Exception as e:
            logger.error(f"Error waiting for form selection: {str(e)}")
            raise
    
    async def wait_for_autofill_start(self):
        """Wait for user to click start auto-fill"""
        try:
            logger.info("Waiting for auto-fill to start...")
            
            await self.page.wait_for_function(
                "window.jobFormAutoFiller && window.jobFormAutoFiller.startAutofill",
                timeout=300000  # 5 minutes timeout
            )
            
            logger.info("Auto-fill started by user")
            
        except Exception as e:
            logger.error(f"Error waiting for autofill start: {str(e)}")
            raise
    
    async def get_form_elements(self) -> List[Dict[str, Any]]:
        """Get all form elements within the selected area"""
        try:
            if not self.selected_form_area:
                raise RuntimeError("No form area selected")
            
            form_elements = await self.page.evaluate(f"""
                () => {{
                    const formArea = document.querySelector('{self.selected_form_area}');
                    if (!formArea) return [];
                    
                    const elements = [];
                    const inputs = formArea.querySelectorAll('input, textarea, select');
                    
                    inputs.forEach((el, index) => {{
                        const rect = el.getBoundingClientRect();
                        const label = el.closest('label') || 
                                     document.querySelector(`label[for="${{el.id}}"]`) ||
                                     el.previousElementSibling;
                        
                        elements.push({{
                            index: index,
                            type: el.type || el.tagName.toLowerCase(),
                            tagName: el.tagName.toLowerCase(),
                            id: el.id,
                            name: el.name,
                            className: el.className,
                            placeholder: el.placeholder,
                            value: el.value,
                            required: el.required,
                            label: label ? label.textContent.trim() : '',
                            visible: rect.width > 0 && rect.height > 0,
                            selector: el.id ? `#${{el.id}}` : `input[name="${{el.name}}"]`
                        }});
                    }});
                    
                    return elements;
                }}
            """)
            
            logger.info(f"Found {len(form_elements)} form elements")
            return form_elements
            
        except Exception as e:
            logger.error(f"Error getting form elements: {str(e)}")
            raise
    
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
    
    async def update_status(self, status: str):
        """Update the status text in the UI panel"""
        try:
            await self.page.evaluate(f"""
                () => {{
                    const statusEl = document.getElementById('status-text');
                    if (statusEl) statusEl.textContent = '{status}';
                }}
            """)
        except Exception as e:
            logger.error(f"Error updating status: {str(e)}")
    
    async def auto_fill_form(self, resume_data: Dict[str, Any], ai_expansion) -> Dict[str, Any]:
        """Automatically fill the entire form"""
        results = {
            'filled_fields': 0,
            'total_fields': 0,
            'errors': [],
            'success': True
        }
        
        try:
            await self.update_status("Analyzing form fields...")
            
            # Get all form elements
            form_elements = await self.get_form_elements()
            results['total_fields'] = len(form_elements)
            
            await self.update_status(f"Found {len(form_elements)} fields. Starting auto-fill...")
            
            for element in form_elements:
                try:
                    if not element['visible']:
                        continue
                    
                    # Determine what value to fill
                    question = self._extract_question_from_element(element)
                    value = await self._get_field_value(question, element, resume_data, ai_expansion)
                    
                    if value:
                        success = await self.fill_form_field(
                            element['selector'], 
                            value, 
                            element['type']
                        )
                        
                        if success:
                            results['filled_fields'] += 1
                            await self.update_status(f"Filled {results['filled_fields']}/{results['total_fields']} fields")
                        else:
                            results['errors'].append(f"Failed to fill {element['selector']}")
                    
                except Exception as e:
                    error_msg = f"Error processing element {element.get('selector', 'unknown')}: {str(e)}"
                    results['errors'].append(error_msg)
                    logger.error(error_msg)
            
            await self.update_status(f"Completed! Filled {results['filled_fields']}/{results['total_fields']} fields")
            
        except Exception as e:
            results['success'] = False
            results['errors'].append(f"Form filling failed: {str(e)}")
            logger.error(f"Auto-fill form error: {str(e)}")
        
        return results
    
    def _extract_question_from_element(self, element: Dict[str, Any]) -> str:
        """Extract the question/label from a form element"""
        # Priority order: label, placeholder, name, id
        question = element.get('label', '').strip()
        if not question:
            question = element.get('placeholder', '').strip()
        if not question:
            question = element.get('name', '').replace('_', ' ').replace('-', ' ').strip()
        if not question:
            question = element.get('id', '').replace('_', ' ').replace('-', ' ').strip()
        
        return question
    
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
            return self._get_default_value(element, resume_data)
            
        except Exception as e:
            logger.error(f"Error getting field value for '{question}': {str(e)}")
            return ""
    
    def _get_default_value(self, element: Dict[str, Any], resume_data: Dict[str, Any]) -> str:
        """Get default value based on element type and resume data"""
        personal_info = resume_data.get('personal_info', {})
        
        # Default mappings for common field types
        field_type = element['type'].lower()
        
        if field_type == 'email':
            return personal_info.get('email', '')
        elif field_type == 'tel':
            return personal_info.get('phone', '')
        elif 'name' in element.get('name', '').lower():
            return personal_info.get('name', '')
        
        return "" 