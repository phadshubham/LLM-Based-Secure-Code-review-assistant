# LLM-Powered Secure Code Review Assistant for Student Projects

A complete, fully functional full-stack web application for reviewing the security of student software projects. It uses deterministic security scanners (Semgrep, Bandit, Trivy, ESLint, SpotBugs) for verified vulnerability detection and a local Qwen LLM via Ollama for student-friendly explanations and remediation guidance.

## Problem Statement
Students often write insecure code because they don't understand the security implications of their implementation choices. Traditional security scanners produce cryptic, hard-to-understand output, while raw LLMs can hallucinate vulnerabilities that don't exist.

## Objectives
1. Provide verified security findings using standard static analysis tools.
2. Explain vulnerabilities in simple, student-friendly language.
3. Keep the analysis local and free (no paid APIs).
4. Never automatically modify the student's project code.
5. Create a professional cybersecurity dashboard for clear visualization.

## Features
- **Project Upload:** Upload ZIP archives or link public GitHub repositories.
- **Language Detection:** Automatically detects Python, JavaScript, and Java.
- **Dependency Detection:** Finds package.json, requirements.txt, pom.xml, etc.
- **Security Scanners:** Runs Semgrep, Bandit, ESLint, SpotBugs, and Trivy depending on the language.
- **AI Explanations:** Sends verified findings to a local Qwen model (via Ollama) for explanation, impact assessment, and patch generation.
- **Security Score:** Calculates an educational security score.
- **Dashboard:** Modern, cybersecurity-themed React interface with charts and statistics.
- **Reports:** Generate and download PDF and JSON reports.
- **Sample Vulnerable Project:** Includes a deliberately vulnerable Python project for testing.

## Technology Stack
- **Frontend:** React, Vite, Tailwind CSS, Recharts, React Router
- **Backend:** Python, FastAPI, SQLAlchemy, SQLite, ReportLab
- **LLM:** Ollama, Qwen (qwen2.5-coder:3b recommended)
- **Scanners:** Semgrep, Bandit, Trivy, ESLint, SpotBugs

## Requirements
- Python 3.10+
- Node.js 18+
- Git
- Ollama
- Supported Scanners (must be available in PATH for their respective language support):
  - `semgrep`
  - `bandit`
  - `trivy`
  - `eslint`
  - `spotbugs` / `findbugs`

## Installation

### 1. Backend Setup
```bash
cd backend
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

pip install -r requirements.txt
cp .env.example .env
```

### 2. Frontend Setup
```bash
cd frontend
npm install
```

### 3. Ollama Setup
1. Install [Ollama](https://ollama.ai/)
2. Start the Ollama server:
   ```bash
   ollama serve
   ```
3. Pull the Qwen model:
   ```bash
   ollama pull qwen2.5-coder:3b
   ```

### 4. Security Tool Installation
Install the scanners you want to use. The system will gracefully skip scanners that are not installed.

**Python:**
```bash
pip install semgrep bandit
```

**JavaScript/Node:**
```bash
npm install -g eslint
```

**Trivy (System package):**
- [Install Trivy](https://aquasecurity.github.io/trivy/latest/getting-started/installation/)

**Java:**
- Install SpotBugs/FindBugs and ensure it's in your PATH.

## Environment Variables
The backend uses a `.env` file for configuration. See `backend/.env.example` for default values:

- `OLLAMA_BASE_URL`: The URL of your local Ollama server (default: `http://localhost:11434`)
- `OLLAMA_MODEL`: The Ollama model to use (default: `qwen2.5-coder:3b`)
- `DATABASE_URL`: SQLite database connection string
- `MAX_UPLOAD_SIZE_MB`: Maximum ZIP upload size
- `CONTEXT_LINES_BEFORE` / `CONTEXT_LINES_AFTER`: How much source code to extract around a finding

## How to Run

1. **Start the backend (from the `backend` directory):**
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```

2. **Start the frontend (from the `frontend` directory):**
   ```bash
   npm run dev
   ```

3. **Start Ollama (if not already running):**
   ```bash
   ollama serve
   ```

4. **Access the application:**
   Open your browser to `http://localhost:5173`

## Usage Guide
1. **Upload ZIP:** Go to "New Project", select "ZIP Upload", and drop a project ZIP file.
2. **Scan GitHub:** Go to "New Project", select "GitHub URL", and paste a public repository URL.
3. **Run Scan:** On the project details page, click "Run Security Scan".
4. **View Findings:** After the scan completes, click "View Full Results" to see the findings table, charts, and filtering options.
5. **Generate Reports:** Go to the "Reports" page to download PDF and JSON summaries.

## How to Run Tests
The backend includes a comprehensive pytest suite covering all system components.
```bash
cd backend
pytest tests/
```

## Known Limitations
- SpotBugs requires Java source files to be compilable (`javac`) to scan them effectively.
- Large repositories with many findings may take a long time for the LLM to process since it evaluates one finding at a time.
- The security score is an educational metric, not an industry standard.

## Security Considerations
- **Untrusted Code:** The application is designed to analyze untrusted code. Uploaded ZIPs are protected against path traversal, and the system never executes the uploaded applications.
- **Isolated Directories:** Each project is cloned or extracted into an isolated directory (`storage/projects/<uuid>`).
- **Subprocess Safety:** Scanners are invoked using safe subprocess arguments (no `shell=True`).
