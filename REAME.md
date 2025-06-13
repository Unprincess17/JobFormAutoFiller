# JobFormAutoFiller - Auto-fill Job Application Forms with Your Resume  

Automatically fill job application forms using your resume data, with AI-powered expansion for abstract questions. Supports text boxes, radio buttons, checkboxes, and integrates with OpenAI for dynamic responses.  


## **Overview**  
JobFormAutoFiller is a tool that streamlines job application processes by:  
- **Parsing your resume** (PDF/Word) into structured data (e.g., education, work experience).  
- **Automatically filling forms** on job boards (e.g., LinkedIn, Boss直聘) using resume data.  
- **Generating extended answers** for abstract questions (e.g., "Describe your technical strengths") via OpenAI’s GPT-3.5/4.  
- **User-friendly interaction**: Let you "select a form area" in the browser to avoid accidental clicks.  


## **Design**

### Core Design Overview

The tool is built around four key modules that work together to automate form filling:

- Resume Parser: Converts raw resume files (PDF/Word) into structured data.
- Browser Automation Engine: Controls the browser to interact with form elements (text boxes, radio buttons, etc.).
- AI Expansion Module: Uses OpenAI’s GPT models to generate extended answers for abstract questions.
- User Interaction Layer: Lets you "select a form area" in the browser to scope automation.

### Key Tools & How They Work Together

1. Resume Parsing: PyPDF2 + python-docx + Custom NLP Rules

PyPDF2/PyMuPDF: Extracts text from PDF resumes (handles both text-based and scanned PDFs via optional OCR integration).
python-docx: Reads text from Word (.docx) files.
Custom NLP Rules & Regex: Parses extracted text into structured fields (e.g., "Education" → school, degree; "Work Experience" → company, role, achievements).

2. Browser Automation: Playwright

Why Playwright? It simulates human-like interactions (e.g., typing delays, mouse movements) to avoid bot detection, supports multiple browsers (Chrome/Edge), and offers robust element selection (XPath, CSS, text matching).
How it works: Controls the browser to navigate to the job form, locates elements within your selected "form area," and fills them using data from the parsed resume.

3. AI Expansion: OpenAI API

Role: Generates tailored answers for abstract questions (e.g., "Describe your greatest achievement") by combining resume data with GPT-3.5/4’s natural language capabilities.
Integration: The backend sends a prompt to OpenAI (including resume context and question details) and injects the generated response into the form’s text box.

4. User Interaction: Floating Panel + Form Area Selection

Floating Panel: A lightweight browser extension (or Playwright-injected UI) provides a "Select Form Area" button.
Selection Logic: When activated, the tool highlights form elements as you hover, letting you click to select the target area (e.g., the container of all input fields). This scopes automation to avoid accidental clicks on ads or navigation menus.

### End-to-End Workflow

You upload your resume (PDF/Word) → parsed into structured JSON.
Launch the tool → a browser window opens to your target job form.
Use the "Select Form Area" button to mark the form’s boundaries.
Click "Start Auto-Fill" → the tool:
Fills text boxes (e.g., name, email) with resume data.
Checks radio/checkboxes (e.g., "Highest Degree: Bachelor’s").
For abstract questions, sends resume context + question to OpenAI → injects the generated answer.

## **Key Features**  
| Feature                          | Description                                                                 |  
|----------------------------------|-----------------------------------------------------------------------------|  
| **Resume Parsing**               | Extracts structured data from PDF/Word resumes (name, education, skills, etc.). |  
| **Multi-Form Support**           | Handles text boxes, radio buttons, checkboxes, and dropdowns.                |  
| **AI Expansion**                 | Uses OpenAI API to generate tailored answers for abstract questions.         |  
| **Selection Box Interaction**    | Manually select the form area in the browser to scope automation.            |  
| **Anti-Detection**               | Simulates human-like input (delays, mouse movements) to avoid bot detection. |  


## **Prerequisites**  
- **Python 3.8+** (with `pip`).  
- **Browser**: Chrome or Edge (Playwright-supported).  
- **OpenAI API Key** (get one [here](https://platform.openai.com/)).  


## **Installation**  

### Step 1: Clone the Repository  
```bash  
git clone https://github.com/Unprincess17/JobFormAutoFiller.git  
cd JobFormAutoFiller  
```  

### Step 2: Install Dependencies  
```bash  
pip install -r requirements.txt  
```  

### Step 3: Set Up OpenAI API Key  
Create a `.env` file in the root directory:  
```env  
OPENAI_API_KEY=your-openai-api-key  
```  

### Step 4: Install Browser Drivers  
Run Playwright’s setup to install browser binaries:  
```bash  
playwright install  
```  


## **Usage**  

### 1. Upload Your Resume  
Place your resume (PDF/Word) in the `resumes/` folder. Example:  
```  
resumes/  
├── zhangsan_resume.pdf  
└── lisi_resume.docx  
```  

### 2. Launch the Tool  
```bash  
python main.py  
```  
A browser window will open. Navigate to the job application form you want to fill.  

### 3. Select the Form Area  
- Click the "Select Form Area" button in the tool’s floating panel.  
- Hover over the form (e.g., the container of input fields) and click to select it. The area will be highlighted.  

### 4. Start Automation  
Click "Start Auto-Fill". The tool will:  
- Parse your resume into structured data.  
- Fill text boxes (e.g., name, email) with resume data.  
- Check radio/checkboxes (e.g., "Highest Degree: Bachelor’s").  
- For abstract questions (e.g., "Why do you want this role?"), generate answers via OpenAI and fill them.  


## **Configuration**  

### Adjust OpenAI Settings (Optional)  
Modify `config.yaml` to change:  
- **Model**: Default `gpt-3.5-turbo` (switch to `gpt-4` for better quality).  
- **Temperature**: Controls answer randomness (0.5-1.0 recommended).  
- **Max Tokens**: Limit response length (e.g., 500 for 300-word answers).  

### Customize Resume Parsing (Advanced)  
Update `resume_parser.py` to add:  
- New regex patterns for extracting fields (e.g., GitHub links).  
- NLP rules for complex sections (e.g., project descriptions).  


## **Troubleshooting**  

### Resume Parsing Issues  
- For scanned PDFs, use OCR tools (e.g., Tesseract) to extract text first.  
- Manually edit `parsed_resume.json` if auto-parsing fails.  


## **Contributing**  
We welcome contributions! Submit issues for bugs/feature requests, or open PRs for code changes.  


## **License**  
MIT License. See `LICENSE` for details.  


---  
*Built with ❤️ by Unprincess17 and Bernicesbx. Let’s make job applications less tedious!*