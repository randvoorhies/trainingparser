from __future__ import print_function
import sys
from flask import Flask, render_template, request, redirect, url_for, session, flash, Response, make_response
from flask.ext.session import Session
import os
import trainingparser
import StringIO
import zipfile
import io
import traceback
import pdfkit

app = Flask(__name__)
app.secret_key = "\x97J\xab\xdf\xa7 \x86;'5\x81\xff\x17\x91*\x8d\xd4o\xaeY\x93\xd9Z\xe0"  # os.urandom(24) 

SESSION_TYPE = 'filesystem'
app.config.from_object(__name__)
Session(app)

ALLOWED_EXTENSIONS = set(['txt', 'html', 'input', 'training', 'program', 'max', 'maxes'])

def log(*objs):
    print(*objs, file=sys.stderr)

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
    log('Generating single training program')
    try:
        formatFileIO = StringIO.StringIO(session['formatFile'])

        htmlFileIO = StringIO.StringIO()

        maxes = dict((k.replace('max', ''), float(v)) for k,v in request.form.iteritems() if k.startswith('max'))

        program = session['program']
        trainee = request.form['trainee']

        trainingparser.writeJinja(program=program, template=formatFileIO, maxes=maxes, trainee=trainee, out=htmlFileIO)

        if 'generatePDF' in request.form:
            pdfFile = pdfkit.from_string(htmlFileIO.getvalue(), False)
            return Response(pdfFile,
                            headers={'Content-Disposition': 'attachment; filename={filename}.pdf'.format(filename=trainee.replace(' ', '_'))})
        else:
            return Response(htmlFileIO.getvalue(),
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
    log('Uploading Program')
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
    log('Uploaded format file. Redirecting to / : {}'.format(url_for('index')))
    return redirect('/')

@app.route('/')
def index():
    return render_template('index.html')


if __name__ == '__main__':
    app.debug = True
    SESSION_TYPE = 'filesystem'
    app.config.from_object(__name__)
    Session(app)
    app.run()
