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
import serial  # serial port for eeg triggering

print('Reminder: Press Q to quit.')


###################################
# SESSION INFO
###################################
# PARTICIPANT INFO POP-UP
expName = 'reward-effort-pgACC-TUS'
curecID = 'R88533/RE002'
expInfo = {'participant nr': '999',
           'trial schedule': 'testing',  # schedule A or B, 1-8 (e.g. A_1), 'testing' for testing, 'traning' for training session
           'grippers (y/n)': 'n', # if y, use real grippers, if n, use mouse movement
           'eeg (y/n)': 'n',  # if y, send EEG triggers, if n, just print them
           'session nr': '0',  # 0 for training session
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
    effort_started_threshold=0.1,  # threshold to consider effort exertion started for EEG trigger
    net_value_shift = 15,  # shift in net value for shifted effort state
    assumed_k = 1.1,  # assumed k value for effort shift calculation
    training = False,  # training session

    # trial schedule
    num_trials = None,
    block_number = [],
    outcome_level = [],
    actual_outcome = [],
    effort = [],
    action_type = [],
    attention_focus = [],
    rating_trial = [],
    effort_state = [],

    # visual parameters
    effort_bar_width = 65,
    effort_bar_height = 138,
)

# READ TRIAL SCHEDULE
trial_schedule_key = expInfo['trial schedule']
trial_schedule_filepath = f'../final_trial_schedules/schedule_{trial_schedule_key}.csv'
if os.path.exists(trial_schedule_filepath):
    max_trial_number = 0
    with open(trial_schedule_filepath, 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            gv['block_number'].append(int(row['block_number']))
            gv['outcome_level'].append(int(row['outcome_level']))
            gv['actual_outcome'].append(int(row['actual_outcome']))
            gv['effort'].append(int(row['effort']))
            gv['action_type'].append(row['action_type'])
            gv['attention_focus'].append(row['attention_focus'])
            gv['rating_trial'].append(row['rating'])
            gv['effort_state'].append(row['global_effort_state'])
            max_trial_number = max(max_trial_number, int(row['trial_in_experiment']))
    gv['num_trials'] = max_trial_number
else:
    print(f"Error: File {trial_schedule_filepath} not found.")
    core.quit()

if expInfo['trial schedule'] == 'training':
    gv['training'] = True
else:
    pass

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

    block_number=0,  # block counter
    trial_count=0,  # trial counter
    block_action_type = None,  # approach or avoid
    block_global_effort_state = None,  # low or high
    block_attention_focus = None,  # reward rate or heart rate
    trial_rating = None,  # heart or reward rate rating
    trial_effort = None,  # effort level required in the trial
    trial_outcome_level = None,  # offered reward/loss
    trial_actual_outcome = None,

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
if not os.path.exists('data'):
    os.mkdir('data')
filename = os.path.join('data', '%s_%s_%s' % (info['participant'], info['session_nr'], info['date']))
datafile = open(filename + '.csv', 'w')
datafile.write(','.join(log_vars) + '\n')
datafile.flush()


##################################################
# SET UP WINDOW, MOUSE, HAND GRIPPER, EEG TRIGGERS
##################################################
# WINDOW
win = visual.Window(
        size=[1512, 982],  # set to actual screen size
        fullscr=True,  # fullscreen mode
        screen=1,
        allowGUI=False,
        color='black',
        blendMode='avg',
        useFBO=True,  # Frame Buffer Object for rendering (good for complex stimuli)
        units='pix'  # units in pixels (fine for this task but for more complex (e.g. dot motion) stimuli, we probably need visual degrees
    )

# MOUSE
mouse = event.Mouse(visible=True, win=win)
mouse.setVisible(True)
win.setMouseVisible(True)

# HAND GRIPPER
DUMMY = expInfo['grippers (y/n)'].lower() == 'n'
gripper = None
if not DUMMY:
    from mpydev import BioPac
    gripper = BioPac("MP160", n_channels=1, samplerate=200, logfile="test", overwrite=True)
    gripper.start_recording()

# EEG TRIGGERS
triggers = dict(
    experiment_start = 1,
    block_start = 2,
    offer_presentation_approach = 3,
    offer_presentation_avoid = 4,
    participant_choice_accept = 5,
    participant_choice_reject = 6,
    rating_question_reward = 7,
    rating_question_heart = 8,
    rating_response_reward = 9,
    rating_response_heart = 10,
    effort_started = 11,
    effort_threshold_crossed = 12,
    effort_success = 13,
    outcome_presentation_approach_success = 14,
    outcome_presentation_approach_failure = 15,
    outcome_presentation_approach_reject = 16,
    outcome_presentation_avoid_success = 17,
    outcome_presentation_avoid_failure = 18,
    outcome_presentation_avoid_reject = 19,
    experiment_end = 20
)
# Create an EEGConfig object
send_triggers = expInfo['eeg (y/n)'].lower() == 'y'
EEG_config = hf.EEGConfig(triggers, send_triggers)


###################################
# CREATE STIMULI
###################################
green_button = visual.Rect(win=win, units="pix", width=160, height=80, pos=(0, -280), fillColor='green')
button_txt = visual.TextStim(win=win, text='NEXT', height=28, pos=green_button.pos, color='black', bold=True,font='Monospace')
big_txt = visual.TextStim(win=win, text='Welcome!', height=80, pos=[0, 200], color='white', wrapWidth=1100, font='Monospace')
instructions_txt = visual.TextStim(win=win, text="Instructions", height=40, pos=[0, 100], wrapWidth=1100, color='white', font='Monospace')
instructions_top_txt = visual.TextStim(win=win, text="Instructions", height=40, pos=[0, 300], wrapWidth=1200, color='white', font='Monospace')
left_side_txt = visual.TextStim(win=win, text='Points', height=70, pos=(-300, 60), color='white', bold=True,font='Monospace')
upper_button = visual.Rect(win=win, units="pix", width=160, height=60, pos=(0, -250), fillColor='white')
upper_button_txt = visual.TextStim(win=win, text='ACCEPT', height=25, pos=upper_button.pos, color='black', bold=True,font='Monospace')
lower_button = visual.Rect(win=win, units="pix", width=160, height=60, pos=(0, -330), fillColor='white')
lower_button_txt = visual.TextStim(win=win, text='REJECT', height=25, pos=lower_button.pos, color='black', bold=True,font='Monospace')


###################################
# INSTRUCTIONS
###################################
if gv['training']:
    hf.training_instructions_1(big_txt, instructions_txt, green_button, button_txt, win, mouse)
else:
    # Welcome
    big_txt.text = "Welcome!"
    instructions_txt.text = ("\n\n\n\n\nThis is the same task you practiced in your training session. We'll go over some quick "
                             "instructions as a reminder of how the task works.\n\nWhen you're ready to begin, click 'NEXT'.")
    stimuli = [green_button, button_txt, big_txt, instructions_txt]
    hf.draw_all_stimuli(win, stimuli)
    hf.check_button(win, [green_button], stimuli, mouse)
    EEG_config.send_trigger(EEG_config.triggers['experiment_start'])

    # Calibrate hand gripper
    instructions_txt.text = ("As you remember, in this task, you'll use a hand gripper to exert effort. "
                             "\n\nBefore we start, we need to quickly recalibrate the equipment. "
                             "Please don't touch the hand gripper yet.\n\n"
                             "Click 'NEXT' to begin the calibration process.")
    stimuli = [green_button, button_txt, instructions_txt]
    hf.draw_all_stimuli(win, stimuli)
    hf.check_button(win, [green_button], stimuli, mouse)


# CALIBRATE HAND GRIPPER ZERO BASELINE
win.flip()
instructions_top_txt.text = "Calibration in progress. \n\nPlease keep your hands away from the gripper."
hf.draw_all_stimuli(win, [instructions_top_txt], 1)
big_txt.pos = [0, 20]
for countdown in range(3, 0, -1):
    big_txt.text = str(countdown)
    hf.draw_all_stimuli(win, [instructions_top_txt, big_txt], 1)
    if not DUMMY and countdown == 1:
        gv['gripper_zero_baseline'] = gripper.sample()[0]
win.flip()
core.wait(1)


if gv['training']:
    hf.training_instructions_2(big_txt, instructions_txt, green_button, button_txt, win, mouse)
else:
    # Task overview
    instructions_txt.text = ("Great! Calibration is complete.\n\n"
                             "Just to remind you, in this task, you'll control a spaceship. Your goal is to fill it with fuel by exerting effort using the handgripper.\n\n"
                             "Click 'NEXT' to review the task details.")
    stimuli = [green_button, button_txt, instructions_txt]
    hf.draw_all_stimuli(win, stimuli, 1)
    hf.check_button(win, [green_button], stimuli, mouse)

    # Block types
    instructions_txt.text = ("As you practiced before, there are two types of blocks:\n\n"
                             "In approach blocks, you'll see a cloud of stars. The number of stars indicates the reward you can earn. "
                             "If you accept the offer, you need to exert the required effort to get the reward. If you reject or fail to "
                             "exert the required effort, you get no reward.\n\nIn avoid blocks, you'll see a cloud of meteors. The number "
                             "of meteors indicates the potential loss. If you accept the offer, you need to exert the required effort "
                             "to avoid the loss. If you reject or fail to exert the required effort, you incur the loss.")
    stimuli = [green_button, button_txt, instructions_txt]
    hf.draw_all_stimuli(win, stimuli, 1)
    hf.check_button(win, [green_button], stimuli, mouse)

    # Monetary reward
    instructions_txt.text = ("At the end of the task, we'll randomly select xx trials, and your points will be converted into a monetary reward. "
                             "\n\nEach point is worth 1p. For example, if you have 100 points, you'll win £1.")
    stimuli = [green_button, button_txt, instructions_txt]
    hf.draw_all_stimuli(win, stimuli, 1)
    hf.check_button(win, [green_button], stimuli, mouse)

    # Ratings
    instructions_txt.text = ("Throughout this experiment, you'll occasionally be asked about your heart rate or your reward rate. "
                             "\n\nWhen asked, please consider your recent experiences in relation to your overall average experiences during the experiment.")
    stimuli = [green_button, button_txt, instructions_txt]
    hf.draw_all_stimuli(win, stimuli, 1)
    hf.check_button(win, [green_button], stimuli, mouse)

    # Start
    win.flip()
    big_txt.pos = [0, 70]
    big_txt.text = "Take the gripper in your hand and let's begin!"
    big_txt.draw()
    win.flip()
    core.wait(2)


###################################
# TASK
###################################
current_block = 0
current_action_type = None
while info['trial_count'] < gv['num_trials']:  # this must be < because we start with trial_count = 0

    # pause for ca. 1 second between trials
    win.flip()
    base_wait_time = 1
    jitter_range = 0.25  # (±0.25 seconds)
    jittered_wait_time = base_wait_time + random.uniform(-jitter_range, jitter_range)
    core.wait(jittered_wait_time)

    # reset variables
    response = None
    points = None
    rating = None
    result = None
    effort_trace = None
    effort_time = None
    average_effort = None
    action_text = None

    # trial info
    block_number = gv['block_number'][info['trial_count']]
    trial_effort = gv['effort'][info['trial_count']]
    trial_outcome_level = gv['outcome_level'][info['trial_count']]
    trial_actual_outcome = gv['actual_outcome'][info['trial_count']]
    action_type = gv['action_type'][info['trial_count']]
    effort_state = gv['effort_state'][info['trial_count']]
    attention_focus = gv['attention_focus'][info['trial_count']]
    rating_trial = gv['rating_trial'][info['trial_count']]


    ##########################################################################################
    ################################## FOR TESTING ###########################################
    ##########################################################################################
    # rating_trial = "TRUE"
    # effort_state = 'shifted'
    ##########################################################################################
    ##########################################################################################

    # check if action_type has changed
    if action_type != current_action_type:
        big_txt.pos = [0, 120]
        win.color = 'black'  # set window color to black for block message
        win.flip()
        current_action_type = action_type
        if action_type == 'approach':
            big_txt.text = "Your mission is to collect stars to earn points. \n\nGood luck!"
        elif action_type == 'avoid':
            big_txt.text = "Your mission is to evade meteors to avoid losing points. \n\nGood luck!"
        stimuli = [green_button, button_txt, big_txt]
        hf.draw_all_stimuli(win, stimuli, 1)
        hf.check_button(win, [green_button], stimuli, mouse)

    # check if we are at the beginning of a new block
    if block_number != current_block:
        EEG_config.send_trigger(EEG_config.triggers['block_start'])
        current_block = block_number
        win.color = 'black'  # set window color to black for block message
        button_txt.text = 'START'
        win.flip()
        if action_type == 'approach':
            action_text = "collect stars to earn points"
        elif action_type == 'avoid':
            action_text = "evade meteors to avoid losing points"
        instructions_txt.text = (
            f"This is block {current_block} of {max(gv['block_number'])}.\n\n"
            f"Your mission is to {action_text}.\n\n"
            f"Throughout this block, pay attention to your {attention_focus} rate.\n\n"
            "When you're ready to continue, click the 'START' button."
        )
        stimuli = [green_button, button_txt, instructions_txt]
        hf.draw_all_stimuli(win, stimuli, 1)
        hf.check_button(win, [green_button], stimuli, mouse)
        win.color = hf.convert_rgb_to_psychopy([0, 38, 82])  # set window color back to blue for trials
        button_txt.text = 'NEXT'  # reset button text
    else:
        pass

    # draw stimuli
    spaceship, outline, target, effort_text, outcomes = hf.draw_trial_stimuli(win, trial_effort, trial_outcome_level, action_type, gv)
    stimuli = [spaceship, outline, target, effort_text, outcomes, upper_button, upper_button_txt, lower_button, lower_button_txt]
    hf.draw_all_stimuli(win, stimuli)
    if action_type == 'approach':
        EEG_config.send_trigger(EEG_config.triggers['offer_presentation_approach'])
    elif action_type == 'avoid':
        EEG_config.send_trigger(EEG_config.triggers['offer_presentation_avoid'])
    clicked_button, response_time = hf.check_button(win, [upper_button, lower_button], stimuli, mouse)

    # accept
    if clicked_button == upper_button:
        EEG_config.send_trigger(EEG_config.triggers['participant_choice_accept'])
        response = 'accept'
        stimuli = [spaceship, outline, target, effort_text, outcomes]
        result, effort_trace, average_effort, effort_time = hf.sample_effort(win, DUMMY, mouse, gripper, stimuli, trial_effort, target, gv, EEG_config, effort_state)
        # success
        if result == 'success':
            if action_type == 'approach':
                points = trial_actual_outcome
            elif action_type == 'avoid':
                points = 0
            hf.animate_success(win, spaceship, outcomes, target, outline, points, action_type, EEG_config, gv)
        # failure
        elif result == 'failure':
            if action_type == 'approach':
                points = 0
            elif action_type == 'avoid':
                points = trial_actual_outcome
            hf.animate_failure_or_reject(win, spaceship, outline, target, outcomes, points, action_type, result, EEG_config, gv)

    # reject
    elif clicked_button == lower_button:
        EEG_config.send_trigger(EEG_config.triggers['participant_choice_reject'])
        response = 'reject'
        result, effort_trace, average_effort, effort_time = None, None, None, None
        if action_type == 'approach':
            points = 0
        elif action_type == 'avoid':
            points = trial_actual_outcome
        hf.animate_failure_or_reject(win, spaceship, outline, target, outcomes, points, action_type, response, EEG_config, gv)

    # check if we are in a rating trial
    if rating_trial=="TRUE":
        if attention_focus == "reward":
            EEG_config.send_trigger(EEG_config.triggers['rating_question_reward'])
            rating = hf.get_rating(win, mouse, attention_focus)
            EEG_config.send_trigger(EEG_config.triggers['rating_response_reward'])
        elif attention_focus == "heart":
            EEG_config.send_trigger(EEG_config.triggers['rating_question_heart'])
            rating = hf.get_rating(win, mouse, attention_focus)
            EEG_config.send_trigger(EEG_config.triggers['rating_response_heart'])
    else:
        pass


    # save trial data
    info['trial_count'] += 1
    info['block_number'] = block_number
    info['block_action_type'] = action_type
    info['block_global_effort_state'] = effort_state
    info['block_attention_focus'] = attention_focus
    info['trial_rating'] = rating
    info['trial_effort'] = trial_effort
    info['trial_outcome_level'] = trial_outcome_level
    info['trial_actual_outcome'] = trial_actual_outcome
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


# End of experiment
big_txt.pos = [0, 200]
big_txt.text = "Well done! You have completed the experiment."
instructions_txt.text = "\n\n\n\n\n\nTrials x and x have been selected for your payout. You win £xx"
stimuli = [big_txt, instructions_txt]
hf.draw_all_stimuli(win, stimuli)
EEG_config.send_trigger(EEG_config.triggers['experiment_end'])
core.wait(10)

# CLOSE WINDOW
win.close()
core.quit()