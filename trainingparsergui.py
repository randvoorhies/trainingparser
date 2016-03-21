import trainingparser
from Tkinter import Frame, Button, Tk, Text, Label, Entry, StringVar, N, S, E, W, END, Menu
import tkFileDialog
import os
import json


class Application(Frame):
    def __init__(self, master=None):
        Frame.__init__(self, master)
        self.master = master

        # self.master.protocol("WM_DELETE_WINDOW", self.onWindowClose)

        # Load defaults from the config file
        self.configFilename = os.path.expanduser('~/.trainingparser')
        self.config = self.readConfig(self.configFilename)
        self.templateFileName = self.config['TemplateFile']
        self.programFileName = self.config['ProgramFile']
        self.maxFileName = self.config['MaxFile']

        self.pack()
        self.createWidgets()

    # def onWindowClose(self):
    #     if self.master:
    #         print 'DESTROYING'
    #         self.master.destroy()

    def readConfig(self, filename):
        config = {}
        if os.path.exists(filename):
            with open(filename) as f:
                return json.load(f)
        else:
            return {
                'TemplateFile': None,
                'ProgramFile': None,
                'MaxFile': None,
                'OutputDirectory': os.path.expanduser('~'),
            }

    def writeConfig(self, config, filename):
        with open(filename, 'w') as f:
            json.dump(config, f, indent=2)

    def createWidgets(self):

        self.menuBar = Menu(self.master)
        self.fileMenu = Menu(self.menuBar, tearoff=0)
        self.fileMenu.add_command(label="Exit", command=self.master.destroy)
        self.menuBar.add_cascade(label="File", menu=self.fileMenu)
        self.master.config(menu=self.menuBar)

        self.openProgramButton = Button(self, text='Open Program File', command=self.openProgramFile)
        self.openProgramButton.grid(row=0, column=0, sticky=W)
        self.programLabelText = StringVar()
        self.programLabelText.set('No Program File' if self.programFileName is None else self.programFileName)
        self.programLabel = Label(self, textvariable=self.programLabelText)
        self.programLabel.grid(row=0, column=1, sticky=W)

        self.openMaxButton = Button(self, text='Open Max File', command=self.openMaxFile)
        self.openMaxButton.grid(row=1, column=0, sticky=W)
        self.maxLabelText = StringVar()
        self.maxLabelText.set('No Max File' if self.maxFileName is None else self.maxFileName)
        self.maxLabel = Label(self, textvariable=self.maxLabelText)
        self.maxLabel.grid(row=1, column=1, sticky=W)

        self.openTemplateButton = Button(self, text='Open Template File', command=self.openTemplateFile)
        self.openTemplateButton.grid(row=2, column=0, sticky=W)
        self.templateLabelText = StringVar()
        self.templateLabelText.set('No Template File' if self.templateFileName is None else self.templateFileName)
        self.templateLabel = Label(self, textvariable=self.templateLabelText)
        self.templateLabel.grid(row=2, column=1, sticky=W)

        self.programNameLabel = Label(self, text='Program Name')
        self.programNameLabel.grid(row=3, column=0, sticky=W)
        self.programNameField = Entry(self, width=60)
        self.programNameField.insert(END, "Waxman's Gym Programming")
        self.programNameField.grid(row=3, column=1, sticky=W)

        self.openMaxButton = Button(self, text='Generate!', command=self.generate)
        self.openMaxButton.grid(row=4, column=0, columnspan=2)

        self.statusText = Text(self)
        self.statusText.grid(row=5, column=0, columnspan=2)

    def quit(self):
        self.master.destroy()

    def generate(self):
        try:
            self.statusText.insert(END, 'Parsing max file...')
            with open(self.maxFileName) as maxFile:
                maxes = trainingparser.parseMaxes(maxFile)
            self.statusText.insert(END, 'Success!\n')
        except RuntimeError as e:
            self.statusText.insert(END, 'Failed!\n')
            self.statusText.insert(END, e.message)
            return
        except Exception as e:
            self.statusText.insert(END, 'Failed!\n')
            self.statusText.insert(END, 'Unknown Error! Please send Rand your input and max files, and the following message:\n')
            self.statusText.insert(END, str(e) + '\n')
            return

        try:
            self.statusText.insert(END, 'Parsing input file...')
            with open(self.programFileName) as programFile:
                program = trainingparser.parseTraining(programFile, maxes)
            self.statusText.insert(END, 'Success!\n')
        except RuntimeError as e:
            self.statusText.insert(END, 'Failed!\n')
            self.statusText.insert(END, e.message)
            return
        except Exception as e:
            self.statusText.insert(END, 'Failed!\n')
            self.statusText.insert(END, 'Unknown Error! Please send Rand your input and max files, and the following message:\n')
            self.statusText.insert(END, str(e) + '\n')
            return

        try:
            self.statusText.insert(END, 'Generating output HTML file...')
            outFileName = tkFileDialog.asksaveasfilename(message='Output HTML')
            with open(outFileName, 'w') as outfile:
                trainingparser.writeJinja(program=program, out=outfile, template=self.templateFile)
            self.statusText.insert(END, 'Success!\n')
        except Exception as e:
            self.statusText.insert(END, 'Failed!\n')
            self.statusText.insert(
                END, 'Unknown Error! Please send Rand your input, template and max files, and the following message:\n')
            self.statusText.insert(END, str(e) + '\n')
            return

    def openProgramFile(self):
        Tk().withdraw()
        self.programFileName = tkFileDialog.askopenfilename(parent=self)
        self.config['ProgramFile'] = self.programFileName
        self.writeConfig(self.config, self.configFilename)
        self.programLabelText.set(self.programFileName)
        self.statusText.insert(END, 'Opened input file: {}\n'.format(self.programFileName))

    def openTemplateFile(self):
        Tk().withdraw()
        self.templateFileName = tkFileDialog.askopenfilename(parent=self)
        self.config['TemplateFile'] = self.templateFileName
        self.writeConfig(self.config, self.configFilename)
        self.templateLabelText.set(self.templateFileName)
        self.statusText.insert(END, 'Opened template file: {}\n'.format(self.templateFileName))

    def openMaxFile(self):
        Tk().withdraw()
        self.maxFileName = tkFileDialog.askopenfilename(parent=self)
        self.config['MaxFile'] = self.maxFileName
        self.writeConfig(self.config, self.configFilename)
        self.maxLabelText.set(self.maxFileName)
        self.statusText.insert(END, 'Opened max file: {}\n'.format(self.maxFileName))

root = Tk()
app = Application(master=root)
root.protocol("WM_DELETE_WINDOW", root.destroy)
app.mainloop()
