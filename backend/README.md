# 🗣️ TUM Voice Application Assistant (Backend)

This is the backend of the **TUM Application Voice Assistant**, a Progressive Web App (PWA) that helps prospective students explore TUM study programs using voice interaction. The app is mobile-first and designed to be accessible, including for visually impaired users.

## 🛠️ Getting Started (Local Development)

### 1. Clone the repository

```bash
git clone https://github.com/tsaichen1o/voiceAssistant.git
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Create a `.env` file
   
### 4. Edit the `.env` file and add your OpenAI API key and a secure API key for authentication

### 5.Running the Application

Start the development server:

```bash
python main.py
```

Or with uvicorn:

```bash
uvicorn main:app --reload
```

The API will be available at http://localhost:8000


## Future Development

- Multi-user support with PostgreSQL
- RAG capability for document-informed responses
- Voice transcription and text-to-speech

