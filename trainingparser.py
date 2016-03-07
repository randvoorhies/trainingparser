import sys
import re
import copy


def parseMaxes(maxesFile):
    maxes = {}
    for lineNumber, line in enumerate(maxesFile):
        line = line.strip()
        if len(line) == 0:
            continue

        match = re.search(r'(.*): +([0-9]*\.?[0-9]*)', line)
        if not match:
            raise RuntimeError('Error parsing line {} : "{}"'.format(lineNumber, line))

        liftName = match.group(1).strip().lower()
        weight = match.group(2)

        if liftName in maxes:
            raise RuntimeError('Duplicate max found on line {} : {}'.format(lineNumber, liftName))

        try:
            weight = float(weight)
        except ValueError:
            raise RuntimeError('Error interpreting weight as a number on line {} : "{}"'.format(lineNumber, line))

        maxes[liftName] = float(weight)

    return maxes

class Week:
    def __init__(self, name, days=None):
        self.name = name
        self.days = [] if days is None else days

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
    def __init__(self, reps, weight):
        self.reps = reps
        self.weight = weight

class SetsComment:
    def __init__(self, comment):
        self.comment = comment


def parseTraining(inFile, maxes={}):

    weeks = []

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
                    weeks.append(currentWeek)
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

                            if baseLift in maxes:
                                weight = percent / 100.0 * maxes[baseLift]
                            else:
                                weight = percent

                            # Now let's unroll the sets and reps
                            for setNumber in range(0, numSets):
                                sets.append(Set(weight=weight, reps=numReps))

                    currentDay.lifts.append(Lift(name=liftName, baseLift=baseLift, sets=sets))

                elif line.lower() == 'off':
                    currentDay.lifts = None
                else:
                    raise RuntimeError('Error parsing line {} (No ":" found): "{}"'.format(
                        lineNumber + 1, line))
                    # currentDay['lifts'].append({'name': line})
        except:
            raise

    weeks.append(currentWeek)
    return weeks



def writeHTML(weeks, out, header='weekheader.html', programName=''):
    out.write(
        '''<html>
        <link rel="stylesheet" type="text/css" href="style.css">
        <head>
        <body>''')

    for weekNumber, week in enumerate(weeks):

        # Count the maximum number of sets for any exercise this week
        maxSets = 0
        for day in week.days:
            if day.lifts is not None:
                for lift in day.lifts:
                    if isinstance(lift.sets, list):
                        maxSets = max(maxSets, len(lift.sets))

        # Print the name of the week
        with open(header) as weekheader:
            for line in weekheader:
                line = line.replace('{Program_Name}', programName)
                line = line.replace('{Week_Name}', week.name)
                line = line.replace('{Week_Number}', str(weekNumber + 1))
                line = line.replace('{Total_Weeks}', str(len(weeks)))
                out.write(line)

        out.write('<table>\n')

        # Print the table header
        out.write('<tr>\n')
        out.write('  <th>Day</th><th>Exercise</th>')
        # Print the set number headers
        for setNum in range(1, maxSets + 1):
            out.write('  <th>Set {}</th>'.format(setNum))
        out.write('</tr>\n')

        for dayNumber, day in enumerate(week.days):
            # Calculate the number of lifts for this day (or 1 if it is an off day)
            numLifts = len(day.lifts) if day.lifts is not None else 1

            dayClass = 'oddDay' if dayNumber % 2 else 'evenDay'

            # Write out the day cell which covers numLifts rows
            out.write('<tr class="{dayClass}">\n'.format(dayClass=dayClass))
            out.write('<td rowspan="{rowSpan}" class="day">{dayName}</td>\n'.format(rowSpan=numLifts, dayName=day.name))

            if day.lifts is None:
                # If lifts is None then make this an "Off" day
                out.write('<td colspan="{colSpan}" class="off">Off</td>\n'.format(colSpan=maxSets + 1))
                out.write('</tr>\n')

            elif isinstance(day.lifts, list):

                # For each lift in the day, make a new row
                for liftNum, lift in enumerate(day.lifts):
                    if liftNum > 0:
                        out.write('<tr class="{dayClass}">'.format(dayClass=dayClass))
                    out.write('<td class="liftname">{liftName}</td>\n'.format(liftName=lift.name))

                    # Write out each set
                    if isinstance(lift.sets, list):
                        # Right out all of the sets
                        for s in lift.sets:
                            out.write('<td>\n')
                            out.write('  <span class="reps">{reps}</span>\n'.format(reps=s.reps))
                            out.write('  <span class="repsAt">@</span>\n')
                            out.write('  <span class="weight">{weight}</span>\n'.format(weight=s.weight))
                            out.write('</td>\n')

                        # Fill out the unused sets with blank space
                        for i in range(0, maxSets - len(lift.sets)):
                            out.write('<td class="emptyset"></td>\n')
                    else:
                        out.write('<td class="liftdescription" colspan="{colSpan}">{description}</td>'.format(colSpan=maxSets, 
                                                                                                              description=lift.sets.comment))
                    out.write('</tr>')
            else:
                print 'Unknown lift type:', day.lifts
                sys.exit(-1)

            out.write('</tr>\n')

        out.write('</table>\n')

        # Suggest a page-break for printers
        if weekNumber < len(weeks) - 1:
            out.write('<div class="page-break"></div>')

    out.write('</body>')
    out.write('</html>')

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Training Log Parser and Formatter')
    parser.add_argument('input', type=str, help='The input text file')
    parser.add_argument('--output', type=str, default='output.html', help='The output HTML file')
    parser.add_argument('--maxes', type=str, default='maxes.txt', help='The output HTML file')
    parser.add_argument('--programname', type=str, default='Waxmans Gym Training Program', help='The name of the training program')
    args = parser.parse_args()

    with open(args.maxes) as maxFile:
        maxes = parseMaxes(maxFile)

    with open(args.input) as inputFile:
        weeks = parseTraining(inputFile, maxes)

    with open(args.output, 'w') as outputFile:
        writeHTML(weeks=weeks, out=outputFile, header='weekheader.html', programName=args.programname)
