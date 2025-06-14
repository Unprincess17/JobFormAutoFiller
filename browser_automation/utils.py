import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

def get_default_value(element: Dict[str, Any], resume_data: Dict[str, Any]) -> str:
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

def extract_question_from_element(element: Dict[str, Any]) -> str:
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