import sys
# from pprint import pprint
import re

maxes = {
    'snatch': 100,
    'c&j': 100,
    'squat': 100
}

######################################################################
# Parsing
######################################################################

infile = open(sys.argv[1], 'r')

weeks = []

currentWeek = None
currentDay = None

daysOfTheWeek = ('monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday')

for lineNumber, line in enumerate(infile):
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
                                raise runtimeerror('unrecognized sets/reps scheme on line {}: "{}"'.format(
                                    linenumber + 1, line))
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
            elif line.lower() == 'off':
                currentDay['lifts'] = None
            else:
                raise RuntimeError('Error parsing line {} (No ":" found): "{}"'.format(
                    lineNumber + 1, line))
                # currentDay['lifts'].append({'name': line})
    except:
        print 'Error parsing line {}: "{}"'.format(lineNumber + 1, line)
        raise


weeks.append(currentWeek)

# pprint(weeks)

######################################################################
# Output
######################################################################

with open('output.html', 'w') as out:
    out.write(
        '''<html>
             <style type="text/css">
                 @media all {
                 .page-break	{ display: none; }
                 }

                 @media print {
                 .page-break	{ display: block; page-break-before: always; }
                 }

                 th, td { border: 1px solid black; }
                 table { border-collapse: collapse; }
             </style>
        <head>
        <body>''')

    for weekNumber, week in enumerate(weeks):

        # Count the maximum number of sets for any exercise this week
        maxSets = 0
        for day in week['days']:
            if day['lifts'] is not None:
                for lift in day['lifts']:
                    if isinstance(lift['sets'], list):
                        maxSets = max(maxSets, len(lift['sets']))

        # Print the name of the week
        out.write('<h2>{weekName}</h2>\n'.format(weekName=week['name']))

        out.write('<table>\n')

        # Print the table header
        out.write('<tr>\n')
        out.write('  <th>Day</th><th>Exercise</th>')
        # Print the set number headers
        for setNum in range(1, maxSets + 1):
            out.write('  <th>Set {}</th>'.format(setNum))
        out.write('</tr>\n')

        for day in week['days']:
            # Calculate the number of lifts for this day (or 1 if it is an off day)
            numLifts = len(day['lifts']) if day['lifts'] is not None else 1

            # Write out the day cell which covers numLifts rows
            out.write('<tr>\n')
            out.write('<td rowspan="{rowSpan}">{dayName}</td>\n'.format(rowSpan=numLifts, dayName=day['name']))

            if day['lifts'] is None:
                # If lifts is None then make this an "Off" day
                out.write('<td colspan="{colSpan}">Off</td>\n'.format(colSpan=maxSets + 1))
                out.write('</tr>\n')

            elif isinstance(day['lifts'], list):

                # For each lift in the day, make a new row
                for liftNum, lift in enumerate(day['lifts']):
                    if liftNum > 0:
                        out.write('<tr>')
                    out.write('<td>{liftName}</td>\n'.format(liftName=lift['name']))

                    # Write out each set
                    if isinstance(lift['sets'], list):
                        # Right out all of the sets
                        for s in lift['sets']:
                            out.write('<td>{reps} @ {weight}</td>\n'.format(reps=s['reps'], weight=s['weight']))

                        # Fill out the unused sets with blank space
                        for i in range(0, maxSets - len(lift['sets'])):
                            out.write('<td></td>\n')
                    else:
                        out.write('<td colspan="{colSpan}">{description}</td>'.format(colSpan=maxSets, description=lift['sets']))
                    out.write('</tr>')
            else:
                print 'Unknown lift type:', day['lifts']
                sys.exit(-1)

            out.write('</tr>\n')

        out.write('</table>\n')

        # Suggest a page-break for printers
        if weekNumber < len(weeks) - 1:
            out.write('<div class="page-break"></div>')

    out.write('</body>')
    out.write('</html>')



# doc, tag, text = yattag.Doc().tagtext()

# with tag('html'):
#     with tag('head'):
#         doc.asis(r"""
#              <style type="text/css">
#                  @media all {
#                  .page-break	{ display: none; }
#                  }
# 
#                  @media print {
#                  .page-break	{ display: block; page-break-before: always; }
#                  }
# 
#                  th, td { border: 1px solid black; }
#                  table { border-collapse: collapse; }
#              </style>
#              """)
#     with tag('body'):
#         with tag('h1'):
#             text('Training Log')
# 
#         for weekNumber, week in enumerate(weeks):
# 
#             # Count the maximum number of sets for any exercise this week
#             maxSets = 0
#             for day in week['days']:
#                 if day['lifts'] is not None:
#                     for lift in day['lifts']:
#                         if isinstance(lift['sets'], list):
#                             maxSets = max(maxSets, len(lift['sets']))
# 
#             # Print the name of the week
#             with tag('h2'):
#                 text(''.format(week['name']))
# 
#             with tag('table'):
# 
#                 # Print the table header
#                 with tag('tr'):
#                     with tag('th'):
#                         text('Day')
#                     with tag('th'):
#                         text('Exercise')
# 
#                     # Print the set number headers
#                     for setNum in range(1, maxSets + 1):
#                             with tag('th'):
#                                 text('Set {}'.format(setNum))
# 
#                 for day in week['days']:
#                     # Calculate the number of lifts for this day (or 1 if it is an off day)
#                     numLifts = len(day['lifts']) if day['lifts'] is not None else 1
# 
#                     # Write out the day cell which covers numLifts rows
#                     with tag('tr'):
#                         with tag('td', rowspan=numLifts + 1):
#                             text(day['name'])
# 
#                     if day['lifts'] is None:
#                         # If lifts is None then make this an "Off" day
#                         with tag('tr'):
#                             with tag('td', colspan=maxSets + 1):
#                                 text('Off')
#                     elif isinstance(day['lifts'], list):
# 
#                         # For each lift in the day, make a new row
#                         for lift in day['lifts']:
#                             with tag('tr'):
#                                 with tag('td'):
#                                     text(lift['name'])
# 
#                                 # Write out each set
#                                 if isinstance(lift['sets'], list):
#                                     for s in lift['sets']:
#                                         with tag('td'):
#                                             text('{} @ {}'.format(s['reps'], s['weight']))
#                                     for i in range(0, maxSets - len(lift['sets'])):
#                                         with tag('td'):
#                                             text('')
#                                 else:
#                                     with tag('td', colspan=maxSets):
#                                         text(lift['sets'])
# 
#                     else:
#                         print 'Unknown lift type:', day['lifts']
#                         sys.exit(-1)
# 
#             # Suggest a page-break for printers
#             if weekNumber < len(weeks) - 1:
#                 with tag('div', klass='page-break'):
#                     pass
# 
# 
# with open('output.html', 'w') as outfile:
#     outfile.write(doc.getvalue())
