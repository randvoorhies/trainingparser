from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask.ext.session import Session
import os
import trainingparser
import StringIO

app = Flask(__name__)

ALLOWED_EXTENSIONS = set(['txt', 'html', 'input', 'training', 'program', 'max', 'maxes'])

@app.route('/fonts/<fontname>')
def fonts(fontname):
    return redirect(url_for('static', filename='fonts/'+fontname))

@app.route('/help')
def help():
    return render_template('help.html')

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

            print '>>>>>', programFile.filename, maxFile.filename, formatFile.filename

            if programFile.filename != '':
                session['programFile'] = programFile.read()
                session['programFileName'] = programFile.filename

                try:
                    program = trainingparser.parseTraining(StringIO.StringIO(session['programFile']))
                    flash('Uploaded and parsed program file: {}'.format(programFile.filename), 'info')
                except RuntimeError as e:
                    flash('Error parsing program file. Please contact Rand! ' + str(e), 'danger')
                    del session['programFile']
                    del session['programFileName']

            if maxFile.filename != '':
                flash('Uploaded max file: {}'.format(maxFile.filename), 'info')
                session['maxFile'] = maxFile.read()
                session['maxFileName'] = maxFile.filename
            if formatFile.filename != '':
                flash('Uploaded format file: {}'.format(formatFile.filename), 'info')
                session['formatFile'] = formatFile.read()
                session['formatFileName'] = formatFile.filename

        elif 'process' in request.form:
            if 'programFile' not in session or 'maxFile' not in session or 'formatFile' not in session:
                print 'Shit!'
                print session.keys()
            else:
                programFileIO = StringIO.StringIO(session['programFile'])
                maxFileIO = StringIO.StringIO(session['maxFile'])
                formatFileIO = StringIO.StringIO(session['formatFile'])

                maxes = trainingparser.parseMaxes(maxFileIO)
                program = trainingparser.parseTraining(programFileIO)

                outputFileIO = StringIO.StringIO()
                trainingparser.writeJinja(program=program, template=formatFileIO, maxes=maxes, out=outputFileIO)

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
