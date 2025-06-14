import openai
from openai import OpenAI
import json
import logging
from typing import Dict, Any, Optional
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class AIExpansion:
    def __init__(self, config: Dict[str, Any]):
        """Initialize OpenAI client with configuration"""
        self.openai_base_url = config.get('base_url')
        self.api_key = config.get('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("OpenAI API key not found. Please set OPENAI_API_KEY in your .env file")
        
        self.model = config.get('model', 'gpt-4o-mini')
        self.temperature = config.get('temperature', 0.7)
        self.max_tokens = config.get('max_tokens', 500)
        self.timeout = config.get('timeout', 30)
        
    def generate_answer(self, question: str, resume_data: Dict[str, Any], context: str = "") -> str:
        """Generate a tailored answer for abstract questions using resume data"""
        try:
            # Create a comprehensive prompt
            prompt = self._create_prompt(question, resume_data, context)
            
            # Call OpenAI API
            client = OpenAI(api_key=self.api_key, base_url=self.openai_base_url)
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a professional resume assistant helping to fill job application forms. Provide concise, professional answers based on the candidate's resume data."},
                    {"role": "user", "content": prompt}
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                timeout=self.timeout
            )
            
            answer = response.choices[0].message.content.strip()
            logger.info(f"Generated answer for question: {question[:50]}...")
            return answer
            
        except Exception as e:
            logger.error(f"Error generating AI answer: {str(e)}")
            # Return a fallback response
            return self._generate_fallback_answer(question, resume_data)
    
    def _create_prompt(self, question: str, resume_data: Dict[str, Any], context: str = "") -> str:
        """Create a comprehensive prompt for OpenAI"""
        
        # Extract key information from resume
        personal_info = resume_data.get('personal_info', {})
        education = resume_data.get('education', [])
        experience = resume_data.get('work_experience', [])
        skills = resume_data.get('skills', [])
        projects = resume_data.get('projects', [])
        
        prompt = f"""
Based on the following resume information, please provide a professional and tailored answer to the question below.

CANDIDATE INFORMATION:
Name: {personal_info.get('name', 'N/A')}
Email: {personal_info.get('email', 'N/A')}

EDUCATION:
"""
        
        for edu in education:
            prompt += f"- {edu.get('degree', 'N/A')} from {edu.get('institution', 'N/A')} ({edu.get('year', 'N/A')})\n"
        
        prompt += "\nWORK EXPERIENCE:\n"
        for exp in experience:
            prompt += f"- {exp.get('position', 'N/A')} at {exp.get('company', 'N/A')} ({exp.get('duration', 'N/A')})\n"
        
        prompt += f"\nSKILLS:\n{', '.join(skills[:10])}\n"  # Limit to first 10 skills
        
        if projects:
            prompt += "\nPROJECTS:\n"
            for proj in projects[:3]:  # Limit to first 3 projects
                prompt += f"- {proj.get('name', 'N/A')}: {proj.get('description', 'N/A')}\n"
        
        if context:
            prompt += f"\nADDITIONAL CONTEXT:\n{context}\n"
        
        prompt += f"""
QUESTION TO ANSWER:
{question}

INSTRUCTIONS:
1. Provide a professional, concise answer (150-300 words)
2. Use specific examples from the candidate's experience when relevant
3. Maintain a positive and confident tone
4. Focus on how the candidate's background relates to the question
5. Do not make up information not present in the resume
"""
        
        return prompt
    
    def _generate_fallback_answer(self, question: str, resume_data: Dict[str, Any]) -> str:
        """Generate a basic fallback answer when AI fails"""
        personal_info = resume_data.get('personal_info', {})
        skills = resume_data.get('skills', [])
        experience = resume_data.get('work_experience', [])
        
        # Basic template responses for common questions
        fallback_templates = {
            'why': f"Based on my background in {', '.join(skills[:3])}, I am excited about this opportunity to contribute my skills and experience.",
            'strength': f"My key strengths include {', '.join(skills[:5])}, which I have developed through my professional experience.",
            'experience': f"I have experience in {', '.join(skills[:3])} and have worked in roles that involved diverse responsibilities.",
            'motivation': "I am motivated by challenging opportunities that allow me to apply my skills and contribute to meaningful projects.",
            'goal': "My career goal is to continue growing professionally while making meaningful contributions to innovative projects.",
        }
        
        question_lower = question.lower()
        for keyword, template in fallback_templates.items():
            if keyword in question_lower:
                return template
        
        # Generic fallback
        return "I believe my background and experience make me a strong candidate for this position, and I am excited about the opportunity to contribute to your team."
    

    # TODO: Should use LLM to determine if a question requires AI expansion vs direct resume data
    def is_abstract_question(self, question: str, field_type: str = "text") -> bool:
        """Determine if a question requires AI expansion vs direct resume data"""
        abstract_keywords = [
            'why', 'describe', 'explain', 'tell us', 'what motivates', 'your greatest',
            'how would you', 'what interests you', 'your goals', 'your passion',
            'cover letter', 'personal statement', 'objective', 'summary'
        ]
        
        question_lower = question.lower()
        
        # Check if it's a text field that might need expansion
        if field_type == "textarea" or len(question) > 50:
            return True
        
        # Check for abstract question keywords
        return any(keyword in question_lower for keyword in abstract_keywords)
    
    def get_direct_answer(self, question: str, resume_data: Dict[str, Any]) -> Optional[str]:
        """Get direct answer from resume data for non-abstract questions"""
        question_lower = question.lower()
        personal_info = resume_data.get('personal_info', {})
        education = resume_data.get('education', [])
        experience = resume_data.get('work_experience', [])
        skills = resume_data.get('skills', [])
        
        # Direct mappings for common fields
        if 'name' in question_lower or 'full name' in question_lower:
            return personal_info.get('name', '')
        
        if 'email' in question_lower:
            return personal_info.get('email', '')
        
        if 'phone' in question_lower:
            return personal_info.get('phone', '')
        
        if 'linkedin' in question_lower:
            return personal_info.get('linkedin', '')
        
        if 'github' in question_lower:
            return personal_info.get('github', '')
        
        if 'university' in question_lower or 'school' in question_lower:
            if education:
                return education[0].get('institution', '')
        
        if 'degree' in question_lower:
            if education:
                return education[0].get('degree', '')
        
        if 'company' in question_lower or 'employer' in question_lower:
            if experience:
                return experience[0].get('company', '')
        
        if 'position' in question_lower or 'title' in question_lower:
            if experience:
                return experience[0].get('position', '')
        
        if 'skill' in question_lower:
            return ', '.join(skills[:5])  # Return top 5 skills
        
        return None 