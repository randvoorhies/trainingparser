import sys
from pprint import pprint
import re

maxes = {
    'snatch': 100,
    'c&j': 120,
    'squat': 160
}

infile = open(sys.argv[1], 'r')

weeks = []

currentWeek = None
currentDay = None

daysOfTheWeek = ('monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday')

for lineNumber, line in enumerate(infile):
    try:
        # Strip out any leading and trailing whitespace
        line = line.strip()

        # print line

        # If the line starts with "Week", then let's start a new week
        if line.lower().startswith('week'):
            # If we were already parsing a week, push it onto the list of weeks
            if currentWeek is not None:
                currentWeek['days'].append(currentDay)
                currentDay = None
                weeks.append(currentWeek)
            currentWeek = {'name': line, 'days': []}

        # If the line starts with the name of a day, then let's start a new day
        elif line.lower().startswith(daysOfTheWeek):
            # If we were already parsing a day, push it onto the current week's list of days
            if currentDay is not None:
                currentWeek['days'].append(currentDay)
            currentDay = {'name': line, 'lifts': []}

        # Otherwise, interpret this as a lift and add it to the current day
        elif len(line) > 0:
            if ':' in line:
                liftName = line.split(':')[0].split('{')[0].strip()

                # Check to see if there is something in curly braces in the lift name
                # to interpret as a base lift on which we should base our percentages
                if '{' in line.split(':')[0]:
                    baseLift = re.search('\{(.*)\}', line).group(1)
                else:
                    baseLift = None

                # Split the sets and reps string
                setsAndRepsString = line.split(':')[1].strip()

                sets = None

                # If the sets and reps section starts with a hard bracket "[", then it is
                # a special comment (e.g. [singles to max])
                if setsAndRepsString.startswith('['):
                    sets = setsAndRepsString.replace('[', '').replace(']', '')
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
                                raise RuntimeError('Unrecognized sets/reps scheme on line {}: "{}"'.format(
                                    lineNumber + 1, line))
                        else:
                            # Try to match weight/reps lines
                            match = re.match(r'(\d*)%?\/(\d*\+?\d*)', setString)
                            if match:
                                percent = match.group(1)
                                numReps = match.group(2)
                                numSets = 1
                                # print '>>>>>', setString, percent, numReps
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
                            sets.append({
                                'weight': weight,
                                'reps': numReps
                            })

                currentLift = {
                    'name': liftName,
                    'baseLift': baseLift,
                    'sets': sets
                }
                currentDay['lifts'].append(currentLift)

                # print line
            else:
                currentDay['lifts'].append({'name': line})
    except:
        print 'Error parsing line {}: "{}"'.format(lineNumber + 1, line)
        raise


weeks.append(currentWeek)

# pprint(weeks)
