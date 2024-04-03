"""
script for the main task (use the gripper labelled as LEFT)
if using the hand-gripper (rather than DUMMY version), run gripper_calibration.py before this to determine the participant's max grip strength
with 'strength' I refer to raw grip strength
with 'effort' I refer to grip strength relative to the participant's max strength (as determined with gripper_calibration.py)

Maja Friedemann 2024
"""

###################################
# IMPORT PACKAGES
###################################
import os
import csv
import json
import random
import numpy as np
from psychopy import gui, visual, core, data, event
import helper_functions as hf

print('Reminder: Press Q to quit.')


###################################
# SESSION INFO
###################################
expName = 'reward-strength-pgACC-TUS'
curecID = 'R88533/RE002'
expInfo = {'participant nr': '999',
           'dummy (y/n)': 'y',
           'session nr': '1',
           'age': '',
           'gender (f/m/o)': '',
           }
dlg = gui.DlgFromDict(dictionary=expInfo, sortKeys=False, title=expName) # pop-up window asking for participant number and which hand they will use for the gripper (they need to be happy to use the respective other hand for the keyboard)
if not dlg.OK:
    core.quit()

# get participant's max strength from calibration_data
for filename in os.listdir('calibration_data'):
    if filename.startswith(expInfo['participant nr']) and filename.endswith('.csv'):
        filepath = os.path.join('calibration_data', filename)
        with open(filepath, 'r') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                max_strength = float(row['max_strength'])
if max_strength is None:
    print('Max strength calibration file for participant not found.')
else:
    print(max_strength)

# variables in gv are used to structure the task
gv = dict(
    n_trials_per_combination=5,
    effort_levels = [40, 60, 80, 100],
    outcome_mean_magnitude_levels= [5, 7, 9],
    outcome_uncertainty_levels = ['safe', '25/50/25', '50/50'],
)


###################################
# DATA SAVING
###################################
# variables in info will be saved as participant data
info = dict(
    expName=expName,
    curec_ID=curecID,
    session_nr=expInfo['session nr'],
    date=data.getDateStr(),
    end_date=None,

    participant=expInfo['participant nr'],
    age=expInfo['age'],
    gender=expInfo['gender (f/m/o)'],
    max_strength=max_strength,  # from calibration data

    block_count=0,  # block counter
    trial_count=0,  # trial counter

    block_type='',  # approach or avoid block
    outcome_mean_magnitude=None,
    outcome_uncertainty=None,
    effort_required=None,  # effort level to approach/avoid the outcome
    response=None,  # accept or reject
    response_time=None,  # time taken to accept or reject
    points=None,  # points won or lost in the trial
    cumulative_points=None,  # points across trials

    strength_trace='',
    effort_trace='',
    effort_expended=None, # actual effort expended on trial during the 1 second where effort is above the threshold
    effort_response_time=None
)

# start a csv file for saving the participant data
log_vars = list(info.keys())
if not os.path.exists('data'):
    os.mkdir('data')
filename = os.path.join('data', '%s_%s_%s' % (info['participant'], info['session_nr'], info['date']))
datafile = open(filename + '.csv', 'w')
datafile.write(','.join(log_vars) + '\n')
datafile.flush()


###################################
# HAND GRIPPER
###################################
DUMMY = expInfo['dummy (y/n)'].lower() == 'y'
gripper = None
if not DUMMY:
    from mpydev import BioPac
    gripper = BioPac("MP160", n_channels=1, samplerate=200, logfile="test", overwrite=True)
    gripper.start_recording()


###################################
# SET UP WINDOW
###################################
win = visual.Window(
    size=[1512, 982],  # set correct monitor size
    fullscr=True,  # fullscreen mode
    screen=0,  # adjust if using multiple monitors
    allowGUI=False,
    color='black',
    blendMode='avg',
    useFBO=True,  # Frame Buffer Object for rendering (good for complex stimuli)
    units='pix'  # units in pixels (fine for this task but for more complex (e.g. dot motion) stimuli, we probably need visual degrees
)


