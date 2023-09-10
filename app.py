import os
from flask import Flask, flash, request, redirect, url_for
from werkzeug.utils import secure_filename

import json

from moviepy.editor import *

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
    print("transcribing...")
    fileInQuestion = open("./uploads/" + filename, "rb")
    transcript = openai.Audio.transcribe("whisper-1", fileInQuestion)

    # try catch delete audiofile

    return (transcript["text"])


def save_transcript_file(content):

    print("running")

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
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "user", "content": "You are a helpful assistant, your task is to write a summary with key points and the minutes of the meeting if it is a meeting based on the following transcript: {0}".format(
                transcript)},
        ]
    )

    return response["choices"][0]["message"]["content"]


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

            transcript = run_transcription("audiofile.mp3")
            print(transcript)

            print(generate_summary(transcript))

            return "Done!"

    return "hello"
