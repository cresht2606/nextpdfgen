import whisper, pyttsx3

_whisper_model = None

def get_whisper():
    global _whisper_model
    if _whisper_model is None:
        _whisper_model = whisper.load_model("base")
    return _whisper_model

def transcribe_audio(file_path):
    model = get_whisper()
    result = model.transcribe(file_path)
    return result["text"]

def speak_text(text):
    engine = pyttsx3.init()
    engine.say(text)
    engine.runAndWait()
