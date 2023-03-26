
from flask import Flask, render_template, request
# from vdo import summarization
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
from transformers import pipeline, AutoTokenizer, AutoModelWithLMHead
model = AutoModelWithLMHead.from_pretrained("t5-base")
tokenizer = AutoTokenizer.from_pretrained("t5-base")

# nltk.download('punkt')
app = Flask(__name__)


@app.route('/')
def index():
    return render_template('index.html')


ALLOWED_EXTENSIONS = ['mp4']


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/summarization', methods=['POST'])
# def upload():
#     if 'video' not in request.files:
#         return 'No video file found'
#     video = request.files['video']
#     if video.filename == '':
#         return 'No video selected'
#     if video and allowed_file(video.filename):
#         video.save('static/videos/' + video.filename)
#         return render_template('preview.html', result=summary)
#     else: 'Invalid video file'
def summarization():
    if 'video' not in request.files:
        return 'No video file found'
    video = request.files['video']
    if video.filename == '':
        return 'No video selected'
    if video and allowed_file(video.filename):
        video.save('static/videos/' + video.filename)
    else: 'Invalid video file'

    csv_file = request.files['csv_file']
    fsv = csv_file.filename
    csv_file.save(fsv)

    clip = mp.VideoFileClip(r"static\\videos\\" + video.filename)
    video_duration = int(clip.duration)
    hours, mins, secs = convert(video_duration)

    # print("Hours:", hours)
    # print("Minutes:", mins)
    # print("Seconds:",secs)
    clip.audio.write_audiofile("audio1_file.mp3")

    # untext = !python transcribe.py audio1_file.mp3 --local

    audio_file = "audio1_file.mp3"
    command = ["python", "transcribe.py", audio_file, "--local"]
    result = subprocess.run(command, capture_output=True, text=True)
    # print(result.stdout)

    text = ''.join(map(str, result.stdout))
    # print(text)
    summary = summarize(text)
    # csv input
    # fsv = "meetingAttendanceList.csv"
    attendee_value = attendee(fsv)

    file_paths = ["static\\videos\\" + video.filename,
                  "audio1_file.mp3", fsv, "transcript.txt"]

    clip.close()

    action_item = find_action_item(text)

    return render_template('preview.html', result21=summary, h=hours, m=mins, ss=secs, c=attendee_value, d=action_item)
# , delete_files(file_paths)


def find_action_item(text):
    array_text = text.split('. ')
    actions =  ["backup","support","Project title","deadline","Schedule","decision","Prepare","Contact","develop budget","follow up","demand"]
    actions = [' '.join([word.lower() for word in sentence.split() if word.lower() ]) for sentence in actions]
    array_text = [' '.join([word.lower() for word in sentence.split() if word.lower() ]) for sentence in array_text]
    
    vectorizer = TfidfVectorizer()
    vectors = vectorizer.fit_transform(actions + array_text)
    similarity_scores = cosine_similarity(
        vectors[:len(actions)], vectors[len(actions):])

    results = []
    for i, sentence in enumerate(actions):
        # for j in similarity_scores > 0.0 :
        most_similar_indices = similarity_scores[i].argsort()[::-1][:5]

        for index in most_similar_indices:
            if similarity_scores[i][index] > 0.3:
              
                results.append(array_text[index])

    return results


def summarize(text):
    # parser = PlaintextParser.from_string(text, Tokenizer("english"))
    # summarizer = LexRankSummarizer()
    # summary = summarizer(parser.document, ratio *
    #                      len(parser.document.sentences))
    # return " ".join(map(str, summary))

    
# Define summarization pipeline
    summarizer = pipeline("summarization", model=model, tokenizer=tokenizer)
    summary_text = summarizer(text, max_length=200, min_length=50, do_sample=False)
    sum = (summary_text[0]['summary_text'])
    sentences = sum.split(".")

# Create an empty list to store the capitalized sentences
    capitalized_sentences = []

# Loop through each sentence in the list
    for sentence in sentences:
    # Strip any leading or trailing whitespace from the sentence
        sentence = sentence.strip()

        if sentence:
        # Capitalize the first letter of the sentence
            capitalized_sentence = sentence[0].upper() + sentence[1:]
        else:
            capitalized_sentence = sentence
   
    # Append the capitalized sentence to the list
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
        # Load the Excel file using xlrd
        # wb = xlrd.open_workbook(fsv)
        # sheet = wb.sheet_by_index(0)

        # # Count the number of non-empty cells in the specified column
        # count = sum([1 for cell in sheet.col(attendee_column) if cell.value])-1

        unique_attendees = set()  # a set to store unique attendees

        workbook = xlrd.open_workbook(fsv)  # open the XLS file
        worksheet = workbook.sheet_by_index(0)  # select the first worksheet

        for row_idx in range(1, worksheet.nrows):
            # assuming the attendee name is in the first column of the XLS file
            # remove leading/trailing whitespaces
            attendee = worksheet.cell_value(row_idx, 0).strip()
            if attendee:  # check if the attendee name is not an empty string
                # add the attendee name to the set of unique attendees
                unique_attendees.add(attendee)

        count = len(unique_attendees)

    elif fsv.endswith('.csv'):
        # Read the CSV file using the csv module
        # with open(fsv, "r") as file:
        #     csvReader = csv.reader(codecs.open(fsv, 'rU',))
        # count = -1
        # for row in csvReader:
        #     if row[attendee_column]:
        #         count += 1

        unique_attendees = set()  # a set to store unique attendees

        with open(fsv, 'r') as file:
            reader = csv.reader(file)
            for row in reader:
                # assuming the attendee name is in the first column of the CSV file
                # remove leading/trailing whitespaces
                attendee = row[0].strip()
                if attendee:  # check if the attendee name is not an empty string
                    # add the attendee name to the set of unique attendees
                    unique_attendees.add(attendee)

        count = len(unique_attendees)

# print(f'Number of unique attendees: {num_unique_attendees}')
# for name in unique_attendees:
#     print(name)

    else:
        raise ValueError("Unsupported file format")

    return count


# Contains the duration of the video in terms of seconds


# def delete_files(file_paths):
#     time.sleep(120)
#     for file_path in file_paths:
#         try:
#             # delete the file
#             os.remove(file_path)
#             print(f"{file_path} has been deleted")
#         except OSError as error:
#             print(error)


if __name__ == '__main__':
    app.run(debug=True)
