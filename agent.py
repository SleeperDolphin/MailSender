import os
import streamlit as st
import requests
import base64
from email.mime.text import MIMEText
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import pickle
import re
import json

SCOPES = ['https://www.googleapis.com/auth/gmail.send']
OLLAMA_API_URL = "http://localhost:11434/v1/chat/completions"
OLLAMA_MODEL = "llama3"

# --- Gmail logic (same as before) ---
def get_gmail_service():
    creds = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    service = build('gmail', 'v1', credentials=creds)
    return service

def send_email(to, subject, body):
    message = MIMEText(body, 'plain')
    message['to'] = to
    message['subject'] = subject
    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
    service = get_gmail_service()
    try:
        message = service.users().messages().send(userId="me", body={"raw": raw}).execute()
        return True, f"Message Id: {message['id']}"
    except Exception as e:
        return False, str(e)

# --- Agent logic ---
def ollama_chat(messages):
    payload = {
        "model": OLLAMA_MODEL,
        "messages": messages
    }
    try:
        response = requests.post(OLLAMA_API_URL, json=payload)
        response.raise_for_status()
        data = response.json()
        content = data["choices"][0]["message"]["content"]
        return content.strip()
    except Exception as e:
        return f"Error: {e}"

# --- Streamlit Chat UI ---
st.set_page_config(page_title="AI Agent Chat", layout="centered")
st.title("AI Agent Chat (Ollama)")

if 'chat_history' not in st.session_state:
    st.session_state['chat_history'] = []
if 'mail_state' not in st.session_state:
    st.session_state['mail_state'] = {}

user_input = st.chat_input("Say something to your agent...")

if user_input:
    st.session_state['chat_history'].append({"role": "user", "content": user_input})
    st.rerun()

# Display chat history in a clean chat interface
for msg in st.session_state['chat_history']:
    if msg['role'] == 'user':
        with st.chat_message('user'):
            st.markdown(msg['content'])
    else:
        with st.chat_message('assistant'):
            st.markdown(msg['content'])

# Only process the agent's reply if the last message is from the user and not yet answered
if st.session_state['chat_history'] and st.session_state['chat_history'][-1]['role'] == 'user':
    # Improved system prompt for natural, context-aware behavior
    system_prompt = (
        "You are a helpful AI assistant. "
        "Behave like a normal chatbot and answer questions or chat naturally. "
        "Only offer to send an email if the user explicitly asks to inform, email, or contact someone, or if the context strongly suggests an email is needed (e.g., 'Can you let Alice know about the meeting?', or 'How am I going to tell ... about ...?'). "
        "If the user wants to send an email, extract the recipient, subject, and body. "
        "If any information is missing (especially the recipient email), ask the user for it in a conversational way, and do NOT say 'Sending email now...' or attempt to send until you have all three: recipient, subject, and body. "
        "You do not have to directly ask about what to write to the subject, just choose it according to your liking. Try not to ask many questions, just the necessary ones. "
        "When you have all the info, say 'Sending email now...' and stop. "
        "After that, the backend will send the email and inform the user. "
        "If the user is not asking to send an email, never mention your email capabilities."
    )
    messages = [{"role": "system", "content": system_prompt}] + st.session_state['chat_history']
    agent_reply = ollama_chat(messages)
    st.session_state['chat_history'].append({"role": "assistant", "content": agent_reply})
    with st.chat_message('assistant'):
        st.markdown(agent_reply)

    # Only try to extract and send email if the agent says 'Sending email now...'
    if 'sending email now' in agent_reply.lower():
        # Try to extract recipient, subject, and body from the conversation
        extract_prompt = (
            "From the previous conversation, extract the recipient email, subject, and body for the email. "
            "Reply with ONLY a valid JSON object with keys: recipient, subject, body. Do not include any explanation or extra text. "
            "If any are missing, use null."
        )
        extract_messages = messages + [{"role": "user", "content": extract_prompt}]
        extract_reply = ollama_chat(extract_messages)
        try:
            match = re.search(r'\{.*\}', extract_reply, re.DOTALL)
            if match:
                json_str = match.group(0)
                mail_info = json.loads(json_str)
            else:
                mail_info = json.loads(extract_reply)
            to = mail_info.get('recipient')
            subject = mail_info.get('subject')
            body = mail_info.get('body')
            if to and subject and body:
                with st.spinner("Sending email..."):
                    success, msg = send_email(to, subject, body)
                    if success:
                        st.session_state['chat_history'].append({"role": "assistant", "content": f"✅ Email sent to {to}!"})
                        with st.chat_message('assistant'):
                            st.markdown(f"✅ Email sent to {to}!")
                    else:
                        st.session_state['chat_history'].append({"role": "assistant", "content": f"❌ Failed to send email: {msg}"})
                        with st.chat_message('assistant'):
                            st.markdown(f"❌ Failed to send email: {msg}")
            else:
                st.session_state['chat_history'].append({"role": "assistant", "content": "❌ Could not extract all email fields. Please clarify recipient, subject, and body."})
                with st.chat_message('assistant'):
                    st.markdown("❌ Could not extract all email fields. Please clarify recipient, subject, and body.")
        except Exception as e:
            st.session_state['chat_history'].append({"role": "assistant", "content": f"❌ Error extracting email info: {e}\nRaw response: {extract_reply}"})
            with st.chat_message('assistant'):
                st.markdown(f"❌ Error extracting email info: {e}\nRaw response: {extract_reply}") 