###################################
# CREATE STIMULI
###################################
green_button = visual.Rect(win=win, units="pix", width=160, height=60, pos=(0, -270), fillColor='green')
button_txt = visual.TextStim(win=win, text='NEXT', height=25, pos=green_button.pos, color='black', bold=True,font='Monospace')
big_txt = visual.TextStim(win=win, text='Welcome!', height=90, pos=[0, 40], color='white', wrapWidth=800, font='Monospace')
instructions_txt = visual.TextStim(win=win, text="Instructions", height=40, pos=[0, 80], wrapWidth=900, color='white', font='Monospace')
instructions_top_txt = visual.TextStim(win=win, text="Instructions", height=40, pos=[0, 220], wrapWidth=1200, color='white', font='Monospace')
upper_button = visual.Rect(win=win, units="pix", width=160, height=60, pos=(0, -240), fillColor='white')
upper_button_txt = visual.TextStim(win=win, text='ACCEPT', height=25, pos=upper_button.pos, color='black', bold=True,font='Monospace')
lower_button = visual.Rect(win=win, units="pix", width=160, height=60, pos=(0, -320), fillColor='white')
lower_button_txt = visual.TextStim(win=win, text='REJECT', height=25, pos=lower_button.pos, color='black', bold=True,font='Monospace')


###################################
# TASK
###################################
# INITIALISE CLOCK AND MOUSE
globalClock = core.Clock()
mouse = event.Mouse()
win.mouseVisible = True


# WELCOME
stimuli = [green_button, button_txt, big_txt]
hf.draw_all_stimuli(win, stimuli)
hf.check_button(win, green_button, stimuli, mouse) # show instructions until button is pressed


# # INSTRUCTIONS
# instructions_txt.text = ("Let's get ready to measure your grip strength! \n\n"
#                          "First up, we need to calibrate the equipment. So please do not touch the hand gripper yet. \n\n"
#                          "Click the 'NEXT' button to begin the calibration process.")
# stimuli = [green_button, button_txt, instructions_txt]
# hf.draw_all_stimuli(win, stimuli)
# hf.check_button(win, green_button, stimuli, mouse) # show instructions until button is pressed
#
#
# # CALIBRATE HAND GRIPPER ZERO BASELINE
# instructions_top_txt.text = "Calibration in progress. Do not touch the hand gripper."
# hf.draw_all_stimuli(win, [instructions_top_txt], 1)
# gripper_zero_baseline = None
# for countdown in range(3, 0, -1):
#     big_txt.text = str(countdown)
#     hf.draw_all_stimuli(win, [instructions_top_txt, big_txt], 1) # display a 3, 2, 1 countdown
#     if not DUMMY and countdown == 3:
#         gripper_zero_baseline = gripper.sample()[0] # on 1, sample the gripper 0 baseline
#
#
# # INSTRUCTIONS
# instructions_txt.text = ("Great! Calibration is done. \n\n"
#                          "Now, please pick up the hand gripper with the hand you're not using for the mouse. Make sure you have a comfortable yet firm grip. \n\n"
#                          "There will be 3 trials. When you feel ready to show us how strong your grip is, press 'NEXT' to begin.")
# stimuli = [green_button, button_txt, instructions_txt]
# hf.draw_all_stimuli(win, stimuli, 1)
# hf.check_button(win, green_button, stimuli, mouse) # show instructions until button is pressed


# TASK
trial_schedule = hf.generate_trial_schedule(gv['n_trials_per_combination'], gv['effort_levels'], gv['outcome_mean_magnitude_levels'], gv['outcome_uncertainty_levels'])

# loop over the trial_schedule dataframe
for i, trial in trial_schedule.iterrows():
    bars = hf.outcome_bars(win, trial['mean_magnitude'], trial['uncertainty'], np.max(gv['outcome_mean_magnitude_levels']))
    effort_bar = hf.effort_bar(win, trial['effort'])
    stimuli = [bars, effort_bar, upper_button, upper_button_txt, lower_button, lower_button_txt]
    hf.draw_all_stimuli(win, stimuli)
    hf.check_button(win, upper_button, stimuli, mouse)






# CLOSE WINDOW
win.close()
core.quit()