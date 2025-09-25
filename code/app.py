from flask import Flask, jsonify, render_template
import os, json, asyncio, time, hashlib
from datetime import datetime
import fitz  # PyMuPDF
from langdetect import detect
from modules.metadata_extractors import enrich_text  # NLP enrichment
from neo4j import GraphDatabase
from modules.neo4j_handler import Neo4jHandler
from modules import metadata_extractors 



app = Flask(__name__)

# Hardcoded paths
ROOT_FOLDER = r"C:\Users\ANIRUGHO\Desktop\Python\WOW_DEMO_LAB\Ollama + neo4j\KM_folder"
METADATA_DIR = r"C:\Users\ANIRUGHO\Desktop\Python\WOW_DEMO_LAB\Ollama + neo4j\metadata"
SITEMAP_DIR = r"C:\Users\ANIRUGHO\Desktop\Python\WOW_DEMO_LAB\Ollama + neo4j\sitemaps"

# Hardcoded Neo4j credentials
NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "graph@123"

driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
handler = Neo4jHandler(driver)

os.makedirs(SITEMAP_DIR, exist_ok=True)
os.makedirs(METADATA_DIR, exist_ok=True)

# -----------------------------
# Utility functions
# -----------------------------
def infer_tags(path):
    parts = path.replace("\\", "/").split("/")
    return {
        "domain": parts[0] if len(parts) > 0 else "Unknown",
        "region": parts[1] if len(parts) > 1 else "Unknown",
        "client": parts[2] if len(parts) > 2 else "Unknown"
    }

