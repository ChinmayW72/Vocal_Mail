from __future__ import print_function
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

# If modifying these scopes, delete the file token.pickle.
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]


def speak(text):
    engine = pyttsx3.init()
    voices = engine.getProperty('voices')
    engine.setProperty('voice', voices[1].id)
    rate = engine.getProperty('rate')
    engine.setProperty('rate', rate - 20)
    engine.say(text)
    engine.runAndWait()


speak("Welcome to mail service")


def get_audio():
    r = sr.Recognizer()

    # Set parameters for recording
    samplerate = 44100  # Sample rate
    duration = 3  # Duration of recording in seconds

    # Record audio
    print("Listening...")
    audio_data = sd.rec(int(samplerate * duration), samplerate=samplerate, channels=1, dtype='int16')
    sd.wait()  # Wait until recording is finished

    # Convert the recorded audio to a format compatible with SpeechRecognition
    audio_data = np.array(audio_data, dtype='int16').flatten()  # Flatten the array
    audio = sr.AudioData(audio_data.tobytes(), samplerate, 2)  # Create AudioData instance

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


def authenticate_gmail():
    creds = None
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


def check_mails(service):
    # Call the Gmail API to fetch all emails
    results = service.users().messages().list(userId='me', labelIds=["INBOX"]).execute()
    messages = results.get('messages', [])

    if not messages:
        print('No messages found.')
        speak('No messages found.')
    else:
        speak("{} emails found.".format(len(messages)))
        speak("Say 'read' to read a specific email or 'leave' to skip.")

        for message in messages:
            msg = service.users().messages().get(userId='me', id=message['id'], format='metadata').execute()
            for add in msg['payload']['headers']:
                if add['name'] == "From":
                    # fetching sender's email name
                    a = str(add['value'].split("<")[0])
                    print(a)
                    speak("Email from " + a)

                    command = get_audio()  # Listen for voice command

                    if "read" in command:
                        print(msg['snippet'])
                        # Speak up the mail
                        speak(msg['snippet'])
                    elif "leave" in command:
                        speak("Email passed.")
                    else:
                        speak("Command not recognized.")


SERVICE2 = authenticate_gmail()
check_mails(SERVICE2)
