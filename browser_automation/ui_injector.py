import logging
import asyncio
from typing import Optional
from playwright.async_api import Page

logger = logging.getLogger(__name__)

class UIInjector:
    def __init__(self, page: Page):
        """Initialize UI injector with page reference"""
        self.page = page
        
    async def inject_ui_scripts(self):
        """Inject JavaScript for the floating UI panel"""
        try:
            # Wait for the page to be ready
            await self.page.wait_for_load_state('domcontentloaded')
            
            # Check if the panel already exists
            panel_exists = await self.page.evaluate("""
                () => !!document.getElementById('job-form-autofiller-panel')
            """)
            
            if panel_exists:
                logger.info("UI panel already exists")
                return
                
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
            
            # Inject the script
            await self.page.add_script_tag(content=ui_script)
            
            # Verify the panel was created
            panel_created = await self.page.evaluate("""
                () => !!document.getElementById('job-form-autofiller-panel')
            """)
            
            if not panel_created:
                raise RuntimeError("Failed to create UI panel")
                
            logger.info("UI panel successfully injected")
            
        except Exception as e:
            logger.error(f"Error injecting UI scripts: {str(e)}")
            raise
            
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
            
    async def ask_continue_filling(self) -> bool:
        """Ask user if they want to fill another form area"""
        try:
            # Reset form selection state and update UI
            await self.page.evaluate("""
                () => {
                    const panel = document.getElementById('job-form-autofiller-panel');
                    if (!panel) return;
                    
                    // Reset form selection state
                    window.jobFormAutoFiller = window.jobFormAutoFiller || {};
                    window.jobFormAutoFiller.selectedArea = null;
                    window.jobFormAutoFiller.startAutofill = false;
                    
                    // Reset select form area button
                    const selectBtn = document.getElementById('select-form-area-btn');
                    if (selectBtn) {
                        selectBtn.textContent = 'Select Form Area';
                        selectBtn.style.background = '#4CAF50';
                    }
                    
                    // Reset start autofill button
                    const startBtn = document.getElementById('start-autofill-btn');
                    if (startBtn) {
                        startBtn.disabled = true;
                    }
                    
                    // Update status
                    const statusEl = document.getElementById('status-text');
                    if (statusEl) {
                        statusEl.textContent = 'Select another form area to continue filling';
                    }
                }
            """)
            
            # Wait for user to select another area or close
            try:
                await self.page.wait_for_function(
                    "window.jobFormAutoFiller && window.jobFormAutoFiller.selectedArea",
                    timeout=300000  # 5 minutes timeout
                )
                return True
            except Exception:
                # If timeout occurs, assume user wants to stop
                return False
            
        except Exception as e:
            logger.error(f"Error asking to continue filling: {str(e)}")
            return False 