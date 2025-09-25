from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory
import os

# Ensure integration_layer is importable regardless of run context

import sys
import os
import importlib
APP_DIR = os.path.dirname(os.path.abspath(__file__))
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)
integration_layer = importlib.import_module('integration_layer')
get_all_metadata = integration_layer.get_all_metadata
run_neo4j_query = integration_layer.run_neo4j_query
process_file = integration_layer.process_file


app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Change this in production

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def get_uploaded_filenames():
    return [f for f in os.listdir(UPLOAD_FOLDER) if os.path.isfile(os.path.join(UPLOAD_FOLDER, f))]

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/admin')
def admin_dashboard():
    filenames = get_uploaded_filenames()
    knowledge_graph = {"nodes": ["A", "B"], "edges": [["A", "B"]]}
    ollama_summary = {"total_docs": len(filenames), "list": filenames, "keywords": ["AI", "Graph"], "domains": ["Tech"]}
    return render_template('admin_dash.html', filenames=filenames, knowledge_graph=knowledge_graph, ollama_summary=ollama_summary)


# Support uploading multiple files (folder upload)
@app.route('/upload_file', methods=['POST'])
def upload_file():
    files = request.files.getlist('file')
    if not files or files == [None]:
        flash('No files selected.', 'warning')
        return redirect(url_for('admin_dashboard'))
    success, errors = 0, 0
    for file in files:
        if file and file.filename:
            filepath = os.path.join(UPLOAD_FOLDER, file.filename)
            file.save(filepath)
            try:
                process_file(filepath)
                success += 1
            except Exception as e:
                flash(f'Error processing {file.filename}: {e}', 'danger')
                errors += 1
    if success:
        flash(f'{success} file(s) processed successfully!', 'success')
    if errors:
        flash(f'{errors} file(s) failed to process.', 'danger')
    return redirect(url_for('admin_dashboard'))

@app.route('/uploads/<filename>')

def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

@app.route('/view_metadata/<filename>')
def view_metadata(filename):
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    try:
        metadata = get_all_metadata()  # Replace with per-file if available
    except Exception as e:
        flash(f'Error loading metadata: {e}', 'danger')
        metadata = {}
    return render_template('view_metadata.html', filename=filename, metadata=metadata)

@app.route('/neo4j_query', methods=['GET', 'POST'])
def neo4j_query():
    result = None
    if request.method == 'POST':
        query = request.form.get('query')
        if query:
            try:
                result = run_neo4j_query(query)
            except Exception as e:
                flash(f'Error running query: {e}', 'danger')
    return render_template('admin_dash.html', result=result)

if __name__ == '__main__':
    app.run(debug=True)
