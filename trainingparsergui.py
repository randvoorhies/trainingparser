import trainingparser
from Tkinter import Frame, Button, Tk, Text, Label, Entry, StringVar, N, S, E, W, END
import tkFileDialog
import ConfigParser


class Application(Frame):
    def __init__(self, master=None):
        Frame.__init__(self, master)
        self.pack()
        self.createWidgets()

    def createWidgets(self):
        self.openInputButton = Button(self, text='Open Input File', command=self.openInputFile)
        self.openInputButton.grid(row=0, column=0, sticky=W)
        self.inputLabelText = StringVar()
        self.inputLabelText.set('No Input File')
        self.inputLabel = Label(self, textvariable=self.inputLabelText)
        self.inputLabel.grid(row=0, column=1, sticky=W)

        self.openMaxButton = Button(self, text='Open Max File', command=self.openMaxFile)
        self.openMaxButton.grid(row=1, column=0, sticky=W)
        self.maxLabelText = StringVar()
        self.maxLabelText.set('No Max File')
        self.maxLabel = Label(self, textvariable=self.maxLabelText)
        self.maxLabel.grid(row=1, column=1, sticky=W)

        self.openTemplateButton = Button(self, text='Open Template File', command=self.openTemplateFile)
        self.openTemplateButton.grid(row=2, column=0, sticky=W)
        self.templateLabelText = StringVar()
        self.templateLabelText.set('No Template File')
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
        self.root.destroy()

    def generate(self):
        try:
            self.statusText.insert(END, 'Parsing max file...')
            maxes = trainingparser.parseMaxes(self.maxFile)
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
            program = trainingparser.parseTraining(self.inputFile, maxes)
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
            outfile = tkFileDialog.asksaveasfile(message='Output HTML')
            trainingparser.writeJinja(program=program, out=outfile, template=self.templateFile)
            self.statusText.insert(END, 'Success!\n')
        except Exception as e:
            self.statusText.insert(END, 'Failed!\n')
            self.statusText.insert(
                END, 'Unknown Error! Please send Rand your input, template and max files, and the following message:\n')
            self.statusText.insert(END, str(e) + '\n')
            return

    def openInputFile(self):
        Tk().withdraw()
        self.inputFile = tkFileDialog.askopenfile()
        self.inputLabelText.set(self.inputFile.name)
        self.statusText.insert(END, 'Opened input file: {}\n'.format(self.inputFile.name))

    def openTemplateFile(self):
        Tk().withdraw()
        self.templateFile = tkFileDialog.askopenfile()
        self.templateLabelText.set(self.templateFile.name)
        self.statusText.insert(END, 'Opened template file: {}\n'.format(self.templateFile.name))

    def openMaxFile(self):
        Tk().withdraw()
        self.maxFile = tkFileDialog.askopenfile()
        self.maxLabelText.set(self.maxFile.name)
        self.statusText.insert(END, 'Opened max file: {}\n'.format(self.maxFile.name))


root = Tk()
app = Application(master=root)
root.protocol("WM_DELETE_WINDOW", app.destroy)
app.mainloop()
root.destroy()
