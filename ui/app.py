
from flask import Flask, render_template, request
# from vdo import summarization
import subprocess
import csv
import moviepy.editor as mp
import nltk
import nltk.downloader
from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.lex_rank import LexRankSummarizer
import xlrd
import codecs
nltk.download('punkt')
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

    return render_template('preview.html', result21=summary, h=hours, m=mins, ss=secs, c=attendee_value)


def summarize(text, ratio=0.2):
    parser = PlaintextParser.from_string(text, Tokenizer("english"))
    summarizer = LexRankSummarizer()
    summary = summarizer(parser.document, ratio *
                         len(parser.document.sentences))
    return " ".join(map(str, summary))


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
        wb = xlrd.open_workbook(fsv)
        sheet = wb.sheet_by_index(0)

        # Count the number of non-empty cells in the specified column
        count = sum([1 for cell in sheet.col(attendee_column) if cell.value])-1

    elif fsv.endswith('.csv'):
        # Read the CSV file using the csv module
        # with open(fsv, "r") as file:
        #     csvReader = csv.reader(codecs.open(fsv, 'rUb', 'utf-16'))
        # count = -1
        # for row in csvReader:
        #     if row[attendee_column]:
        #         count += 1

        unique_attendees = set()  # a set to store unique attendees

        with open(fsv, 'r') as file:
            reader = csv.reader(file)
            for row in reader:
        # assuming the attendee name is in the first column of the CSV file
                attendee = row[0].strip()  # remove leading/trailing whitespaces
                if attendee:  # check if the attendee name is not an empty string
                    unique_attendees.add(attendee)  # add the attendee name to the set of unique attendees

        count = len(unique_attendees)

    else:
        raise ValueError("Unsupported file format")
    return count

# Contains the duration of the video in terms of seconds


if __name__ == '__main__':
    app.run(debug=True)
