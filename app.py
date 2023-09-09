import os, csv
from flask import Flask, flash, request, redirect, url_for
from werkzeug.utils import secure_filename
## MP4 TO MP3 CONVERTER ##
from moviepy.editor import *

## EMAIL SENDING ##
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content

## METAPHOR ##
from metaphor_python import Metaphor

import smtplib

from dotenv import load_dotenv

import openai

UPLOAD_FOLDER = './uploads'
ALLOWED_EXTENSIONS = {'mp4'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['SECRET_KEY'] = os.getenv("FLASK_SECRET")

load_dotenv()

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def converter(filename):
    video = VideoFileClip("./uploads/" + filename)
    video.audio.write_audiofile("./uploads/audiofile.mp3")

    # try catch delete video

def transcribe(filename):
    fileInQuestion = open("./uploads/" + filename, "rb")
    transcript = openai.Audio.transcribe("whisper-1", fileInQuestion)

    # try catch delete audiofile

    print(transcript)

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        if 'file' not in request.files:
            return 'No file part'

        file = request.files['file']

        if file.filename == '':
            return 'No selected file'

        if file and allowed_file(file.filename):
            filename = "videofile.mp4"
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            converter(filename)
            transcribe("audiofile.mp3")
            return "Done!"

    return "hello"

def metaphor_test():
    metaphor = Metaphor(os.getenv("METAPHOR_API_KEY"))
    summary = "On September 8th, 2023, The Code Report highlighted significant developments in the world of software development. SOI developers celebrated Mojo's general availability, a Python superset boasting remarkable speed gains. Meanwhile, JavaScript received a boost in performance thanks to Bun, a versatile Swiss Army Knife tool. Bun not only accelerates JavaScript execution but also functions as a bundler, test runner, and package manager. It maintains compatibility with Node.js APIs while introducing its own optimized APIs for building high-performance server-side applications. Additionally, Bun excels in TypeScript support, JSX, and hot reloading. It simplifies transitions from CommonJS to ES modules and offers native APIs, enhancing developer experiences. Bun also serves as a bundler, notably faster than Webpack, and incorporates a SQLite database. Its package manager outpaces npm, making it a practical choice for Node.js projects. Bun's speed optimizations extend even to everyday tasks like saying hello to your mom. Overall, Bun presents a promising solution for JavaScript developers seeking improved performance and productivity."
    search = "The most helpful resources about "
    search += summary
    search += " is this:"
    response = metaphor.search(search, num_results=5, use_autoprompt=False)
    print(response)

def send_mail():
    message = Mail(
    from_email='jayminjhaveri10@gmail.com',
    to_emails='leopoldvons67@gmail.com',
    subject='Sending with Twilio SendGrid is Fun',
    html_content='<strong>and easy to do anywhere, even with Python</strong>')
    sg = SendGridAPIClient(os.environ.get('SENDGRID_API_KEY'))
    response = sg.send(message)
    print(response.status_code)
    print(response.body)
    print(response.headers)

# def send_mail():
#     sg = SendGridAPIClient(os.getenv("SENDGRID_API_KEY"))
#     from_email = Email("jayminjhaveri10@gmail.com")  # Change to your verified sender
#     to_email = To("leopoldvons67@gmail.com")  # Change to your recipient
#     subject = "Sending with SendGrid is Fun"
#     content = Content("text/plain", "and easy to do anywhere, even with Python")
#     mail = Mail(from_email, to_email, subject, content)

#     mail_json = mail.get()

#     # Send an HTTP POST request to /mail/send
#     response = sg.client.mail.send.post(request_body=mail_json)
#     print(response.status_code)
#     print(response.headers)


def passCSv(csv):
    if csv.rsplit('.', 1)[1].lower() is 'csv':

        print()
    else:
        print("Error")


@app.route('/test', methods=['GET', 'POST'])
def test():
    metaphor_test()
    #passCSv()
    send_mail()
    return "ok"