import asyncio
from pathlib import Path
from PyPDF2 import PdfReader

async def extract_pdf_metadata(file_path: Path) -> dict:
    # Simulate async I/O
    await asyncio.sleep(0)
    metadata = {
        "type": "pdf",
        "name": file_path.name,
        "path": str(file_path),
    }
    try:
        reader = PdfReader(str(file_path))
        metadata["pages"] = len(reader.pages)
        text = ""
        for page in reader.pages:
            text += page.extract_text() or ""
        metadata["word_count"] = len(text.split())
        metadata["summary"] = text[:200]  # Placeholder for NLP summary
    except Exception as e:
        metadata["error"] = str(e)
    return metadata