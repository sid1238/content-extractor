# content-extractor

A job search assistant that compares your resume with a job posting, scans it for common applicant tracking system (ATS) problems, and generates a one-page version tailored to the job.

It has a React frontend and a Flask backend. Resume text is processed on your own computer. The backend only goes online to fetch the job posting and, on first run, to download its models and checker.

## Features

### Resume and job match

On the **Find Match** page, upload a resume and paste a job URL, then select **Start match**. The result shows:

- An overall match percentage: skills count for 70% and experience for 30%. If the posting doesn't state the years required, the score uses skills only.
- The required skills found in your resume, and the ones missing.
- Whether you meet the experience requirement. Your years come from a figure stated in your resume, or else from your job dates, leaving out education dates and counting overlapping jobs once.

Skills are recognized from a fixed list in `backend/rag/matcher.py`, so a skill that isn't on the list won't be counted.

### ATS scan

Select **Scan for ATS issues** to check an uploaded resume. No job URL is needed. The report covers:

| Check | What it looks for |
|---|---|
| Contact and format | Missing phone number, email or LinkedIn link; missing standard section headings; tables, text boxes and images; contact details only in a page header or footer; more than 2 pages |
| Spelling and typos | Likely misspellings with suggestions, skipping names, employers and known tools |
| Grammar and tense | Grammar and punctuation errors, and present-tense wording under jobs that have ended |
| Date consistency | End dates before start dates, future dates, mixed date formats, jobs not listed newest first, overlaps, unexplained gaps, and stated years that don't match your job dates |
| Job titles, company and tool names | The same name written different ways, and a summary title that your job history doesn't support |
| Experience balance | Older or unrelated jobs that take up more space than your latest job |

### Tailored resume

Enter a resume and job URL, then select **Generate tailored resume**. A local AI model rewrites your experience bullets, project descriptions and any summary to fit the job. Skills are reordered so the job's skills come first. **Download resume** turns on once the new resume is ready, and it saves a one-page, single-column PDF.

The tailoring is designed to stay truthful:

- Your name, contact details, education, job titles, companies, dates, project names and section order are never rewritten.
- Rewrites that add numbers, tools or claims not backed by your resume are rejected, and so are rewrites that drop numbers or tools. Your original wording is kept instead.
- A job skill is added only if your resume or notes already show it. The rest are listed so you can see the gaps.
- Lines with no number are listed. To add one, enter a result you can back up under **Real results to include** and generate again.
- Every change is shown before and after. Review them before you send the resume, because a rewrite can still subtly change a line's meaning.

If a resume doesn't fit on one page at the smallest font size, the bullets least relevant to the job are removed and listed. A resume that still doesn't fit shows an error.

### Other pages

- **Find Match** also shows 24 sample job listings, 3 per row, with the company, role, experience and required skills.
- **Application** shows jobs you have applied to with their status, and the best-matching jobs you haven't applied to yet.
- **Profile** shows your name, email, phone, years of experience, interested roles and skills.
- **Resumes** shows 24 sample resumes that enlarge when selected.

These pages use sample data from `frontend/src/data/`. They aren't connected to the backend or to your uploaded resume.

## File requirements

Resumes must be PDF or Word (`.docx`) files of 2 MB or less. Older `.doc` files aren't supported. Scanned PDFs have no readable text, so export a text-based PDF instead.

## Requirements

- Node.js and npm
- Python 3.11
- [Ollama](https://ollama.com), for tailored resumes
- Java 17 or newer, for spelling and grammar checks in the ATS scan

## Setup

### Backend

From the project folder, create a virtual environment and install the dependencies:

```
python -m venv venv
venv\Scripts\activate
pip install -r backend/requirements.txt
```

On macOS or Linux, activate it with `source venv/bin/activate` instead.

Install the model used for tailored resumes, and make sure Ollama is running:

```
ollama pull llama3.1
```

Start the backend:

```
cd backend
python app.py
```

It runs at `http://127.0.0.1:5000`. Startup is slow because the question generation models load first, and the first run downloads them. The first ATS scan also downloads LanguageTool, the spelling and grammar checker, which is about 260 MB.

### Frontend

In a second terminal:

```
cd frontend
npm install
npm start
```

The app opens at `http://localhost:3000`.

### Optional settings

| Environment variable | Used for | Default |
|---|---|---|
| `REACT_APP_API_URL` | Backend address used by the frontend | `http://127.0.0.1:5000` |
| `OLLAMA_URL` | Ollama address | `http://127.0.0.1:11434` |
| `RESUME_LLM_MODEL` | Ollama model used for tailoring | `llama3.1:latest` |

## Limitations

- Some job sites block automated access or need JavaScript or a login to show a posting. LinkedIn, for example, returned an error when tested, and the page shows that error.
- Tailoring is slow on a CPU: about 6.5 minutes for a one-page resume when tested.
- Spelling is checked in US English, so British spellings may be flagged. Grammar checks can miss errors.
- Two-column PDF resumes haven't been tested, and their text may be read out of order.
- The tailored PDF doesn't keep the original resume's fonts or styling.
- The frontend test in `App.test.js` doesn't currently run, because the test runner can't load `react-router-dom`.

## Project structure

```
backend/
  app.py                 Flask routes
  rag/
    matcher.py           Job page fetching, skill and experience extraction, match score
    ats.py               ATS scan checks
    tailor.py            Resume rewriting, accuracy checks, PDF generation
    retriever.py         Reads text from uploaded PDF and Word files
    generator.py         Generates questions from a resume
frontend/src/
  App.js, Header.js      Routes and top bar
  pages/                 Application, Find Match, Profile and Resumes pages
  components/            Upload panel, ATS report and tailored resume results
  data/                  Sample jobs, resumes, applications and profile
```

## API routes

| Route | Purpose | Used by the current UI |
|---|---|---|
| `POST /match` | Compares a resume with a job URL | Yes |
| `POST /ats-scan` | Scans a resume for ATS issues | Yes |
| `POST /tailor` | Generates a tailored one-page PDF | Yes |
| `POST /upload` | Generates questions from an uploaded file | No |
| `POST /signup`, `POST /login`, `GET /profile/<email>` | User accounts, stored in a `rag_users` MySQL database | No |

The account routes need a MySQL database and the connection settings in `backend/app.py`. The other routes don't use the database. `frontend/src/firebase.js` contains placeholder settings and isn't used yet.
