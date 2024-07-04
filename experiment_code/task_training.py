"""
script for the training session (use the gripper labelled as LEFT)
will be automatically executed after gripper calibration

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
           'trial schedule': 'training',  # keep this to 'training' for the training task
           'grippers (y/n)': 'n', # if y, use real grippers, if n, use mouse movement
           'eeg (y/n)': 'n',  # should be 'n' for the training task!
           'session nr': '0',  # keep this to 0 for the training task!
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
    asummed_k = 1.1,  # assumed k value for effort shift calculation

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
win.mouseVisible = True

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
instructions_txt = visual.TextStim(win=win, text="Instructions", height=40, pos=[0, 100], wrapWidth=1000, color='white', font='Monospace')
instructions_top_txt = visual.TextStim(win=win, text="Instructions", height=40, pos=[0, 300], wrapWidth=1200, color='white', font='Monospace')
left_side_txt = visual.TextStim(win=win, text='Points', height=70, pos=(-300, 60), color='white', bold=True,font='Monospace')
upper_button = visual.Rect(win=win, units="pix", width=160, height=60, pos=(0, -250), fillColor='white')
upper_button_txt = visual.TextStim(win=win, text='ACCEPT', height=25, pos=upper_button.pos, color='black', bold=True,font='Monospace')
lower_button = visual.Rect(win=win, units="pix", width=160, height=60, pos=(0, -330), fillColor='white')
lower_button_txt = visual.TextStim(win=win, text='REJECT', height=25, pos=lower_button.pos, color='black', bold=True,font='Monospace')


###################################
# TRAINING SESSION INSTRUCTIONS
###################################
# Welcome
big_txt.text = "Welcome to the experiment!"
instructions_txt.text = "\n\n\n\n\nYou're about to begin a training session to familiarize yourself with the task. We'll guide you through each step.\n\nWhen you're ready to start, click 'NEXT'."
stimuli = [green_button, button_txt, big_txt, instructions_txt]
hf.draw_all_stimuli(win, stimuli)
hf.check_button(win, [green_button], stimuli, mouse)
EEG_config.send_trigger(EEG_config.triggers['training_start'])

# Introduce hand gripper
instructions_txt.text = ("In this experiment, you'll be using a hand gripper to exert effort.\n\n"
                         "The hand gripper is a small device that you'll squeeze with your dominant hand.\n\n"
                         "Before we begin, we need to calibrate the equipment to your individual strength.\n\n"
                         "Click 'NEXT' to proceed with the calibration.")
stimuli = [green_button, button_txt, instructions_txt]
hf.draw_all_stimuli(win, stimuli)
hf.check_button(win, [green_button], stimuli, mouse)

# Calibrate hand gripper
instructions_txt.text = ("For accurate calibration, please follow these steps:\n\n"
                         "1. Hold the gripper in your dominant hand.\n"
                         "2. When instructed, squeeze the gripper as hard as you can for 3 seconds.\n"
                         "3. Relax your hand when you see 'RELAX' on the screen.\n"
                         "4. We'll repeat this process 3 times to ensure accuracy.\n\n"
                         "Click 'NEXT' when you're ready to start the calibration.")
stimuli = [green_button, button_txt, instructions_txt]
hf.draw_all_stimuli(win, stimuli)
hf.check_button(win, [green_button], stimuli, mouse)

# CALIBRATE HAND GRIPPER (repeated 3 times)
for i in range(3):
    win.flip()
    instructions_top_txt.text = f"Calibration Round {i + 1} of 3"
    big_txt.text = "GET READY"
    hf.draw_all_stimuli(win, [instructions_top_txt, big_txt], 2)

    big_txt.text = "SQUEEZE!"
    hf.draw_all_stimuli(win, [instructions_top_txt, big_txt], 3)
    if not DUMMY:
        gv[f'max_force_{i + 1}'] = max(gripper.sample())

    big_txt.text = "RELAX"
    hf.draw_all_stimuli(win, [instructions_top_txt, big_txt], 2)

# Task overview
instructions_txt.text = ("Great job! Calibration is complete.\n\n"
                         "Now, let's learn about the task. In this experiment, you'll control a virtual spaceship.\n"
                         "Your goal is to fill the spaceship with fuel by exerting effort using the hand gripper.\n\n"
                         "The task consists of multiple trials, each presenting you with a choice.\n\n"
                         "Click 'NEXT' to learn about the different types of trials.")
stimuli = [green_button, button_txt, instructions_txt]
hf.draw_all_stimuli(win, stimuli, 1)
hf.check_button(win, [green_button], stimuli, mouse)

# Block types
instructions_txt.text = ("There are two types of trials in this task:\n\n"
                         "1. Approach Trials: You'll see a cloud of stars.\n"
                         "   - The number of stars represents the reward you can earn.\n"
                         "   - If you accept and successfully exert the required effort, you'll gain the reward.\n"
                         "   - If you reject or fail to exert enough effort, you'll get no reward.\n\n"
                         "2. Avoid Trials: You'll see a cloud of meteors.\n"
                         "   - The number of meteors represents a potential loss.\n"
                         "   - If you accept and successfully exert the required effort, you'll avoid the loss.\n"
                         "   - If you reject or fail to exert enough effort, you'll incur the loss.\n\n"
                         "Click 'NEXT' to continue.")
stimuli = [green_button, button_txt, instructions_txt]
hf.draw_all_stimuli(win, stimuli, 1)
hf.check_button(win, [green_button], stimuli, mouse)

# Trial structure
instructions_txt.text = ("Each trial follows this structure:\n\n"
                         "1. Offer: You'll see either stars (reward) or meteors (potential loss).\n"
                         "2. Decision: Choose to accept or reject the offer.\n"
                         "3. Effort: If accepted, squeeze the hand gripper to the required level.\n"
                         "4. Outcome: See whether you succeeded and your current score.\n\n"
                         "Click 'NEXT' to learn about the effort gauge.")
stimuli = [green_button, button_txt, instructions_txt]
hf.draw_all_stimuli(win, stimuli, 1)
hf.check_button(win, [green_button], stimuli, mouse)

# Effort gauge explanation
instructions_txt.text = ("During the effort phase, you'll see a vertical gauge on the screen:\n\n"
                         "- The gauge fills up as you squeeze the hand gripper.\n"
                         "- A horizontal line shows the required effort level.\n"
                         "- You must keep the gauge above this line for the entire duration.\n"
                         "- The duration is shown by a shrinking bar at the top of the screen.\n\n"
                         "Click 'NEXT' to continue.")
stimuli = [green_button, button_txt, instructions_txt]
hf.draw_all_stimuli(win, stimuli, 1)
hf.check_button(win, [green_button], stimuli, mouse)

# Monetary reward
instructions_txt.text = ("Your performance in this task translates to real money!\n\n"
                         "At the end of the experiment, we'll randomly select xx trials.\n"
                         "Your points from these trials will be converted into a monetary reward.\n\n"
                         "Each point is worth 1p. For example:\n"
                         "- If you have 100 points, you'll win £1\n"
                         "- If you have 500 points, you'll win £5\n\n"
                         "Click 'NEXT' to learn about the ratings.")
stimuli = [green_button, button_txt, instructions_txt]
hf.draw_all_stimuli(win, stimuli, 1)
hf.check_button(win, [green_button], stimuli, mouse)

# Ratings
instructions_txt.text = ("Throughout the experiment, we'll occasionally ask you about two things:\n\n"
                         "1. Your heart rate: How fast do you feel your heart is beating?\n"
                         "2. Your reward rate: How rewarding do you find the task at that moment?\n\n"
                         "When asked, consider your recent experiences compared to your overall average during the experiment.\n"
                         "You'll use a slider to indicate your response.\n\n"
                         "Click 'NEXT' to begin the training trials.")
stimuli = [green_button, button_txt, instructions_txt]
hf.draw_all_stimuli(win, stimuli, 1)
hf.check_button(win, [green_button], stimuli, mouse)

# Start training
big_txt.text = "Let's start the training!"
instructions_txt.text = ("You'll now complete a few practice trials to get familiar with the task.\n"
                         "Remember, this is just for practice. Ask questions if anything is unclear.\n\n"
                         "Good luck!")
stimuli = [big_txt, instructions_txt]
hf.draw_all_stimuli(win, stimuli, 5)


###################################
# TASK
###################################
current_block = 0
current_action_type = None
while info['trial_count'] < gv['num_trials']:  # this must be < because we start with trial_count = 0

    # pause for 1 second between trials
    win.flip()
    core.wait(1)

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
        button_txt.txt = 'START'
        win.flip()
        if action_type == 'approach':
            action_text = "collect stars to earn points"
        elif action_type == 'avoid':
            action_text = "evade meteors to avoid losing points"
        instructions_txt.text = (
            f"This is block {current_block} of {max(gv['block_number'])}."
            f"Your mission is to {action_text}.\n\n"
            f"Throughout this block, pay attention to your {attention_focus} rate.\n\n"
            "You may take a short break if needed. "
            "When you're ready to continue, click the 'START' button."
        )
        stimuli = [green_button, button_txt, instructions_txt]
        hf.draw_all_stimuli(win, stimuli, 1)
        hf.check_button(win, [green_button], stimuli, mouse)
        win.color = hf.convert_rgb_to_psychopy([0, 38, 82])  # set window color back to blue for trials
        button_txt.txt = 'NEXT'  # reset button text
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
            hf.animate_success(win, spaceship, outcomes, target, outline, points, action_type, EEG_config)
        # failure
        elif result == 'failure':
            if action_type == 'approach':
                points = 0
            elif action_type == 'avoid':
                points = trial_actual_outcome
            hf.animate_failure_or_reject(win, spaceship, outline, target, outcomes, points, action_type, result, EEG_config)

    # reject
    elif clicked_button == lower_button:
        EEG_config.send_trigger(EEG_config.triggers['participant_choice_reject'])
        response = 'reject'
        result, effort_trace, average_effort, effort_time = None, None, None, None
        if action_type == 'approach':
            points = 0
        elif action_type == 'avoid':
            points = trial_actual_outcome
        hf.animate_failure_or_reject(win, spaceship, outline, target, outcomes, points, action_type, result, EEG_config)

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
    print("rating: ", rating)


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
big_txt.text = "Well done! You have completed the training session."
stimuli = [big_txt, instructions_txt]
hf.draw_all_stimuli(win, stimuli)
EEG_config.send_trigger(EEG_config.triggers['experiment_end'])
core.wait(10)

# CLOSE WINDOW
win.close()
core.quit()


