import aiofiles
from pathlib import Path

async def extract_txt_metadata(file_path: Path) -> dict:
    metadata = {
        "type": "txt",
        "name": file_path.name,
        "path": str(file_path),
    }
    try:
        async with aiofiles.open(file_path, mode="r", encoding="utf-8", errors="ignore") as f:
            content = await f.read()
            metadata["line_count"] = content.count("\n") + 1
            metadata["word_count"] = len(content.split())
            metadata["summary"] = content[:200]  # Placeholder for NLP summary
    except Exception as e:
        metadata["error"] = str(e)
    return metadata