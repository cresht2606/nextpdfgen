import json, uuid, shutil
from pathlib import Path
from datetime import datetime

from backend.indexer import create_session_from_file, load_index
from backend.llm import call_ollama_stream

BASE_DIR = Path(__file__).resolve().parent.parent
BASE_DATA = BASE_DIR / "data"
BASE_MODELS = BASE_DIR / "models"
_INDEX_CACHE = {}

def create_session_from_pdf(file_obj, filename: str) -> str:
    session_id = create_session_from_file(file_obj, filename)

    clean_name = Path(filename).stem.replace(" ", "_")

    meta = {
        "session_id": session_id,
        "display_name": clean_name,
        "filename": filename,
        "uploaded_at": datetime.utcnow().isoformat(),
        "chat_history": []
    }

    save_meta(session_id, meta)
    return session_id

def ask_session_stream(session_id: str, question: str, stop_flag_callable, top_k: int = 3):
    meta = load_meta(session_id)
    if not meta:
        yield "Session metadata not found."
        return

    if session_id not in _INDEX_CACHE:
        _INDEX_CACHE[session_id] = load_index(session_id)

    index = _INDEX_CACHE[session_id]

    retriever = index.as_retriever(similarity_top_k=top_k)
    nodes = retriever.retrieve(question)

    context_parts = []
    for node in nodes:
        page = node.metadata.get("page")
        context_parts.append(f"[Page {page}] {node.text}")

    context = "\n\n".join(context_parts)

    prompt = f"""
    You are a document-based AI assistant.

    You must answer ONLY using the provided document context.
    Do not use outside knowledge.
    Do not invent information.
    Do not invent page numbers.

    If the user requests a summary:
    - Identify the main topics and key points.
    - Write a clear and concise structured summary.
    - Preserve the original meaning.
    - Cite page numbers when they are explicitly available in the document.

    If the user asks a question:
    - Answer directly and concisely.
    - If the answer is not clearly stated in the document, say:
    "I couldn't find this in the document"
    - If the document provides partial information, give the closest relevant information and state that it is partial.
    - Cite page numbers when available in the document using format: (Page X)

    ---------------------
    DOCUMENT CONTEXT:
    {context}
    ---------------------

    Question:
    {question}

    Answer:
    """

    full_answer = ""

    # STREAM FROM OLLAMA
    for token in call_ollama_stream(prompt, stop_flag_callable):
        full_answer += token
        yield token

        if stop_flag_callable():
            break

    # SAVE CHAT HISTORY AFTER STREAM ENDS
    meta["chat_history"].append({"role": "user", "text": question})
    meta["chat_history"].append({"role": "assistant", "text": full_answer})
    save_meta(session_id, meta)


def is_valid_uuid(val):
    try:
        uuid.UUID(val)
        return True
    except ValueError:
        return False

def delete_session(session_id: str):
    if not session_id or not is_valid_uuid(session_id):
        return False
    
    data_dir = (BASE_DATA / session_id).resolve()
    model_dir = (BASE_MODELS / session_id).resolve()

    if not str(data_dir).startswith(str(BASE_DATA.resolve())):
        return False

    if not str(model_dir).startswith(str(BASE_MODELS.resolve())):
        return False

    try:
        if data_dir.exists():
            shutil.rmtree(data_dir)

        if model_dir.exists():
            shutil.rmtree(model_dir)
        
        _INDEX_CACHE.pop(session_id, None)

        return True
    
    except Exception as e:
        print(f"Deletion failed for {session_id}: {e}")
        return False

def save_meta(session_id: str, meta: dict):
    session_dir = BASE_DATA / session_id
    session_dir.mkdir(parents=True, exist_ok=True)
    with open(session_dir / "meta.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)

def load_meta(session_id: str):
    try:
        with open(BASE_DATA / session_id / "meta.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None

def list_sessions():
    sessions = []
    for d in BASE_DATA.iterdir():
        if d.is_dir() and (d / "meta.json").exists():
            meta = load_meta(d.name)
            sessions.append({
                "id": d.name,
                "label": meta.get("display_name", d.name)
            })
    return sessions
