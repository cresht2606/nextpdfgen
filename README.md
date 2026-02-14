# NextPDFGen
> **Your Absolute No-one-care Local PDF RAG assistant.**

NextPDFGen is a friendly, interactive web application that allow users, especially students to upload their PDF files onto AI-powered platform, wired up by conversations for further extension. This application relies on the RAG (Retrieval-Augmented Generation) architecture under the hood of local LLM qwen3 (8B version) for semantic interpretation and supports voice input / output for seamless experience.
---

## Key Features

* **Local-First Intelligence:** Powered by **Ollama**, utilizing the **Qwen 3 (4B)** model for high-performance semantic interpretation.
* **Voice-Enabled Interaction:** Hands-free learning with integrated **Voice Input and Output** for a more natural conversation flow.
* **Streamlined UI:** A neat, modern interface built with **Streamlit**, featuring persistent session history and intuitive controls.
* **Privacy by Design:** Your files stay on your hardware. No cloud, no leakage.
---

## Tech Stack

| Component | Technology |
| :--- | :--- |
| **Frontend** | Streamlit |
| **Inde** | LlamaIndex / RAG Architecture |
| **Local LLM** | Ollama (Qwen 3:4B-instruct) |
| **Vector Store** | Local FAISS |
| **Audio** | Speech-to-Text (openai-whisper) & Text-to-Speech (pyttsx3) Integration |

---

## Prerequisites

Before running the app, ensure you have the following installed:

1.  **Python 3.10+**
2.  **Ollama:** [Download here](https://ollama.ai/)
3.  **The Model:** Qwen3:4b-instruct

## Installation & Setup

1. **Clone the repository:**
   ```bash
   git clone [https://github.com/cresht2606/nextpdfgen.git](https://github.com/cresht2606/nextpdfgen.git)
   cd nextpdfgen
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Ruth the application:**
   ```bash
   streamlit run app.py
   ```