def file_hash(path):
    with open(path, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()

def detect_language(text):
    try:
        return detect(text)
    except:
        return "unknown"

def generate_quick_overview(text, max_chars=500):
    return text.strip().replace("\n", " ")[:max_chars]

# -----------------------------
# Sitemap builder
# -----------------------------
def build_sitemap(root_folder):
    entries = []
    for dirpath, _, filenames in os.walk(root_folder):
        print(f"Scanning: {dirpath}, found {len(filenames)} files")
        for fname in filenames:
            print(f"  -> {fname}")
            ext = os.path.splitext(fname)[1].lower()
            if ext != ".pdf":
                continue
            full_path = os.path.join(dirpath, fname)
            rel_path = os.path.relpath(full_path, root_folder)
            tags = infer_tags(rel_path)
            stat = os.stat(full_path)
            try:
                with fitz.open(full_path) as doc:
                    page_count = doc.page_count
                    text = doc[0].get_text("text") if page_count > 0 else ""
            except:
                page_count = 0
                text = ""
            entries.append({
                "id": file_hash(full_path)[:12],
                "filename": fname,
                "absolute_path": full_path,
                "relative_path": rel_path,
                "extension": ext,
                "domain": tags["domain"],
                "region": tags["region"],
                "client": tags["client"],
                "file_size_bytes": stat.st_size,
                "last_modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "page_count": page_count,
                "quick_overview": generate_quick_overview(text)
            })
    print(f"Total PDFs found: {len(entries)}")
    return entries

# -----------------------------
# PDF metadata extractor
# -----------------------------
def extract_pdf_text(file_path):
    text_chunks = []
    with fitz.open(file_path) as doc:
        for page in doc:
            text_chunks.append(page.get_text("text"))
    return "\n".join(text_chunks)

def extract_pdf_metadata(file_path):
    props = {}
    try:
        stat = os.stat(file_path)
        props["file_size_bytes"] = stat.st_size
        props["created_time"] = datetime.fromtimestamp(stat.st_ctime).isoformat()
        props["modified_time"] = datetime.fromtimestamp(stat.st_mtime).isoformat()
    except Exception as e:
        props["fs_meta_error"] = str(e)

    try:
        with fitz.open(file_path) as doc:
            props["page_count"] = doc.page_count
            props["pdf_metadata"] = doc.metadata or {}
    except Exception as e:
        props["pdf_meta_error"] = str(e)

    return props

async def process_pdf(entry, root_folder, preview_chars=1500):
    full_path = os.path.join(root_folder, entry["relative_path"])
    start = time.time()
    try:
        text = await asyncio.to_thread(extract_pdf_text, full_path)
        props = await asyncio.to_thread(extract_pdf_metadata, full_path)
        lang = detect_language(text)
        hash_val = file_hash(full_path)
        enrichment = await metadata_extractors.enrich_text(text, props.get("page_count", 0))
    except Exception as e:
        return {"error": str(e), "filename": entry["filename"]}

    elapsed = round(time.time() - start, 3)

    return {
        "id": hash_val[:12],
        "filename": entry["filename"],
        "relative_path": entry["relative_path"],
        "extension": entry["extension"],
        "tags": {
            "domain": entry["domain"],
            "region": entry["region"],
            "client": entry["client"]
        },
        "file_size_bytes": props.get("file_size_bytes"),
        "last_modified": props.get("modified_time"),
        "page_count": props.get("page_count"),
        "content_length": len(text),
        "pdf_metadata": props.get("pdf_metadata"),
        "hash": hash_val,
        "language": lang,
        "ingested_at": datetime.utcnow().isoformat(),
        "content_preview": text[:preview_chars],
        "overview_summary": enrichment["content_summary"]["summary"],
        "content_summary": enrichment["content_summary"],
        "classification": enrichment["classification"],
        "industry_tags": enrichment["industry_tags"],
        "entities": enrichment["entities"],
        "extraction_time_sec": elapsed
    }

async def process_all_pdfs(sitemap, root_folder):
    tasks = [process_pdf(entry, root_folder) for entry in sitemap]
    return await asyncio.gather(*tasks)

# -----------------------------
# Flask routes
# -----------------------------
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/ingest", methods=["GET"])
def ingest():
    sitemap = build_sitemap(ROOT_FOLDER)
    sitemap_path = os.path.join(SITEMAP_DIR, "sitemap.json")
    with open(sitemap_path, "w", encoding="utf-8") as f:
        json.dump(sitemap, f, indent=2, ensure_ascii=False)

    results = asyncio.run(process_all_pdfs(sitemap, ROOT_FOLDER))
    metadata_path = os.path.join(METADATA_DIR, "metadata.json")
    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    # Push to Neo4j
    for doc in results:
        if "id" in doc and "filename" in doc:
            handler.create_document_graph(doc)

    preview = json.dumps(results[:1], indent=2, ensure_ascii=False)
    return render_template("results.html", files_processed=len(results),
                           sitemap_file=sitemap_path,
                           metadata_file=metadata_path,
                           metadata_preview=preview)

@app.route("/view_sitemap")
def view_sitemap():
    path = os.path.join(SITEMAP_DIR, "sitemap.json")
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return jsonify(data)

@app.route("/view_metadata")
def view_metadata():
    path = os.path.join(METADATA_DIR, "metadata.json")
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return jsonify(data)
@app.route("/view_graph")
def view_graph():
    with driver.session() as session:
        result = session.run("""
            MATCH (a)-[r]->(b)
            RETURN a, r, b LIMIT 100
        """)
        nodes, edges = [], []
        seen = set()

        def node_color(label):
            colors = {
                "Document": "#1f77b4",   # blue
                "Client": "#2ca02c",     # green
                "Region": "#ff7f0e",     # orange
                "Domain": "#9467bd",     # purple
                "Industry": "#8c564b",   # brown
                "Technology": "#17becf", # teal
                "Partner": "#d62728",    # red
                "Product": "#bcbd22"     # yellow-green
            }
            return colors.get(label, "#7f7f7f")  # default grey

        for record in result:
            a, r, b = record["a"], record["r"], record["b"]

            # Add node a
            if a.id not in seen:
                label = list(a.labels)[0] if a.labels else "Node"
                nodes.append({
                    "id": a.id,
                    "label": label,
                    "title": dict(a),
                    "color": node_color(label)
                })
                seen.add(a.id)

            # Add node b
            if b.id not in seen:
                label = list(b.labels)[0] if b.labels else "Node"
                nodes.append({
                    "id": b.id,
                    "label": label,
                    "title": dict(b),
                    "color": node_color(label)
                })
                seen.add(b.id)

            # Add edge
            edges.append({
                "from": a.id,
                "to": b.id,
                "label": r.type
            })

    return render_template("graph.html",
                           nodes=json.dumps(nodes),
                           edges=json.dumps(edges))

# -----------------------------
# Run app
# -----------------------------
if __name__ == "__main__":
    app.run(debug=True, port=5000)

# When done:
driver.close()