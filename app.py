import os
import csv
import base64

from flask import Flask, flash, request, redirect, url_for
from werkzeug.utils import secure_filename

import json

from zipfile import ZipFile

## MP4 TO MP3 ##
from moviepy.editor import *

from dotenv import load_dotenv

## METAPHOR ##
from metaphor_python import Metaphor

## EMAIL SENDING ##
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import (
    Mail, Attachment, FileContent, FileName, FileType, Disposition)

import openai

UPLOAD_FOLDER = './uploads'
ALLOWED_EXTENSIONS = {'zip'}

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
    print("transcribing...")
    fileInQuestion = open("./uploads/" + filename, "rb")
    transcript = openai.Audio.transcribe("whisper-1", fileInQuestion)

    # try catch delete audiofile

    return (transcript["text"])


def save_transcript_file(content):

    transcription = open("./build/transcription.txt", "w+")
    transcription.write(content)

    return (content)


def run_transcription(audio_file):
    system_prompt = "You are a helpful personal assistant. Your task is to correct any spelling discrepancies in the transcribed text. Only add necessary punctuation such as periods, commas, and capitalization, and use only the context provided. format it in a way which would be easy to email, make it user friendly and save into a txt file"

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": transcribe(audio_file)}
    ]

    functions = [
        {
            "name": "save_transcript_file",
            "description": "save the transcription into a txt file",
            "parameters": {
                "type": "object",
                "properties": {
                    "content": {
                        "type": "string",
                        "description": "the content supposed to go into the .txt file",
                    },
                },
                "required": ["content"],
            },
        }
    ]

    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=messages,
        functions=functions,
        function_call="auto"
    )

    response_message = response["choices"][0]["message"]

    if response_message.get("function_call"):
        available_functions = {
            "save_transcript_file": save_transcript_file,
        }

        function_name = response_message["function_call"]["name"]
        fuction_to_call = available_functions[function_name]
        function_args = json.loads(
            response_message["function_call"]["arguments"], strict=False)

        function_response = fuction_to_call(
            content=function_args.get("content"),)

        # extend conversation with assistant's reply
        messages.append(response_message)
        messages.append(
            {
                "role": "function",
                "name": function_name,
                "content": function_response,
            }
        )  # extend conversation with function response
        second_response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=messages,
        )  # get a new response from GPT where it can see the function response

        return function_args.get("content")


def generate_summary(transcript):
    print("Generating Summary")

    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "user", "content": "You are a helpful assistant, your task is to write a summary with key points and the minutes of the meeting if it is a meeting based on the following transcript that is going to be emailed to the attendes and other stakeholders format it in html so that it can be emailed easily: {0}".format(
                transcript)},
        ]
    )

    return response["choices"][0]["message"]["content"]


def metaphor_ref(transcript):
    print("Generating Readings")

    metaphor = Metaphor(os.getenv("METAPHOR_API_KEY"))
    search = "The most helpful resources about "
    search += transcript
    search += " is this:"
    response = metaphor.search(search, num_results=5, use_autoprompt=False)

    return (response)


def passCSv(sheet):
    # opening the CSV file
    with open(sheet, mode='r') as file:

        # reading the CSV file
        csvFile = (csv.reader(file, delimiter=","))
        list_of_contacts = []

        fields = next(csvFile)
        for row in csvFile:
            row.pop(0)
            list_of_contacts.append(row[0])

        return (list_of_contacts)


def send_mail(summary, readings):

    print("Sending Emails")

    email_content = '<h1>Hey!</h1></br><p>Here is what happened today:</p></br>{0}</br><p>Here are some resources you can refer to </p></br>{1}'.format(
        summary, readings)

    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "user", "content": "You are a helpful assistant, your task is to format the following in html so that it can be emailed easily as a newsletter and is easy to read with bullet points, proper spacing, and formatting: {0}".format(
                email_content)},
        ]
    )

    message = Mail(
        from_email='jayminjhaveri10@gmail.com',
        to_emails=passCSv("./uploads/people.csv"),
        subject='Today\'s Meeting Summary',
        html_content=response["choices"][0]["message"]["content"])

    with open('./uploads/resources.zip', 'rb') as f:
        data = f.read()
        f.close()
        encoded_file = base64.b64encode(data).decode()

    attachedFile = Attachment(
        FileContent(encoded_file),
        FileName('resources.zip'),
        FileType('application/zip'),
        Disposition('attachment')
    )

    message.attachment = attachedFile

    sg = SendGridAPIClient(os.getenv('SENDGRID_API_KEY'))
    response = sg.send(message)

    print(response.status_code)


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
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], file.filename))

            with ZipFile("./uploads/dispatch.zip", 'r') as zObject:
                zObject.extractall(path="./uploads")

            os.remove("./uploads/dispatch.zip")

            converter(filename)

            transcript = run_transcription("audiofile.mp3")
            summary = generate_summary(transcript)
            readings = metaphor_ref(transcript)

            send_mail(summary, readings)

            return "Done!"

    return "hello"


@app.route('/test', methods=['GET', 'POST'])
def test():
    return "ok"
