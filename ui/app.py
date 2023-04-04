from flask import Flask, render_template, request, jsonify
import subprocess
import os
import csv
import moviepy.editor as mp
import nltk
import nltk.downloader
from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.lex_rank import LexRankSummarizer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import xlrd
import time
import codecs
import re
from datetime import datetime
from transformers import pipeline, AutoTokenizer, AutoModelWithLMHead
model = AutoModelWithLMHead.from_pretrained("t5-base")
tokenizer = AutoTokenizer.from_pretrained("t5-base")

app = Flask(__name__)


@app.route('/')
def index():
    return render_template('index.html')


ALLOWED_EXTENSIONS = ['mp4', 'vtt']


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/summarization', methods=['POST'])
def summarization():
    if 'video' not in request.files:
        return 'No video file found'
    video = request.files['video']
    if video.filename == '':
        return 'No video selected'
    if video and allowed_file(video.filename):
        video.save(video.filename)
    else:
        'Invalid video file'

    abc = video.filename

    if abc.endswith('.vtt'):
        text, video_duration = vtt_text(abc)
        hours, mins, secs = convert(video_duration)
        hours = int(hours)
        mins = int(mins)
        secs = int(secs)

    elif abc.endswith('.mp4'):
        clip = mp.VideoFileClip(video.filename)
        video_duration = int(clip.duration)

        hours, mins, secs = convert(video_duration)

        clip.audio.write_audiofile("audio1_file.mp3")

        audio_file = "audio1_file.mp3"
        command = ["python", "transcribe.py", audio_file, "--local"]
        result = subprocess.run(command, capture_output=True, text=True)

        text = ''.join(map(str, result.stdout))
        clip.close()
    else:
        print("ERROR")

    csv_file = request.files['csv_file']
    fsv = csv_file.filename
    csv_file.save(fsv)

    summary = summarize(text)

    attendee_value = attendee(fsv)

    file_paths = ["static\\videos\\" + video.filename,
                  "audio1_file.mp3", fsv, "transcript.txt"]

    action_item = find_action_item(text)

    return render_template('preview.html', result21=summary, h=hours, m=mins, ss=secs, c=attendee_value, d=action_item)


def find_action_item(text):
    array_text = text.split('. ')
    actions = ["backup", "support", "Project title", "deadline", "Schedule",
               "decision", "Prepare", "Contact", "develop budget", "follow up", "demand"]
    actions = [' '.join([word.lower() for word in sentence.split()
                        if word.lower()]) for sentence in actions]
    array_text = [' '.join([word.lower() for word in sentence.split(
    ) if word.lower()]) for sentence in array_text]

    vectorizer = TfidfVectorizer()
    vectors = vectorizer.fit_transform(actions + array_text)
    similarity_scores = cosine_similarity(
        vectors[:len(actions)], vectors[len(actions):])

    results = []
    for i, sentence in enumerate(actions):

        most_similar_indices = similarity_scores[i].argsort()[::-1][:5]

        for index in most_similar_indices:
            if similarity_scores[i][index] > 0.3:

                results.append(array_text[index])

    return results


def summarize(text):

    summarizer = pipeline("summarization", model=model, tokenizer=tokenizer)

    sentences1 = nltk.sent_tokenize(text)

    max_length = 512

    chunks = []
    current_chunk = ""
    for sentence in sentences1:

        if len(current_chunk) + len(sentence) < max_length:
            current_chunk += sentence
        else:

            chunks.append(current_chunk.strip())
            current_chunk = sentence

    if current_chunk:
        chunks.append(current_chunk.strip())

    summary_chunks = [summarizer(chunk, max_length=100, min_length=20, do_sample=False)[
        0]['summary_text'] for chunk in chunks]

    summary_text = " ".join(summary_chunks)

    sentences = summary_text.split(".")

    capitalized_sentences = []

    for sentence in sentences:

        sentence = sentence.strip()

        if sentence:

            capitalized_sentence = sentence[0].upper() + sentence[1:]
        else:
            capitalized_sentence = sentence

        capitalized_sentences.append(capitalized_sentence)

    capitalized_text = ". ".join(capitalized_sentences)

    return capitalized_text


def convert(seconds):
    hours = seconds // 3600
    seconds %= 3600
    mins = seconds // 60
    seconds %= 60
    return hours, mins, seconds


def attendee(fsv):
    attendee_column = 0

    if fsv.endswith('.xls'):

        unique_attendees = set()

        workbook = xlrd.open_workbook(fsv)
        worksheet = workbook.sheet_by_index(0)

        for row_idx in range(1, worksheet.nrows):

            attendee = worksheet.cell_value(row_idx, 0).strip()
            if attendee:
                unique_attendees.add(attendee)

        count = len(unique_attendees)

    elif fsv.endswith('.csv'):

        unique_attendees = set()

        with open(fsv, 'r') as file:
            reader = csv.reader(file)
            for row in reader:

                attendee = row[0].strip()
                if attendee:

                    unique_attendees.add(attendee)

        count = len(unique_attendees)-1

    else:
        raise ValueError("Unsupported file format")

    return count


def vtt_text(abc):
    with open(abc, 'r') as vtt_file:
        text = vtt_file.read()

    timestamps = re.findall(r'\d{2}:\d{2}:\d{2}\.\d{3}', text)
    last_timestamp = timestamps[-1]
    text = re.sub(
        r'(\d{2}:){2}\d{2}\.\d{3}\s-->\s(\d{2}:){2}\d{2}\.\d{3}\n|<c.[^>]+>|(\b[A-Z]+\b:\s)?', '', text)
    text = re.sub(r'(\b\w{8}-\w{4}-\w{4}-\w{4}-\w{12}-\d+\b)', '', text)
    lines = text.split("\n")
    non_empty_lines = [line for line in lines if line.strip() != ""]
    cleantext = "\n".join(non_empty_lines)

    last_timestamp_datetime = datetime.strptime(last_timestamp, '%H:%M:%S.%f')
    seconds = (last_timestamp_datetime - datetime(1900, 1, 1)).total_seconds()
    return cleantext, seconds


if __name__ == '__main__':

    app.run(debug=True)