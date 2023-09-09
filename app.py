import os
from flask import Flask, flash, request, redirect, url_for
from werkzeug.utils import secure_filename

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


def transcribe(filename):
    fileInQuestion = open("./uploads/" + filename, "rb")
    transcript = openai.Audio.transcribe("whisper-1", fileInQuestion)

    # try catch delete filename

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
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            transcribe(filename)
            return "Done!"

    return "hello"
