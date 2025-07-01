# AI Agent Chat with Email (Ollama + Gmail)

This project is a Streamlit-based AI agent that acts as a chat assistant. It uses a local LLM (Ollama) for natural language understanding and can send emails via the Gmail API when instructed.

## Features
- Chat with an AI agent powered by Ollama (e.g., Llama 3)
- The agent can send emails on your behalf when you ask it to inform, email, or contact someone
- If information is missing (like recipient email), the agent will ask for it
- All email sending is handled securely via the Gmail API

## Setup Instructions

### 1. Clone the Repository
```bash
git clone <your-repo-url>
cd <your-repo-folder>
```

### 2. Create and Activate a Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
# Or manually:
pip install streamlit requests google-api-python-client google-auth-httplib2 google-auth-oauthlib
```

### 4. Install and Run Ollama
- Download and install Ollama from [ollama.com/download](https://ollama.com/download)
- Start a model (e.g., llama3):
```bash
ollama run llama3
```

### 5. Set Up Gmail API Credentials
- Go to [Google Cloud Console](https://console.cloud.google.com/)
- Create a project, enable Gmail API, and create OAuth2 credentials (Desktop app)
- Download `credentials.json` and place it in your project folder (DO NOT COMMIT THIS FILE)

### 6. Run the App
```bash
streamlit run agent.py
```
- The app will open in your browser at [http://localhost:8501](http://localhost:8501)

## Security Warning
- **Never commit `credentials.json`, `token.pickle`, `.env`, or any secrets to your repository.**
- The `.gitignore` in this repo is set up to help prevent this.

## License
MIT (or your preferred license) 