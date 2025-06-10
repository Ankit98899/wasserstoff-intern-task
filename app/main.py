import os
import sys
import logging
import traceback 
from flask import Flask, render_template, request, redirect, url_for, flash
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
from langchain.llms import OpenAI
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import FAISS

# Load environment variables from .env file
load_dotenv()
#test:print(f"INFO: Loaded environment variables from .env file at {os.path.abspath('.env')}")
print("openai key:", os.getenv('OPENAI_API_KEY'))

# Initialize OpenAI API Key
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
if OPENAI_API_KEY:
    os.environ['OPENAI_API_KEY'] = OPENAI_API_KEY
else:
    raise ValueError("OPENAI_API_KEY not set in .env file")

# Setup LLM and Embeddings
llm = OpenAI()
embedding_model = OpenAIEmbeddings()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Adjust backend path for imports
_main_py_dir = os.path.dirname(os.path.realpath(__file__))
_backend_dir = os.path.dirname(_main_py_dir)
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

# Attempt to import DocumentChatService and constants
try:
    from app.api.vectorDb.database import (
        DocumentChatService,
        DEFAULT_DOCUMENTS_DIR,
        DEFAULT_FAISS_INDEX_PATH,
        DEFAULT_METADATA_PATH
    )
    SERVICE_IMPORTS_OK = True
    logger.info("Successfully imported DocumentChatService and path defaults.")
except ImportError as e:
    SERVICE_IMPORTS_OK = False
    logger.error(f"ERROR importing DocumentChatService and dependencies: {e}")
    DocumentChatService = None
    DEFAULT_DOCUMENTS_DIR = './documents'
    DEFAULT_FAISS_INDEX_PATH = None
    DEFAULT_METADATA_PATH = None

# Create Flask app
app = Flask(__name__, template_folder='templates')
app.secret_key = os.urandom(24)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

doc_chat_service_instance = None
services_are_initialized_successfully = False

def initialize_core_services(rebuild=False):
    global doc_chat_service_instance, services_are_initialized_successfully

    if not SERVICE_IMPORTS_OK or DocumentChatService is None:
        logger.error("Cannot initialize core services because imports failed.")
        services_are_initialized_successfully = False
        return

    try:
        doc_chat_service_instance = DocumentChatService(
            documents_dir=DEFAULT_DOCUMENTS_DIR,
            faiss_index_path=DEFAULT_FAISS_INDEX_PATH,
            metadata_path=DEFAULT_METADATA_PATH,
            rebuild_on_init=rebuild
        )
        index_ready = doc_chat_service_instance.faiss_index is not None
        groq_ready = getattr(doc_chat_service_instance, 'groq_client', None) is not None
        services_are_initialized_successfully = index_ready and groq_ready
        logger.info("Core services initialized successfully.")
    except Exception as e:
        logger.error(f"Initialization error: {e}")
        traceback.print_exc()
        services_are_initialized_successfully = False

initialize_core_services(rebuild=False)

ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'tiff', 'bmp'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    docs = []
    if doc_chat_service_instance and doc_chat_service_instance.metadata:
        try:
            unique_sources = {
                meta.get("source_doc")
                for meta in doc_chat_service_instance.metadata.get("metadata_store", {}).values()
                if meta.get("source_doc")
            }
            docs = [{"name": name} for name in sorted(unique_sources)]
        except Exception as e:
            logger.error(f"Failed to retrieve documents list: {e}")

    return render_template(
        "index.html",
        services_available=services_are_initialized_successfully,
        documents=docs
    )

@app.route('/upload', methods=['POST'])
def upload_files():
    if 'files[]' not in request.files:
        flash('No file part in request.', 'warning')
        return redirect(url_for('index'))

    files = request.files.getlist('files[]')
    if not files or all(f.filename == '' for f in files):
        flash('No files selected.', 'info')
        return redirect(url_for('index'))

    upload_dir = doc_chat_service_instance.documents_dir if doc_chat_service_instance else DEFAULT_DOCUMENTS_DIR
    os.makedirs(upload_dir, exist_ok=True)

    uploaded = 0
    for file in files:
        if file and allowed_file(file.filename):
            try:
                filename = secure_filename(file.filename)
                file.save(os.path.join(upload_dir, filename))
                uploaded += 1
            except Exception as e:
                logger.error(f"File save error: {e}")

    if uploaded:
        flash(f"{uploaded} file(s) uploaded. Re-index to include them.", "success")
    else:
        flash("No valid files uploaded.", "warning")

    return redirect(url_for('index'))

@app.route('/reindex', methods=['POST'])
def reindex_documents():
    flash("Re-indexing started...", "info")
    initialize_core_services(rebuild=True)
    if services_are_initialized_successfully:
        count = getattr(doc_chat_service_instance.faiss_index, 'ntotal', 'N/A')
        flash(f"Re-indexing completed. Index has {count} chunks.", "success")
    else:
        flash("Re-indexing failed. See logs.", "error")
    return redirect(url_for('index'))

@app.route('/query', methods=['POST'])
def query_documents():
    query = request.form.get('query', '').strip()
    if not query:
        flash("Enter a query.", "warning")
        return redirect(url_for('index'))

    if not services_are_initialized_successfully:
        flash("Services unavailable.", "error")
        return redirect(url_for('index'))

    try:
        response, doc_key = doc_chat_service_instance.process_query(query)
        if not response:
            flash("Query returned no response.", "info")
    except Exception as e:
        logger.error(f"Query error: {e}")
        flash("Query failed.", "error")
        response, doc_key = None, None

    docs = []
    if doc_chat_service_instance and doc_chat_service_instance.metadata:
        try:
            unique_sources = {
                meta.get("source_doc")
                for meta in doc_chat_service_instance.metadata.get("metadata_store", {}).values()
                if meta.get("source_doc")
            }
            docs = [{"name": name} for name in sorted(unique_sources)]
        except Exception as e:
            logger.error(f"Metadata refresh error: {e}")

    return render_template(
        "index.html",
        services_available=services_are_initialized_successfully,
        documents=docs,
        last_query=query,
        llm_response=response,
        doc_key=doc_key
    )

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal error: {error}")
    return "Internal server error", 500

if __name__ == '__main__':
    logger.info("App running at http://0.0.0.0:8080")
    app.run(debug=True, host='0.0.0.0', port=8080)