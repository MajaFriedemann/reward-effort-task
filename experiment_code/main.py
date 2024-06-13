"""
script for the main task (use the gripper labelled as LEFT)
if using the hand-gripper (rather than DUMMY version), run gripper_calibration.py once before this (only before the first session)
to determine the participant's max grip strength
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
import numpy as np
from psychopy import gui, visual, core, data, event
import helper_functions as hf
import random

print('Reminder: Press Q to quit.')


###################################
# SESSION INFO
###################################
# PARTICIPANT INFO POP-UP
expName = 'reward-effort-pgACC-TUS'
curecID = 'R88533/RE002'
expInfo = {'participant nr': '999',
           'trial schedule': 'A',  # schedule A or B
           'grippers (y/n)': 'n', # if y, use real grippers, if n, use mouse movement
           'eeg (y/n)': 'n',  # if y, send EEG triggers
           'session nr': '1',
           'age': '28',
           'gender (f/m/o)': 'f',
           }
dlg = gui.DlgFromDict(dictionary=expInfo, sortKeys=False, title=expName)
if not dlg.OK:
    core.quit()

# PARTICIPANT MAX GRIP STRENGTH
for filename in os.listdir('calibration_data'):
    if filename.startswith(expInfo['participant nr']) and filename.endswith('.csv'):
        filepath = os.path.join('calibration_data/', filename)
        with open(filepath, 'r') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                max_strength = float(row['max_strength'])
if max_strength is None:
    print('Max strength calibration file for participant not found.')
else:
    print(max_strength)

# TASK VARIABLES
gv = dict(
    # task parameters
    max_strength = max_strength,
    gripper_zero_baseline = None,
    effort_duration = 1,  # second duration for which the effort needs to be above threshold
    time_limit = 8,  # time limit for exerting the effort

    # trial schedule
    num_trials = None,
    outcome = [],
    effort = [],
    action_type = [],
    effort_state = [],
    attention_focus = [],

    # visual parameters
    effort_bar_width = 65,
    effort_bar_height = 138,
)

# READ TRIAL SCHEDULE
if expInfo['trial schedule'] == 'A':
    trial_schedule_filepath = 'trial_schedule_A.csv'
elif expInfo['trial schedule'] == 'B':
    trial_schedule_filepath = 'trial_schedule_B.csv'
else:
    trial_schedule_filepath = None
    print('Error: Choose a valid trial schedule file.')
    core.quit()
if os.path.exists(trial_schedule_filepath):
    max_trial_number = 0
    with open(trial_schedule_filepath, 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            gv['outcome'].append(int(row['outcome']))
            gv['effort'].append(int(row['effort']))
            gv['action_type'].append(row['action_type'])
            gv['effort_state'].append(row['effort_state'])
            gv['attention_focus'].append(row['attention_focus'])
            max_trial_number = max(max_trial_number, int(row['trial_number']))
    gv['num_trials'] = max_trial_number
else:
    print(f"Error: File {trial_schedule_filepath} not found.")
    core.quit()


###################################
# DATA SAVING
###################################
# variables in info will be saved as participant data
info = dict(
    expName=expName,
    curec_ID=curecID,
    trial_schedule = expInfo['trial schedule'],
    session_nr=expInfo['session nr'],
    date=data.getDateStr(),
    end_date=None,

    participant=expInfo['participant nr'],
    age=expInfo['age'],
    gender=expInfo['gender (f/m/o)'],
    max_strength=max_strength,  # from calibration data

    block_count=0,  # block counter
    trial_count=0,  # trial counter
    block_action_type = None,  # approach or avoid
    block_global_effort_state = None,  # low or high
    block_attention_focus = None,  # reward rate or heart rate
    trial_effort = None,  # effort level required in the trial
    trial_outcome = None,  # offered reward/loss

    response=None,  # accept or reject
    response_time=None,  # time taken to accept or reject
    result = None,  # did participant manage to exert the required effort
    points=None,  # points won or lost in the trial
    cumulative_points=None,  # points across trials

    effort_trace='',
    effort_expended=None, # average effort expended on trial during the 1 second where effort is above the threshold
    effort_response_time=None
)

# start a csv file for saving the participant data
log_vars = list(info.keys())
if not os.path.exists('../data'):
    os.mkdir('../data')
filename = os.path.join('../data', '%s_%s_%s' % (info['participant'], info['session_nr'], info['date']))
datafile = open(filename + '.csv', 'w')
datafile.write(','.join(log_vars) + '\n')
datafile.flush()


#####################################
# SET UP WINDOW, MOUSE, HAND GRIPPER
#####################################
# WINDOW
win = visual.Window(
        size=[1512, 982],  # set to actual screen size
        fullscr=True,  # fullscreen mode
        screen=0,
        allowGUI=False,
        color='black',
        blendMode='avg',
        useFBO=True,  # Frame Buffer Object for rendering (good for complex stimuli)
        units='pix'  # units in pixels (fine for this task but for more complex (e.g. dot motion) stimuli, we probably need visual degrees
    )

# MOUSE
mouse = event.Mouse(visible=True, win=win)
win.mouseVisible = True

# HAND GRIPPER
DUMMY = expInfo['grippers (y/n)'].lower() == 'n'
gripper = None
if not DUMMY:
    from mpydev import BioPac
    gripper = BioPac("MP160", n_channels=1, samplerate=200, logfile="test", overwrite=True)
    gripper.start_recording()


###################################
# CREATE STIMULI
###################################
green_button = visual.Rect(win=win, units="pix", width=160, height=80, pos=(0, -270), fillColor='green')
button_txt = visual.TextStim(win=win, text='NEXT', height=25, pos=green_button.pos, color='black', bold=True,font='Monospace')
big_txt = visual.TextStim(win=win, text='Welcome!', height=70, pos=[0, 40], color='white', wrapWidth=800, font='Monospace')
instructions_txt = visual.TextStim(win=win, text="Instructions", height=40, pos=[0, 80], wrapWidth=900, color='white', font='Monospace')
instructions_top_txt = visual.TextStim(win=win, text="Instructions", height=40, pos=[0, 300], wrapWidth=1200, color='white', font='Monospace')
left_side_txt = visual.TextStim(win=win, text='Points', height=70, pos=(-300, 60), color='white', bold=True,font='Monospace')
upper_button = visual.Rect(win=win, units="pix", width=160, height=60, pos=(0, -250), fillColor='white')
upper_button_txt = visual.TextStim(win=win, text='ACCEPT', height=25, pos=upper_button.pos, color='black', bold=True,font='Monospace')
lower_button = visual.Rect(win=win, units="pix", width=160, height=60, pos=(0, -330), fillColor='white')
lower_button_txt = visual.TextStim(win=win, text='REJECT', height=25, pos=lower_button.pos, color='black', bold=True,font='Monospace')


###################################
# INSTRUCTIONS
###################################
# Welcome
big_txt.text = "Welcome to the experiment! Thank you for participating.\n\nClick 'NEXT' to begin."
stimuli = [green_button, button_txt, big_txt]
hf.draw_all_stimuli(win, stimuli)
hf.check_button(win, [green_button], stimuli, mouse) # show instructions until button is pressed

# Calibrate hand gripper
instructions_txt.text = ("First up, we need to calibrate the equipment. So please do not touch the hand gripper yet. \n\n"
                         "Click the 'NEXT' button to begin the calibration process.")
stimuli = [green_button, button_txt, instructions_txt]
hf.draw_all_stimuli(win, stimuli)
hf.check_button(win, [green_button], stimuli, mouse) # show instructions until button is pressed

# CALIBRATE HAND GRIPPER ZERO BASELINE
win.flip()
instructions_top_txt.text = "Calibration in progress. Do not touch the hand gripper."
hf.draw_all_stimuli(win, [instructions_top_txt], 1)
for countdown in range(3, 0, -1):
    big_txt.text = str(countdown)
    hf.draw_all_stimuli(win, [instructions_top_txt, big_txt], 1) # display a 3, 2, 1 countdown
    if not DUMMY and countdown == 3:
        gv['gripper_zero_baseline'] = gripper.sample()[0] # on 1, sample the gripper 0 baseline

# Task overview
instructions_txt.text = ("Great! Calibration is done.\n\n"
                         "In this task, you will control a spaceship. Your goal is to fill it with fuel by exerting effort using a handgripper.\n\n"
                         "Click 'NEXT' to learn more about the task.")
stimuli = [green_button, button_txt, instructions_txt]
hf.draw_all_stimuli(win, stimuli, 1)
hf.check_button(win, [green_button], stimuli, mouse) # show instructions until button is pressed

# Block types
instructions_txt.text = ("There are two types of blocks:\n\n"
                         "1. Approach Blocks: There will be a cloud of stars. The number of stars indicates the reward you can earn. If you "
                         "accept the offer, you need to exert the required effort to get the reward. If you reject, you get no reward. "
                         "If you fail to exert the required effort after accepting, you will lose points.\n\n"
                         "2. Avoid Blocks: There will be a cloud of meteors. The number of meteors indicates the loss you can incur. "
                         "If you accept the offer, you need to exert the required effort to avoid the loss. If you reject, you incur the loss. "
                         "If you fail to exert the required effort after accepting, you will incur an even bigger loss.\n\n"
                         "Click 'NEXT' to see examples.")
stimuli = [green_button, button_txt, instructions_txt]
hf.draw_all_stimuli(win, stimuli, 1)
hf.check_button(win, [green_button], stimuli, mouse) # show instructions until button is pressed

# Visual example
instructions_txt.text = ("Here are examples of what you will see:\n\n"
                         "In Approach Blocks, you will see a cloud of stars indicating potential rewards.\n\n"
                         "In Avoid Blocks, you will see a cloud of meteors indicating potential losses.\n\n"
                         "Click 'NEXT' to start the task.")
stimuli = [green_button, button_txt, instructions_txt]
hf.draw_all_stimuli(win, stimuli, 1)
hf.check_button(win, [green_button], stimuli, mouse) # show instructions until button is pressed


###################################
# TASK
###################################
previous_action_type = None  # Initialize to None to avoid comparison on the first trial
win.flip()
while info['trial_count'] < gv['num_trials']:
    # Set window color to blue at the start of each trial
    win.color = hf.convert_rgb_to_psychopy([0, 38, 82])
    win.flip()
    core.wait(1)

    # trial info
    trial_effort = gv['effort'][info['trial_count']]
    trial_outcome = gv['outcome'][info['trial_count']]
    action_type = gv['action_type'][info['trial_count']]
    effort_state = gv['effort_state'][info['trial_count']]
    attention_focus = gv['attention_focus'][info['trial_count']]

    # MAJA - JUST FOR TESTING!!! changes block type every 3 trials
    if (info['trial_count'] // 3) % 2 == 0:
        action_type = 'approach'
    else:
        action_type = 'avoid'
        trial_outcome = -abs(gv['outcome'][info['trial_count']])

    # Check for action type change, skip comparison on the first trial
    if previous_action_type is not None and action_type != previous_action_type:
        win.color = 'black'  # Set window color to black before instructions
        instructions_txt.text = f"The next block of trials will be {action_type}. \n\nClick the NEXT button when you are ready to begin."
        stimuli = [instructions_txt, green_button, button_txt]
        hf.draw_all_stimuli(win, stimuli)
        hf.check_button(win, [green_button], stimuli, mouse)
    previous_action_type = action_type

    # draw stimuli
    spaceship, outline, target, effort_text, outcomes = hf.draw_trial_stimuli(win, trial_effort, trial_outcome, action_type, gv)
    stimuli = [spaceship, outline, target, effort_text, outcomes, upper_button, upper_button_txt, lower_button, lower_button_txt]
    hf.draw_all_stimuli(win, stimuli)
    clicked_button, response_time = hf.check_button(win, [upper_button, lower_button], stimuli, mouse)

    # accept
    if clicked_button == upper_button:
        response = 'accept'
        stimuli = [spaceship, outline, target, effort_text, outcomes]
        result, effort_trace, average_effort, effort_time = hf.sample_effort(win, DUMMY, mouse, gripper, stimuli, trial_effort, target, gv)
        # success
        if result == 'success':
            if action_type == 'approach':
                points = trial_outcome
            elif action_type == 'avoid':
                points = 0
            hf.animate_success(win, spaceship, outcomes, target, outline, points, action_type)
        # failure
        elif result == 'failure':
            if action_type == 'approach':
                points = -10  # MAJA - how many points should be lost?
            elif action_type == 'avoid':
                points = -120  # MAJA - how many points should be lost?
            hf.animate_failure(win, spaceship, outline, target, outcomes, points, action_type)

    # reject
    elif clicked_button == lower_button:
        response = 'reject'
        result, effort_trace, average_effort, effort_time = None, None, None, None
        if action_type == 'approach':
            points = 0
        elif action_type == 'avoid':
            points = trial_outcome
        hf.animate_reject(win, spaceship, outline, target, outcomes, points, action_type)


    # save trial data
    info['trial_count'] += 1
    info['block_action_type'] = action_type
    info['block_global_effort_state'] = effort_state
    info['block_attention_focus'] = attention_focus
    info['trial_effort'] = trial_effort
    info['trial_outcome'] = trial_outcome
    info['response'] = response
    info['response_time'] = response_time
    info['result'] = result
    info['effort_trace'] = '"' + json.dumps(effort_trace) + '"'
    info['effort_expended'] = average_effort
    info['effort_response_time'] = effort_time
    info['points'] = points
    info['cumulative_points'] = int(info['cumulative_points']) + points if info['cumulative_points'] is not None else points
    datafile.write(','.join([str(info[var]) for var in log_vars]) + '\n')
    datafile.flush()



# CLOSE WINDOW
win.close()
core.quit()