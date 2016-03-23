from flask import Flask, render_template, request, redirect, url_for, session, flash, Response, make_response
from flask.ext.session import Session
import os
import trainingparser
import StringIO
import zipfile
import io
import traceback

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
    try:
        formatFileIO = StringIO.StringIO(session['formatFile'])
        outputFileIO = StringIO.StringIO()

        maxes = dict((k.replace('max', ''), float(v)) for k,v in request.form.iteritems() if k.startswith('max'))

        program = session['program']
        trainee = request.form['trainee']

        print 'Got Maxes:::::', maxes
        trainingparser.writeJinja(program=program, template=formatFileIO, maxes=maxes, trainee=trainee, out=outputFileIO)
        return Response(outputFileIO.getvalue(),
                        headers={'Content-Disposition': 'attachment; filename={filename}.html'.format(filename=trainee.replace(' ', '_'))})
    except:
        flash('Unexpected Error! Send this to Rand: {}'.format(traceback.format_exc()), 'danger')
        return redirect(url_for('index'))

@app.route('/examplefiles')
def examplefiles():
    return render_template('examplefiles.html')

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
                trainingparser.writeJinja(program=session['program'], template=formatFileIO, maxes=maxes, out=outputFileIO, trainee=name)
                outputZip.writestr(name.replace(' ', '_') + '.html', str(outputFileIO.getvalue()))

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
    return render_template('index.html')


if __name__ == '__main__':
    app.debug = True
    SESSION_TYPE = 'filesystem'
    app.config.from_object(__name__)
    app.secret_key = '1234567' # os.urandom(24) 
    Session(app)
    app.run()
