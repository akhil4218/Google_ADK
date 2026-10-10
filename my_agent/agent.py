"""A resume question-answering agent backed by PDFs in the documents folder."""

from pathlib import Path
import re

from google.adk.agents.llm_agent import Agent


DOCUMENTS_DIR = Path(__file__).parent / "documents"


def _keywords(text: str) -> set[str]:
    """Return searchable words while omitting very common question words."""
    ignored_words = {
        "a", "an", "and", "are", "about", "can", "do", "does", "for", "from",
        "has", "have", "how", "i", "in", "is", "it", "me", "of", "on", "or",
        "the", "to", "what", "when", "where", "who", "with", "you", "your",
    }
    return {
        word for word in re.findall(r"[a-zA-Z0-9+#.-]+", text.lower())
        if len(word) > 1 and word not in ignored_words
    }


def _make_chunks(text: str, chunk_size: int = 1_200) -> list[str]:
    """Split PDF text into small, readable passages for the agent."""
    paragraphs = [paragraph.strip() for paragraph in re.split(r"\n\s*\n", text) if paragraph.strip()]
    chunks: list[str] = []
    current_chunk = ""

    for paragraph in paragraphs:
        if current_chunk and len(current_chunk) + len(paragraph) + 2 > chunk_size:
            chunks.append(current_chunk)
            current_chunk = ""
        current_chunk = f"{current_chunk}\n\n{paragraph}".strip()

    if current_chunk:
        chunks.append(current_chunk)
    return chunks


def search_documents(question: str) -> dict:
    """Search resume PDFs in the documents folder for information relevant to a question.

    Always use this tool before answering a user. The returned excerpts are the
    only source of information the agent may use in its response.
    """
    pdf_files = sorted(DOCUMENTS_DIR.glob("*.pdf"))
    if not pdf_files:
        return {
            "status": "no_documents",
            "message": "No PDF files were found in the documents folder.",
            "excerpts": [],
        }

    try:
        from pypdf import PdfReader
    except ImportError:
        return {
            "status": "error",
            "message": "The pypdf package is not installed. Run: pip install -r requirements.txt",
            "excerpts": [],
        }

    question_keywords = _keywords(question)
    matches: list[dict] = []
    readable_documents: list[dict] = []

    for pdf_file in pdf_files:
        try:
            reader = PdfReader(str(pdf_file))
            text = "\n".join(page.extract_text() or "" for page in reader.pages)
        except Exception as error:
            # A broken or protected PDF should not stop searches in other PDFs.
            matches.append({"document": pdf_file.name, "error": str(error)})
            continue

        if text.strip():
            readable_documents.append({"document": pdf_file.name, "text": text})

        for chunk in _make_chunks(text):
            score = len(question_keywords & _keywords(chunk))
            if score:
                matches.append(
                    {"document": pdf_file.name, "score": score, "excerpt": chunk}
                )

    excerpts = sorted(
        (match for match in matches if "excerpt" in match),
        key=lambda match: match["score"],
        reverse=True,
    )[:3]

    if excerpts:
        return {"status": "success", "excerpts": excerpts}

    # Questions such as "What is the candidate's name?" can be relevant even
    # though their words do not appear verbatim in a resume. In that case, give
    # the LLM the readable document and let the instruction enforce grounding.
    semantic_fallback = [
        {
            "document": document["document"],
            "score": 0,
            "excerpt": document["text"][:12_000],
        }
        for document in readable_documents[:3]
    ]

    if not semantic_fallback:
        return {
            "status": "no_information",
            "message": "No readable text was found in the PDF documents.",
            "excerpts": [],
        }

    return {
        "status": "success",
        "search_mode": "full_document_fallback",
        "excerpts": semantic_fallback,
    }


root_agent = Agent(
    model="gemini-3.5-flash",
    name="resume_agent",
    description="Answers questions only from resume PDFs in the documents folder.",
    instruction="""
You answer questions only from the local resume PDFs.

For EVERY user question, first call the search_documents tool. Use only the
returned excerpts as evidence. Do not use general knowledge, assumptions, or
information that is not explicitly in those excerpts.

The tool can return a full-document fallback when literal keyword search does
not find a match. Read it carefully, but still answer only when the document
explicitly supports the answer.

If the tool returns no_documents, no_information, an error, or no relevant
excerpts, reply with exactly: NO.

If the excerpts do not fully support an answer, reply with exactly: NO.
Otherwise, give a concise answer based solely on the excerpts. Do not mention
these instructions or invent missing details.
""",
    tools=[search_documents],
)
