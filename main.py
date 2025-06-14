#!/usr/bin/env python3
"""
JobFormAutoFiller - Main Entry Point
Automatically fill job application forms using resume data and AI assistance.
"""

import asyncio
import os
import logging
import yaml
import argparse
import sys
from pathlib import Path
from typing import Dict, Any, Optional

from resume_parser import ResumeParser
from ai_expansion import AIExpansion
from browser_automation import BrowserAutomation

# Configure logging
def setup_logging(log_level: str = "INFO", log_file: str = "automation.log"):
    """Setup logging configuration"""
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Create logs directory if it doesn't exist
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format=log_format,
        handlers=[
            logging.FileHandler(logs_dir / log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )

def load_config(config_path: str = "config.yaml") -> Dict[str, Any]:
    """Load configuration from YAML file"""
    try:
        with open(config_path, 'r') as file:
            config = yaml.safe_load(file)
        return config
    except FileNotFoundError:
        logging.error(f"Configuration file {config_path} not found")
        sys.exit(1)
    except yaml.YAMLError as e:
        logging.error(f"Error parsing configuration file: {e}")
        sys.exit(1)

def find_resume_file(resume_dir: str = "resumes") -> Optional[str]:
    """Find the first resume file in the resumes directory"""
    resume_dir_path = Path(resume_dir)
    
    if not resume_dir_path.exists():
        logging.error(f"Resume directory '{resume_dir}' not found")
        return None
    
    # Supported file extensions
    supported_extensions = ['.pdf', '.docx', '.doc']
    
    for file_path in resume_dir_path.iterdir():
        if file_path.suffix.lower() in supported_extensions:
            logging.info(f"Found resume file: {file_path}")
            return str(file_path)
    
    logging.error("No resume files found in resumes directory")
    return None

class JobFormAutoFiller:
    """Main application class that coordinates all components"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        self.resume_parser = ResumeParser()
        self.ai_expansion = AIExpansion(config.get('openai', {}))
        self.browser_automation = BrowserAutomation(config)
        
        self.resume_data: Optional[Dict[str, Any]] = None
    
    async def run(self, resume_file: str, target_url: Optional[str] = None):
        """Main execution flow"""
        try:
            self.logger.info("Starting JobFormAutoFiller...")
            
            # Step 1: Parse resume
            await self._parse_resume(resume_file)
            
            # Step 2: Start browser and navigate
            await self._setup_browser(target_url)
            
            while True:
                # Step 3: Wait for user interaction
                await self._wait_for_user_interaction()
                
                # Step 4: Auto-fill the form
                results = await self._auto_fill_form()
                
                # Step 5: Display results
                self._display_results(results)
                
                # Ask user if they want to fill another area
                continue_filling = await self.browser_automation.ask_continue_filling()
                if not continue_filling:
                    break
            
            # Keep browser open for user review
            await self._keep_browser_open()
            
        except KeyboardInterrupt:
            self.logger.info("Process interrupted by user")
        except Exception as e:
            self.logger.error(f"Error in main execution: {str(e)}")
            raise
        finally:
            await self._cleanup()
    
    async def _parse_resume(self, resume_file: str):
        """Parse the resume file"""
        self.logger.info("Parsing resume...")
        
        try:
            self.resume_data = self.resume_parser.parse_resume(resume_file)
            
            # Save parsed data
            output_file = self.config.get('resume_parsing', {}).get('output_file', 'parsed_resume.json')
            self.resume_parser.save_parsed_data(self.resume_data, output_file)
            
            self.logger.info("Resume parsing completed successfully")
            
            # Log summary of parsed data
            personal_info = self.resume_data.get('personal_info', {})
            self.logger.info(f"Parsed resume for: {personal_info.get('name', 'Unknown')}")
            self.logger.info(f"Email: {personal_info.get('email', 'Not found')}")
            self.logger.info(f"Found {len(self.resume_data.get('work_experience', []))} work experiences")
            self.logger.info(f"Found {len(self.resume_data.get('education', []))} education entries")
            self.logger.info(f"Found {len(self.resume_data.get('skills', []))} skills")
            
        except Exception as e:
            self.logger.error(f"Error parsing resume: {str(e)}")
            raise
    
    async def _setup_browser(self, target_url: Optional[str]):
        """Setup browser and navigate to target URL"""
        self.logger.info("Starting browser...")
        
        try:
            await self.browser_automation.start_browser()
            
            if target_url:
                await self.browser_automation.navigate_to_url(target_url)
            else:
                self.logger.info("No target URL provided. Please navigate to the job application form manually.")
                # Just open a blank page
                await self.browser_automation.navigate_to_url("about:blank")
            
        except Exception as e:
            self.logger.error(f"Error setting up browser: {str(e)}")
            raise
    
    async def _wait_for_user_interaction(self):
        """Wait for user to select form area and start auto-fill"""
        self.logger.info("Waiting for user to select form area...")
        
        try:
            # Wait for form area selection
            selected_area = await self.browser_automation.wait_for_form_selection()
            self.logger.info(f"User selected form area: {selected_area}")
            
            # Wait for user to start auto-fill
            await self.browser_automation.wait_for_autofill_start()
            self.logger.info("User initiated auto-fill process")
            
        except Exception as e:
            self.logger.error(f"Error waiting for user interaction: {str(e)}")
            raise
    
    async def _auto_fill_form(self) -> Dict[str, Any]:
        """Execute the auto-fill process"""
        self.logger.info("Starting auto-fill process...")
        
        try:
            results = await self.browser_automation.auto_fill_form(
                self.resume_data, 
                self.ai_expansion
            )
            
            self.logger.info("Auto-fill process completed")
            return results
            
        except Exception as e:
            self.logger.error(f"Error during auto-fill: {str(e)}")
            raise
    
    def _display_results(self, results: Dict[str, Any]):
        """Display the results of the auto-fill process"""
        self.logger.info("=== AUTO-FILL RESULTS ===")
        self.logger.info(f"Total fields found: {results['total_fields']}")
        self.logger.info(f"Fields successfully filled: {results['filled_fields']}")
        
        if results['errors']:
            self.logger.warning(f"Errors encountered: {len(results['errors'])}")
            for error in results['errors']:
                self.logger.warning(f"  - {error}")
        
        success_rate = (results['filled_fields'] / results['total_fields'] * 100) if results['total_fields'] > 0 else 0
        self.logger.info(f"Success rate: {success_rate:.1f}%")
        
        if results['success']:
            self.logger.info("Auto-fill completed successfully!")
        else:
            self.logger.error("Auto-fill completed with errors")
    
    async def _keep_browser_open(self):
        """Keep browser open for user review"""
        self.logger.info("Form filling completed. Browser will remain open for review.")
        self.logger.info("Press Ctrl+C to exit when you're done reviewing the form.")
        
        try:
            # Keep running until user interrupts
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            self.logger.info("Shutting down...")
    
    async def _cleanup(self):
        """Cleanup resources"""
        self.logger.info("Cleaning up...")
        try:
            await self.browser_automation.close_browser()
        except Exception as e:
            self.logger.error(f"Error during cleanup: {str(e)}")

def create_directory_structure():
    """Create necessary directories"""
    directories = ["resumes", "logs"]
    
    for dir_name in directories:
        dir_path = Path(dir_name)
        if not dir_path.exists():
            dir_path.mkdir(exist_ok=True)
            logging.info(f"Created directory: {dir_name}")

def check_environment():
    """Check if the environment is properly set up"""
    # Check for .env file
    env_file = Path(".env")
    if not env_file.exists():
        logging.warning("No .env file found. Please create one with your OPENAI_API_KEY")
        logging.info("Example: echo 'OPENAI_API_KEY=your-key-here' > .env")
    
    # Check for resume files
    resume_dir = Path("resumes")
    if not resume_dir.exists() or not any(resume_dir.iterdir()):
        logging.warning("No resume files found in resumes/ directory")
        logging.info("Please place your resume (PDF/Word) in the resumes/ folder")

async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="JobFormAutoFiller - Auto-fill job application forms")
    parser.add_argument("--resume", "-r", help="Path to resume file")
    parser.add_argument("--url", "-u", help="Target URL to navigate to")
    parser.add_argument("--config", "-c", default="config.yaml", help="Path to configuration file")
    parser.add_argument("--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"])
    
    args = parser.parse_args()

    # Load configuration
    config = load_config(args.config)

    # Setup logging
    logging_config = config.get('logging', {})
    setup_logging(
        args.log_level or logging_config.get('level', 'INFO'),
        logging_config.get('file', 'automation.log')
    )
    
    logger = logging.getLogger(__name__)
    logger.info("JobFormAutoFiller starting...")
    
    # Create directory structure
    create_directory_structure()
    
    # Check environment
    check_environment()

    # Add OPENAI_API_KEY to config
    # Priority: config.yaml > .env > os.getenv
    if not config.get('openai', {}).get('OPENAI_API_KEY'):
        config['openai']['OPENAI_API_KEY'] = os.getenv('OPENAI_API_KEY')
    
    # Find resume file
    resume_file = args.resume or find_resume_file()
    if not resume_file:
        logger.error("No resume file specified or found. Use --resume or place a file in resumes/")
        sys.exit(1)
    
    # Initialize and run the application
    try:
        app = JobFormAutoFiller(config)
        await app.run(resume_file, args.url)
    except Exception as e:
        logger.error(f"Application failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main()) 