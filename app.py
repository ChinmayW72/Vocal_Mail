from __future__ import print_function
import base64
from flask import Flask, render_template, request, redirect, url_for
import datetime
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import os
import pyttsx3
import speech_recognition as sr
import sounddevice as sd
import numpy as np

# Initialize Flask app
app = Flask(__name__)

# Google API scopes
SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send"  # Added permission to send emails
]

# Function to speak text
def speak(text):
    engine = pyttsx3.init()
    voices = engine.getProperty('voices')
    engine.setProperty('voice', voices[1].id)
    rate = engine.getProperty('rate')
    engine.setProperty('rate', rate - 20)
    engine.say(text)
    engine.runAndWait()

# Function to get audio input
def get_audio():
    r = sr.Recognizer()
    samplerate = 44100
    duration = 3
    print("Listening...")
    audio_data = sd.rec(int(samplerate * duration), samplerate=samplerate, channels=1, dtype='int16')
    sd.wait()
    audio_data = np.array(audio_data, dtype='int16').flatten()
    audio = sr.AudioData(audio_data.tobytes(), samplerate, 2)

    try:
        said = r.recognize_google(audio)
        print("You said: ", said)
        return said.lower()
    except sr.UnknownValueError:
        print("Could not understand the audio.")
        return ""
    except sr.RequestError:
        print("Could not request results from Google Speech Recognition service.")
        return ""

# Function to authenticate with Gmail
def authenticate_gmail():
    creds = None
    # Remove existing token if it exists
    if os.path.exists('token.pickle'):
        os.remove('token.pickle')  # Ensure we start fresh
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'C:\\Users\\SomeshP\\Downloads\\client_secret_671332084363-gh465e7arb1o6v45tcr65vsjhthivips.apps.googleusercontent.com.json',
                SCOPES)
            creds = flow.run_local_server(port=0)

        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = build('gmail', 'v1', credentials=creds)
    return service

# Route for the dashboard
@app.route('/')
def dashboard():
    return render_template('dashboard.html')

# Route to check mails
@app.route('/check_mails', methods=['GET', 'POST'])
def check_mails():
    service = authenticate_gmail()
    results = service.users().messages().list(userId='me', labelIds=["INBOX"]).execute()
    messages = results.get('messages', [])

    email_snippets = []
    if not messages:
        email_snippets.append('No messages found.')
    else:
        for message in messages:
            msg = service.users().messages().get(userId='me', id=message['id'], format='metadata').execute()
            for add in msg['payload']['headers']:
                if add['name'] == "From":
                    email_snippets.append((str(add['value'].split("<")[0]), msg['snippet']))

    return render_template('read_mail.html', email_snippets=email_snippets)

# Route to compose email
@app.route('/compose', methods=['GET', 'POST'])
def compose():
    if request.method == 'POST':
        # Get email details from the form
        recipient = request.form['recipient']
        subject = request.form['subject']
        body = request.form['body']

        service = authenticate_gmail()

        # Create email message
        message = {
            'raw': base64.urlsafe_b64encode(f'To: {recipient}\nSubject: {subject}\n\n{body}'.encode()).decode()
        }

        try:
            # Send email
            service.users().messages().send(userId='me', body=message).execute()
            print('Email sent successfully.')
        except Exception as e:
            print(f'An error occurred: {e}')
            return 'Failed to send email.'

        return redirect(url_for('dashboard'))

    return render_template('compose_mail.html')

# Run the Flask app
if __name__ == '__main__':
    app.run(debug=True)
