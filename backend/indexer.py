import uuid
from pathlib import Path
from llama_index.core import VectorStoreIndex, StorageContext, load_index_from_storage
from llama_index.core.schema import Document
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.core.node_parser import SentenceSplitter
from pypdf import PdfReader

BASE_DIR = Path(__file__).resolve().parent.parent
BASE_DATA = BASE_DIR / "data"
BASE_MODELS = BASE_DIR / "models"

embed_model = HuggingFaceEmbedding(model_name="sentence-transformers/all-MiniLM-L6-v2")

def extract_pages(pdf_path: str):
    reader = PdfReader(pdf_path)
    pages = []
    for i, page in enumerate(reader.pages):
        text = page.extract_text() or ""
        pages.append((i + 1, text))
    return pages

def create_session_from_file(file_obj, filename: str) -> str:
    session_id = str(uuid.uuid4())

    session_dir = BASE_DATA / session_id
    model_dir = BASE_MODELS / session_id

    session_dir.mkdir(parents=True, exist_ok=True)
    model_dir.mkdir(parents=True, exist_ok=True)

    file_path = session_dir / filename
    with open(file_path, "wb") as f:
        f.write(file_obj.read())

    build_index(file_path, model_dir)

    return session_id

def build_index(pdf_path: Path, model_dir: Path):
    pages = extract_pages(str(pdf_path))

    splitter = SentenceSplitter(chunk_size = 200, chunk_overlap = 40)
    documents = []

    for page_num, text in pages:
        chunks = splitter.split_text(text)
        for chunk in chunks:
            documents.append(
                Document(
                    text=chunk,
                    metadata={"page": page_num}
                )
            )

    index = VectorStoreIndex.from_documents(
        documents,
        embed_model=embed_model
    )

    index.storage_context.persist(persist_dir=str(model_dir))

def load_index(session_id: str):
    model_dir = BASE_MODELS / session_id
    storage_context = StorageContext.from_defaults(persist_dir = str(model_dir))

    return load_index_from_storage(storage_context, embed_model = embed_model)
