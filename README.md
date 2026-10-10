# Resume PDF Q&A Agent

A small [Google Agent Development Kit (ADK)](https://google.github.io/adk-docs/) project that answers questions only from PDF files placed in a local folder. If the PDFs do not explicitly support an answer, the agent replies with `NO`.

## How it works

1. The user asks a question.
2. The Gemini model calls the `search_documents` Python tool.
3. The tool reads PDFs from `my_agent/documents/` with `pypdf`.
4. It returns relevant text passages to the model.
5. The model answers using only those passages, or returns `NO`.

The implementation is designed for a small set of text-based PDFs, such as one or a few resumes. Scanned, image-only PDFs need OCR before their text can be searched.

## Project structure

```text
.
|-- my_agent/
|   |-- agent.py              # Agent and PDF-search tool
|   |-- .env.example          # Environment-variable template
|   `-- documents/            # Put local resume PDFs here
|-- requirements.txt
`-- README.md
```

## Prerequisites

- Python 3.10 or newer
- A Gemini API key from [Google AI Studio](https://aistudio.google.com/app/apikey)

## Setup

From the repository root:

### 1. Create and activate a virtual environment

**Windows PowerShell**

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**macOS/Linux**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure your API key

Copy the example file:

**Windows PowerShell**

```powershell
Copy-Item my_agent/.env.example my_agent/.env
```

**macOS/Linux**

```bash
cp my_agent/.env.example my_agent/.env
```

Open `my_agent/.env` and replace the placeholder:

```env
GOOGLE_GENAI_USE_ENTERPRISE=0
GOOGLE_API_KEY=your_gemini_api_key
```

Never commit `.env`; it is excluded by `.gitignore`.

### 4. Add PDFs

Copy one or more text-based resume PDFs into:

```text
my_agent/documents/
```

PDFs in this folder are also excluded from Git so private resume data is not published.

## Run the agent

Run the interactive command-line agent from the repository root:

```bash
adk run my_agent
```

Example questions:

```text
What is the candidate's name?
Which companies has the candidate worked for?
What programming languages are listed?
What is the capital of France?
```

The final question should return `NO` because that information is not in the resume.

To use the local ADK web interface instead:

```bash
adk web
```

Then open the local URL printed in the terminal and select `my_agent`.

Before publishing, check that `my_agent/.env` and PDFs inside `my_agent/documents/` are not included in `git status`.

## Limitations and next steps

- The current tool reads documents during each request, which is suitable only for a small number of PDFs.
- For many or large documents, use a RAG pipeline: extract text once, split it into chunks, generate embeddings, store them in a vector database, and retrieve only the most relevant chunks per question.
- Password-protected, corrupted, or image-only PDFs may not produce searchable text.
