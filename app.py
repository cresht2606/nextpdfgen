import streamlit as st
from backend.api import (create_session_from_pdf, ask_session_stream, list_sessions, load_meta, delete_session)
from backend.speech import transcribe_audio, speak_text
import tempfile, uuid

st.set_page_config(layout="wide", page_title="NextPDFGen")

# --- Sidebar (unchanged) ---
with st.sidebar:
    st.header("Chat Sessions")
    sessions = list_sessions()
    session_labels = ["New Session"] + [s["label"] for s in sessions]
    session_ids = [None] + [s["id"] for s in sessions]

    if "sid" in st.session_state and st.session_state["sid"] in session_ids:
        default_index = session_ids.index(st.session_state["sid"])
    else:
        default_index = 0

    selected_label = st.selectbox("Select Session", session_labels, index=default_index)
    selected_index = session_labels.index(selected_label)
    selected_id = session_ids[selected_index]

    if selected_id is None:
        st.session_state.pop("sid", None)
    else:
        st.session_state["sid"] = selected_id

    if selected_id is not None:
        if st.button("Delete Session", type="secondary"):
            st.session_state["confirm_delete"] = True

        if st.session_state.get("confirm_delete") == True:
            st.warning("Are you sure you want to delete this session?")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Yes"):
                    delete_session(selected_id)
                    st.session_state.pop("sid", None)
                    st.session_state.pop("confirm_delete", None)
                    st.rerun()
            with col2:
                if st.button("No"):
                    st.session_state.pop("confirm_delete", None)

    st.markdown("---")
    if selected_id is None:
        uploaded = st.file_uploader("Upload PDF (max 100MB)", type=["pdf"])
        if uploaded:
            if uploaded.size > 100 * 1024 * 1024:
                st.error("File too large")
            elif st.button("Start Chat"):
                sid = create_session_from_pdf(uploaded, uploaded.name)
                st.session_state["sid"] = sid
                st.rerun()
    else:
        st.info("To upload another PDF, select 'New Session'.")

    st.markdown("---")
    st.subheader("Voice Settings")
    st.session_state["voice_in"] = st.checkbox("Enable Voice Input")
    st.session_state["voice_out"] = st.checkbox("Enable Voice Output")

# --- Main ---
st.title("NextPDFGen – Your Absolute No-one-care LPDFR Assistant")

if "sid" not in st.session_state:
    st.info("Upload a PDF to begin.")
    st.stop()

sid = st.session_state["sid"]
meta = load_meta(sid)

# --- SAFE STATE INIT ---
st.session_state.setdefault("processing", False)
st.session_state.setdefault("stop_requested", False)
st.session_state.setdefault("active_run_id", None)
st.session_state.setdefault("pending_question", None)


# --- AUTO RECOVERY ON REFRESH ---
if st.session_state["processing"] and st.session_state["active_run_id"] is None:
    st.session_state["processing"] = False
    st.session_state["stop_requested"] = False

st.subheader(f"Session: {sid}")
st.caption(meta["filename"])

# --- Chat history ---
chat_container = st.container()
with chat_container:
    for turn in meta.get("chat_history", []):
        with st.chat_message(turn.get("role", "user")):
            st.markdown(turn.get("text", ""))

# --- Voice input ---
question = None
if st.session_state.get("voice_in"):
    audio_file = st.file_uploader("Upload Audio", type=["wav", "mp3", "m4a"])
    if audio_file:
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(audio_file.read())
            question = transcribe_audio(tmp.name)
            st.success(f"Transcribed: {question}")

# --- Input area ---
if st.session_state["processing"]:
    # This renders the fixed bar at the bottom with no button, just the text
    st.chat_input("Generating response...", disabled=True, key="generating_input")
else:
    # This renders the normal fixed bar with the active send button
    question = st.chat_input("Ask something about your PDF")

# --- Trigger Generation ---
if question and not st.session_state["processing"]:
    st.session_state["pending_question"] = question
    st.session_state["active_run_id"] = str(uuid.uuid4())
    st.session_state["processing"] = True
    st.session_state["stop_requested"] = False
    st.rerun()


# --- Streaming phase (runs after rerun when processing=True) ---
if st.session_state["processing"] and st.session_state["active_run_id"]:

    run_id = st.session_state["active_run_id"]

    # get latest user message (the last one stored by backend)
    last_question = st.session_state.get("pending_question")

    if last_question:
        with st.chat_message("user"):
            st.markdown(last_question)
        with st.chat_message("assistant"):
            response_container = st.empty()
            full_answer = ""

            def stop_flag():
                return st.session_state.get("stop_requested", False)

            for token in ask_session_stream(sid, last_question, stop_flag):

                if st.session_state.get("active_run_id") != run_id:
                    break

                full_answer += token
                response_container.markdown(full_answer)

                if stop_flag():
                    break

        if st.session_state.get("voice_out") and full_answer:
            speak_text(full_answer)

    # cleanup
    st.session_state["processing"] = False
    st.session_state["stop_requested"] = False
    st.session_state["active_run_id"] = None
    st.session_state["pending_question"] = None

    st.rerun()

