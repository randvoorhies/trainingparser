from flask import Flask, render_template, request, redirect, url_for, session
from flask.ext.session import Session
import os
import trainingparser
import StringIO

app = Flask(__name__)

ALLOWED_EXTENSIONS = set(['txt', 'html', 'input', 'training', 'program', 'max', 'maxes'])

@app.route('/uploaded_file')
def uploaded_file():
    return render_template('uploaded_file.html')

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        if 'upload' in request.form:
            programFile = request.files['programFile']
            maxFile = request.files['maxFile']
            formatFile = request.files['formatFile']

            if programFile.filename != '':
                session['programFile'] = programFile.read()
                session['programFileName'] = programFile.filename
            if maxFile.filename != '':
                session['maxFile'] = maxFile.read()
                session['maxFileName'] = maxFile.filename
            if formatFile.filename != '':
                session['formatFile'] = formatFile.read()
                session['formatFileName'] = formatFile.filename

            print 'Session is up!!!!', session.keys()
        elif 'process' in request.form:
            print '>>>>>>>>>>>>>>>', session.keys()
            if 'programFile' not in session or 'maxFile' not in session or 'formatFile' not in session:
                print 'Shit!'
                print session.keys()
            else:
                programFileIO = StringIO.StringIO(session['programFile'])
                maxFileIO = StringIO.StringIO(session['maxFile'])
                formatFileIO = StringIO.StringIO(session['formatFile'])

                maxes = trainingparser.parseMaxes(maxFileIO)
                program = trainingparser.parseTraining(programFileIO, maxes)

                outputFileIO = StringIO.StringIO()
                trainingparser.writeJinja(program=program, template=formatFileIO, out=outputFileIO)

                print 'Processing...'
                return render_template('processed_file.html', program=outputFileIO.getvalue())

    return render_template('index.html')


if __name__ == '__main__':
    app.debug = True
    SESSION_TYPE = 'filesystem'
    app.config.from_object(__name__)
    app.secret_key = '123456' # os.urandom(24) 
    Session(app)
    app.run()
