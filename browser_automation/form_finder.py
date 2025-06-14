import logging
from typing import List, Dict, Any, Optional
from playwright.async_api import Page

logger = logging.getLogger(__name__)

class FormFinder:
    def __init__(self, page: Page):
        """Initialize form finder with page reference"""
        self.page = page
        self.selected_form_area: Optional[str] = None
        
    async def get_form_elements(self) -> List[Dict[str, Any]]:
        """Get all form elements within the selected area"""
        try:
            if not self.selected_form_area:
                raise RuntimeError("No form area selected")
            
            form_elements = await self.page.evaluate("""
                () => {
                    const selectedArea = window.jobFormAutoFiller.selectedArea;
                    if (!selectedArea) return [];
                    
                    const elements = [];
                    const inputs = selectedArea.querySelectorAll('input, textarea, select');
                    
                    inputs.forEach((el, index) => {
                        const rect = el.getBoundingClientRect();
                        const label = el.closest('label') || 
                                     document.querySelector(`label[for="${el.id}"]`) ||
                                     el.previousElementSibling;
                        
                        elements.push({
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
                            selector: el.id ? `#${el.id}` : `input[name="${el.name}"]`
                        });
                    });
                    
                    return elements;
                }
            """)
            
            logger.info(f"Found {len(form_elements)} form elements")
            return form_elements
            
        except Exception as e:
            logger.error(f"Error getting form elements: {str(e)}")
            raise
            
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