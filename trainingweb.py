from flask import Flask, render_template, request, redirect, url_for, session, flash, Response, make_response
from flask.ext.session import Session
import os
import trainingparser
import StringIO
import zipfile
import io

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

@app.route('/generatesingle', methods=['POST'])
def generatesingle():
    formatFileIO = StringIO.StringIO(session['formatFile'])
    outputFileIO = StringIO.StringIO()
    trainingparser.writeJinja(program=session['program'], template=formatFileIO, maxes=request.form, out=outputFileIO)
    response = make_response(outputFileIO.getvalue())
    response.headers["Content-Disposition"] = "attachment; filename=output.html"
    return response

@app.route('/generatebulk', methods=['POST'])
def generatebulk():

    zipIO = io.BytesIO()
    with zipfile.ZipFile(zipIO, 'w') as outputZip:
        try:
            maxesFile = request.files['maxesFile']
            maxesDB = trainingparser.parseMaxes(maxesFile)

            if len(maxesDB) == 0:
                raise RuntimeError('No entries found in maxes file.')

            for name, maxes in maxesDB.iteritems():
                formatFileIO = StringIO.StringIO(session['formatFile'])
                outputFileIO = StringIO.StringIO()
                trainingparser.writeJinja(program=session['program'], template=formatFileIO, maxes=maxes, out=outputFileIO)
                outputZip.writestr(name + '.html', str(outputFileIO.getvalue()))

        except RuntimeError as e:
            flash('Error parsing maxes file. Please contact Rand! ' + str(e), 'danger')

    zipIO.seek(0)
    return Response(zipIO,
                    mimetype='application/zip',
                    headers={'Content-Disposition':'attachment;filename=output.zip'})

@app.route('/uploadprogram', methods=['POST'])
def uploadprogram():
    programFile = request.files['programFile']
    session['programFile'] = programFile.read()
    session['programFileName'] = programFile.filename

    try:
        program = trainingparser.parseTraining(StringIO.StringIO(session['programFile']))
        session['program'] = program
        flash('Uploaded and parsed program file: {}'.format(programFile.filename), 'info')
    except RuntimeError as e:
        flash('Error parsing program file. Please contact Rand! ' + str(e), 'danger')
        del session['programFile']
        del session['programFileName']
    except:
        flash('Unknown error while parsing program file. Please contact Rand!', 'danger')
        del session['programFile']
        del session['programFileName']

    return redirect(url_for('index'))

@app.route('/uploadformat', methods=['POST'])
def uploadformat():
    formatFile = request.files['formatFile']
    flash('Uploaded format file: {}'.format(formatFile.filename), 'info')
    session['formatFile'] = formatFile.read()
    session['formatFileName'] = formatFile.filename
    return redirect(url_for('index'))

@app.route('/')
def index():
    # elif 'process' in request.form:
    #     if 'programFile' not in session or 'maxFile' not in session or 'formatFile' not in session:
    #         print 'Shit!'
    #         print session.keys()
    #     else:
    #         programFileIO = StringIO.StringIO(session['programFile'])
    #         maxFileIO = StringIO.StringIO(session['maxFile'])
    #         formatFileIO = StringIO.StringIO(session['formatFile'])

    #         maxes = trainingparser.parseMaxes(maxFileIO)
    #         program = trainingparser.parseTraining(programFileIO)

    #         outputFileIO = StringIO.StringIO()
    #         trainingparser.writeJinja(program=program, template=formatFileIO, maxes=maxes, out=outputFileIO)

    #         print 'Processing...'
    #         return render_template('processed_file.html', program=outputFileIO.getvalue())
    return render_template('index.html')


if __name__ == '__main__':
    app.debug = True
    SESSION_TYPE = 'filesystem'
    app.config.from_object(__name__)
    app.secret_key = '1234567' # os.urandom(24) 
    Session(app)
    app.run()
