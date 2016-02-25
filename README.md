# Training Format Parser

## Training Days
- Lines beginning with "Week X" (e.g. Week 1, Week 2, etc) will start a new week
- Underneath each "Week X", lines which contain Monday...Sunday will start a new training day
- Each line underneath a training day will be interpreted as a lift, followed by sets and reps for that lift.

## Lifts
A typical lift line is written as follows:
  `PSn {snatch}: 60/2 65/2 70/2 (75/1)2`

- The section before the colon indicates the name of the lift, with an optional
  "base lift" name in curly braces.
  - If a base lift is present, it will be used to calculate any percentages on
    the rest of the line
- Sets and reps are written after the colon

### Sets and Reps

Sets and reps are written as comma or space separated fields. The following are
the three valid ways to write the same sets/reps prescription: 
  - `60%/3`:  1 set of 3 reps at 60%
  - `60/3`: 1 set of 3 reps at 60%
  - `(60/3)/1`: 1 set of 3 reps at 60%

All reps will ignore "+" characters, so that you can also write complexes as follows:
  - `60%/3+3`
  - `60/3+3`
  - `(60/3+3)/1`

### Go for a max!

Sometimes, you may want to give a freeform sentence instead of rigid sets and
reps for a given lift.  You can do this by enclosing your sentence in hard
brackets and putting it in place of a sets/reps scheme. For example:

    `Clean & Jerk: [singles to max (two misses/10 attempts)]`

