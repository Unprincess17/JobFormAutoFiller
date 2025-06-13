import json
import re
import os
from typing import Dict, List, Optional, Any
import PyPDF2
from docx import Document
import logging

logger = logging.getLogger(__name__)

class ResumeParser:
    def __init__(self):
        self.education_keywords = ['education', 'academic', 'university', 'college', 'school', 'degree', 'bachelor', 'master', 'phd', 'doctorate']
        self.experience_keywords = ['experience', 'work', 'employment', 'career', 'professional', 'job', 'position', 'role']
        self.skills_keywords = ['skills', 'technical', 'technologies', 'programming', 'languages', 'tools', 'frameworks']
        self.contact_keywords = ['contact', 'phone', 'email', 'address', 'linkedin', 'github']
        
    def parse_resume(self, file_path: str) -> Dict[str, Any]:
        """Parse resume from PDF or Word document"""
        try:
            file_extension = os.path.splitext(file_path)[1].lower()
            
            if file_extension == '.pdf':
                text = self._extract_pdf_text(file_path)
            elif file_extension in ['.docx', '.doc']:
                text = self._extract_docx_text(file_path)
            else:
                raise ValueError(f"Unsupported file format: {file_extension}")
            
            return self._parse_text_to_structured_data(text)
            
        except Exception as e:
            logger.error(f"Error parsing resume {file_path}: {str(e)}")
            raise
    
    def _extract_pdf_text(self, file_path: str) -> str:
        """Extract text from PDF file"""
        text = ""
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
        except Exception as e:
            logger.error(f"Error extracting PDF text: {str(e)}")
            raise
        return text
    
    def _extract_docx_text(self, file_path: str) -> str:
        """Extract text from Word document"""
        text = ""
        try:
            doc = Document(file_path)
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
        except Exception as e:
            logger.error(f"Error extracting DOCX text: {str(e)}")
            raise
        return text
    
    def _parse_text_to_structured_data(self, text: str) -> Dict[str, Any]:
        """Parse raw text into structured resume data"""
        resume_data = {
            "personal_info": self._extract_personal_info(text),
            "education": self._extract_education(text),
            "work_experience": self._extract_work_experience(text),
            "skills": self._extract_skills(text),
            "projects": self._extract_projects(text),
            "raw_text": text
        }
        
        return resume_data
    
    def _extract_personal_info(self, text: str) -> Dict[str, str]:
        """Extract personal information from resume text"""
        personal_info = {}
        
        # Extract name (usually in the first few lines)
        lines = text.split('\n')[:5]
        for line in lines:
            line = line.strip()
            if len(line) > 2 and len(line.split()) <= 4 and not any(char.isdigit() for char in line):
                if '@' not in line and 'phone' not in line.lower():
                    personal_info['name'] = line
                    break
        
        # Extract email
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        email_match = re.search(email_pattern, text)
        if email_match:
            personal_info['email'] = email_match.group()
        
        # Extract phone number
        phone_patterns = [
            r'\b\d{3}-\d{3}-\d{4}\b',
            r'\b\(\d{3}\)\s*\d{3}-\d{4}\b',
            r'\b\d{10}\b'
        ]
        for pattern in phone_patterns:
            phone_match = re.search(pattern, text)
            if phone_match:
                personal_info['phone'] = phone_match.group()
                break
        
        # Extract LinkedIn
        linkedin_pattern = r'linkedin\.com/in/[\w-]+'
        linkedin_match = re.search(linkedin_pattern, text, re.IGNORECASE)
        if linkedin_match:
            personal_info['linkedin'] = linkedin_match.group()
        
        # Extract GitHub
        github_pattern = r'github\.com/[\w-]+'
        github_match = re.search(github_pattern, text, re.IGNORECASE)
        if github_match:
            personal_info['github'] = github_match.group()
        
        return personal_info
    
    def _extract_education(self, text: str) -> List[Dict[str, str]]:
        """Extract education information"""
        education = []
        
        # Find education section
        lines = text.split('\n')
        in_education_section = False
        education_lines = []
        
        for line in lines:
            line = line.strip()
            if any(keyword in line.lower() for keyword in self.education_keywords):
                in_education_section = True
                continue
            
            if in_education_section:
                if any(keyword in line.lower() for keyword in self.experience_keywords + self.skills_keywords):
                    break
                if line:
                    education_lines.append(line)
        
        # Parse education entries
        current_entry = {}
        for line in education_lines:
            # Check for degree
            degree_patterns = [
                r'(bachelor|master|phd|doctorate|bs|ms|ba|ma|mba|degree)',
                r'(b\.s\.|m\.s\.|b\.a\.|m\.a\.|ph\.d\.)'
            ]
            for pattern in degree_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    current_entry['degree'] = line
                    break
            
            # Check for institution
            if 'university' in line.lower() or 'college' in line.lower() or 'institute' in line.lower():
                current_entry['institution'] = line
            
            # Check for year
            year_pattern = r'\b(19|20)\d{2}\b'
            year_match = re.search(year_pattern, line)
            if year_match:
                current_entry['year'] = year_match.group()
        
        if current_entry:
            education.append(current_entry)
        
        return education
    
    def _extract_work_experience(self, text: str) -> List[Dict[str, str]]:
        """Extract work experience information"""
        experience = []
        
        # Find experience section
        lines = text.split('\n')
        in_experience_section = False
        experience_lines = []
        
        for line in lines:
            line = line.strip()
            if any(keyword in line.lower() for keyword in self.experience_keywords):
                in_experience_section = True
                continue
            
            if in_experience_section:
                if any(keyword in line.lower() for keyword in self.education_keywords + self.skills_keywords):
                    break
                if line:
                    experience_lines.append(line)
        
        # Parse experience entries
        current_entry = {}
        for line in experience_lines:
            # Check for job title/position
            if any(word in line.lower() for word in ['engineer', 'developer', 'manager', 'analyst', 'specialist', 'coordinator']):
                current_entry['position'] = line
            
            # Check for company
            if 'inc' in line.lower() or 'corp' in line.lower() or 'llc' in line.lower() or 'ltd' in line.lower():
                current_entry['company'] = line
            
            # Check for dates
            date_pattern = r'\b(19|20)\d{2}\s*-\s*(19|20)\d{2}|\b(19|20)\d{2}\s*-\s*present'
            date_match = re.search(date_pattern, line, re.IGNORECASE)
            if date_match:
                current_entry['duration'] = date_match.group()
        
        if current_entry:
            experience.append(current_entry)
        
        return experience
    
    def _extract_skills(self, text: str) -> List[str]:
        """Extract skills information"""
        skills = []
        
        # Find skills section
        lines = text.split('\n')
        in_skills_section = False
        skills_lines = []
        
        for line in lines:
            line = line.strip()
            if any(keyword in line.lower() for keyword in self.skills_keywords):
                in_skills_section = True
                continue
            
            if in_skills_section:
                if any(keyword in line.lower() for keyword in self.education_keywords + self.experience_keywords):
                    break
                if line:
                    skills_lines.append(line)
        
        # Extract individual skills
        for line in skills_lines:
            # Split by common delimiters
            skill_items = re.split(r'[,;|•·\n]', line)
            for item in skill_items:
                item = item.strip()
                if item and len(item) > 1:
                    skills.append(item)
        
        return skills
    
    def _extract_projects(self, text: str) -> List[Dict[str, str]]:
        """Extract project information"""
        projects = []
        
        # Find projects section
        lines = text.split('\n')
        in_projects_section = False
        project_lines = []
        
        for line in lines:
            line = line.strip()
            if 'project' in line.lower():
                in_projects_section = True
                continue
            
            if in_projects_section:
                if any(keyword in line.lower() for keyword in self.education_keywords + self.experience_keywords + self.skills_keywords):
                    break
                if line:
                    project_lines.append(line)
        
        # Parse project entries
        current_project = {}
        for line in project_lines:
            if line and not current_project.get('name'):
                current_project['name'] = line
            elif line:
                current_project['description'] = line
                projects.append(current_project)
                current_project = {}
        
        return projects
    
    def save_parsed_data(self, data: Dict[str, Any], output_file: str = "parsed_resume.json"):
        """Save parsed resume data to JSON file"""
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            logger.info(f"Parsed resume data saved to {output_file}")
        except Exception as e:
            logger.error(f"Error saving parsed data: {str(e)}")
            raise 