import sys
import re
import copy


def parseMaxes(maxesFile):
    maxes = {}
    for lineNumber, line in enumerate(maxesFile):
        line = line.strip()
        if len(line) == 0 or line[0] == '#':
            continue

        if line.count('|') != 1:
            raise RuntimeError('Error finding "|" character on line {} : "{}"'.format(lineNumber, line))

        name, rest = [x.strip() for x in line.split('|')]
        try:
            maxes[name] = dict((kv.split(':')[0].strip(), float(kv.split(':')[1])) for kv in rest.split(','))
        except:
            raise RuntimeError('Error parsing line {} : "{}"'.format(lineNumber, line))
        
    return maxes


class Program:
    def __init__(self, name, weeks=None):
        self.name = name
        self.weeks = [] if weeks is None else weeks
        self.baseLifts = set()


class Week:
    def __init__(self, name, days=None):
        self.name = name
        self.days = [] if days is None else days
        self.maxSets = 0


class Day:
    def __init__(self, name, lifts=None):
        self.name = name
        self.lifts = [] if lifts is None else lifts


class Lift:
    def __init__(self, name, baseLift=None, sets=None):
        self.name = name
        self.baseLift = baseLift
        self.sets = [] if sets is None else sets


class Set:
    def __init__(self, reps, percent):
        self.reps = reps
        self.percent = percent


class SetsComment:
    def __init__(self, comment):
        self.comment = comment


def parseTraining(inFile):

    program = Program("Waxman's Training Program")

    currentWeek = None
    currentDay = None

    daysOfTheWeek = ('monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday')

    for lineNumber, line in enumerate(inFile):
        try:
            # Strip out any leading and trailing whitespace
            line = line.strip()

            if line.count(':') > 1:
                raise RuntimeError('More than one ":" character detected on line {}: "{}"'.format(
                    lineNumber + 1, line))

            # If the line starts with "Week", then let's start a new week
            if line.lower().startswith('week'):
                # If we were already parsing a week, push it onto the list of weeks
                if currentWeek is not None:
                    currentWeek.days.append(copy.copy(currentDay))
                    currentDay = None
                    program.weeks.append(currentWeek)
                currentWeek = Week(name=line)

            # If the line starts with the name of a day, then let's start a new day
            elif line.lower().startswith(daysOfTheWeek):
                # If we were already parsing a day, push it onto the current week's list of days
                if currentDay is not None:
                    currentWeek.days.append(copy.copy(currentDay))
                currentDay = Day(name=line)

            # Otherwise, interpret this as a lift and add it to the current day
            elif len(line) > 0:
                if ':' in line:
                    liftName = line.split(':')[0].split('{')[0].strip()

                    # Check to see if there is something in curly braces in the lift name
                    # to interpret as a base lift on which we should base our percentages
                    if '{' in line.split(':')[0]:
                        baseLift = re.search('\{(.*)\}', line).group(1).lower()
                    else:
                        baseLift = None

                    # Split the sets and reps string
                    setsAndRepsString = line.split(':')[1].strip()

                    sets = None

                    # If the sets and reps section starts with a hard bracket "[", then it is
                    # a special comment (e.g. [singles to max])
                    if setsAndRepsString.startswith('['):
                        sets = SetsComment(setsAndRepsString.replace('[', '').replace(']', ''))
                    else:
                        # Split the sets and reps either by comma or by space
                        setStrings = [r for r in re.split('[ ,]', setsAndRepsString) if len(r) > 0]
                        sets = []
                        for setString in setStrings:
                            percent, numReps, numSets = None, None, 1
                            if '(' in setString:
                                # Try to match (weight/sets)/reps lines
                                match = re.match(r'\((\d*X*%?)\/(\d*\+?\d*)\)\/?(\d*)', setString)
                                if match:
                                    percent = match.group(1)
                                    numReps = match.group(2)
                                    numSets = match.group(3)
                                else:
                                    raise RuntimeError('unrecognized sets/reps scheme on line {}: "{}"'.format(
                                        lineNumber + 1, line))
                            else:
                                # Try to match weight/reps lines
                                match = re.match(r'(\d*)%?\/(\d*\+?\d*)', setString)
                                if match:
                                    percent = match.group(1)
                                    numReps = match.group(2)
                                    numSets = 1
                                else:
                                    raise RuntimeError('Unrecognized sets/reps scheme on line {}: "{}"'.format(
                                        lineNumber + 1, line))

                            if percent is None or numReps is None:
                                raise RuntimeError('Error parsing line {}: "{}"'.format(
                                    lineNumber + 1, line))

                            # Now that we have the percent, sets, and reps let's clean them up a bit
                            try:
                                percent = float(percent.replace('%', ''))
                            except:
                                pass
                            numReps = numReps
                            numSets = int(numSets)

                            # Now let's unroll the sets and reps
                            for setNumber in range(0, numSets):
                                sets.append(Set(percent=percent, reps=numReps))
                        currentWeek.maxSets = max(currentWeek.maxSets, len(sets))

                    currentDay.lifts.append(Lift(name=liftName, baseLift=baseLift, sets=sets))
                    if baseLift is not None:
                        program.baseLifts.add(baseLift)

                elif line.lower() == 'off':
                    currentDay.lifts = None
                else:
                    raise RuntimeError('Error parsing line {} (No ":" found): "{}"'.format(
                        lineNumber + 1, line))
        except:
            raise

    program.weeks.append(currentWeek)
    return program


def writeJinja(program, template, maxes, out):
    import jinja2
    env = jinja2.Environment()

    is_list = lambda l: isinstance(l, list)
    format_weight = lambda w: round(w * 2.0) / 2
    env.filters.update({'is_list': is_list, 'format_weight': format_weight})
    template = env.from_string(''.join(template.readlines()))
    out.write(template.render(program=program, maxes=maxes))


# if __name__ == '__main__':
#     import argparse
#     parser = argparse.ArgumentParser(description='Training Log Parser and Formatter')
#     parser.add_argument('input', type=str, help='The input text file')
#     parser.add_argument('--output', type=str, default='output.html', help='The output HTML file')
#     parser.add_argument('--maxes', type=str, default='maxes.txt', help='The output HTML file')
#     parser.add_argument('--template', type=str, default='template.html', help='The input HTML template')
#     args = parser.parse_args()
# 
#     with open(args.maxes) as maxFile:
#         maxes = parseMaxes(maxFile)
# 
#     with open(args.input) as inputFile:
#         program = parseTraining(inputFile)
# 
#     with open(args.output, 'w') as outputFile:
#         with open(args.template) as template:
#             writeJinja(program=program, template=template, maxes=maxes, out=outputFile)
