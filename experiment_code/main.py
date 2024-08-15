"""
script for the main task (use the gripper labelled as LEFT)
if using the hand-gripper (rather than DUMMY version), run gripper_calibration.py once before this (only before the first session)
if trial schedule is set to 'training', the participant is in the training session
to determine the participant's max grip strength
with 'strength' I refer to raw grip strength
with 'effort' I refer to grip strength relative to the participant's max strength (as determined with gripper_calibration.py)

Maja Friedemann 2024
"""

###################################
# IMPORT PACKAGES
###################################
import csv
import json
import os
import random
from datetime import datetime
import time
from psychopy import gui, visual, core, data, event
import helper_functions as hf
import ctypes

print('Reminder: Press Q to quit.')

###################################
# SESSION INFO
###################################
# PARTICIPANT INFO POP-UP
expName = 'reward-effort-pgACC-TUS'
curecID = 'R88533/RE002'
expInfo = {'participant nr': '7',
           'trial schedule': 'B_5',  # schedule A or B, 1-8 (e.g. A_1), 'testing' for testing, 'training' for training session
           'grippers (y/n)': 'y',  # if y, use real grippers, if n, use mouse movement
           'eeg (y/n)': 'n',  # if y, send EEG triggers, if n, just print them
           'session nr': '1',  # 0 for training session, then 1, 2, 3
           'age': '',
           'gender (f/m/o)': '',
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
max_strength = 0.9 * max_strength  # MAJA

# TASK VARIABLES
gv = dict(
    # task parameters
    response_keys=['j', 'k'],  # keys for accept / reject responses and slider movement
    max_strength=max_strength,
    gripper_zero_baseline=None,
    effort_duration=1,  # second duration for which the effort needs to be above threshold 1
    time_limit=5,  # time limit for exerting the effort 5
    outcome_presentation_time=1.5,  # time for which the outcome is presented
    effort_started_threshold=0.1,  # threshold to consider effort exertion started for EEG trigger
    net_value_shift=30,  # shift in net value for shifted effort state
    assumed_k=1.1,  # assumed k value for effort shift calculation
    training=False,  # training session
    base_bonus_payment=8,  # base bonus payment in pounds

    # trial schedule
    num_trials=None,
    num_trials_per_block=None,
    block_number=[],
    outcome_level=[],
    actual_outcome=[],
    effort=[],
    action_type=[],
    attention_focus=[],
    rating_trial=[],
    effort_state=[],

    # visual parameters
    effort_bar_width=65,
    effort_bar_height=138,
)

# READ TRIAL SCHEDULE
trial_schedule_key = expInfo['trial schedule']
trial_schedule_filepath = f'../final_trial_schedules/schedule_{trial_schedule_key}.csv'
if os.path.exists(trial_schedule_filepath):
    max_trial_number = 0
    max_block_trial_number = 0
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
            max_block_trial_number = max(max_block_trial_number, int(row['trial_in_block']))
    gv['num_trials'] = max_trial_number
    gv['num_trials_per_block'] = max_block_trial_number
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
# initialize an empty list to accumulate trial data
all_trials = []
# variables in info will be saved as participant data
info = dict(
    expName=expName,
    curec_ID=curecID,
    trial_schedule=expInfo['trial schedule'],
    session_nr=expInfo['session nr'],
    date=data.getDateStr(),
    start_time=None,
    end_time=None,
    duration=None,

    participant=expInfo['participant nr'],
    age=expInfo['age'],
    gender=expInfo['gender (f/m/o)'],
    max_strength=max_strength,  # from calibration data

    block_number=0,  # block counter
    trial_count=0,  # trial counter
    block_action_type=None,  # approach or avoid
    block_global_effort_state=None,  # low or high
    block_attention_focus=None,  # reward rate or heart rate
    trial_rating=None,  # heart or reward rate rating
    trial_rating_time=None,  # time taken to rate
    trial_rating_random_start_pos=None,  # random start position of the rating slider
    trial_effort=None,  # effort level required in the trial
    trial_outcome_level=None,  # offered reward/loss
    trial_actual_outcome=None,

    response=None,  # accept or reject
    response_time=None,  # time taken to accept or reject
    result=None,  # did participant manage to exert the required effort
    points=None,  # points won or lost in the trial
    cumulative_points=None,  # points across trials

    effort_trace='',
    effort_expended=None,  # average effort expended on trial during the 1 second where effort is above the threshold
    effort_response_time=None,

    final_bonus_payment=None
)

# start a csv file for saving the participant data
log_vars = list(info.keys())
folder = 'training_data' if gv.get('training') else 'data'
if not os.path.exists(folder):
    os.mkdir(folder)
filename = os.path.join(folder, '%s_%s_%s' % (info['participant'], info['session_nr'], info['date']))
datafile = open(filename + '.csv', 'w')
datafile.write(','.join(log_vars) + '\n')
datafile.flush()

##################################################
# SET UP WINDOW, MOUSE, HAND GRIPPER, EEG TRIGGERS
##################################################
# WINDOW
win = visual.Window(
    size=[1512, 982],  # set to actual screen size
    fullscr=True,  # full-screen mode
    screen=1,
    allowGUI=True,
    color='black',
    blendMode='avg',
    useFBO=True,  # Frame Buffer Object for rendering (good for complex stimuli)
    units='pix'
    # units in pixels (fine for this task but for more complex (e.g. dot motion) stimuli, we probably need visual degrees
)

# MOUSE
win.setMouseVisible(False)
mouse = event.Mouse(visible=False, win=win)
mouse.setVisible(False)
# Explicitly hide the cursor on Windows
if os.name == 'nt':  # Check if the OS is Windows
    ctypes.windll.user32.ShowCursor(False)

# HAND GRIPPER
DUMMY = expInfo['grippers (y/n)'].lower() == 'n'
gripper = None
if not DUMMY:
    from mpydev import BioPac

    gripper = BioPac("MP160", n_channels=1, samplerate=200, logfile="test", overwrite=True)
    gripper.start_recording()

# EEG TRIGGERS
triggers = dict(
    experiment_start=1,
    block_start=2,
    effort_presentation_approach=3,
    effort_presentation_avoid=4,
    outcome_presentation_approach=5,
    outcome_presentation_avoid=6,
    participant_choice_accept=7,
    participant_choice_reject=8,
    rating_question_reward=9,
    rating_question_heart=10,
    rating_response_reward=11,
    rating_response_heart=12,
    effort_started=13,
    effort_threshold_crossed=14,
    effort_success=15,
    outcome_presentation_approach_success=16,
    outcome_presentation_approach_failure=17,
    outcome_presentation_approach_reject=18,
    outcome_presentation_avoid_success=19,
    outcome_presentation_avoid_failure=20,
    outcome_presentation_avoid_reject=21,
    experiment_end=22
)
# Create an EEGConfig object
send_triggers = expInfo['eeg (y/n)'].lower() == 'y'
EEG_config = hf.EEGConfig(triggers, send_triggers)

###################################
# CREATE STIMULI
###################################
green_button = visual.Rect(win=win, units="pix", width=160, height=80, pos=(0, -300), fillColor='green')
button_txt = visual.TextStim(win=win, text='NEXT', height=30, pos=green_button.pos, color='black', bold=True,
                             font='Arial')
big_txt = visual.TextStim(win=win, text='Welcome!', height=80, pos=[20, 160], color='white', wrapWidth=1100,
                          font='Arial')
instructions_txt = visual.TextStim(win=win, text="Instructions", height=40, pos=[0, 60], wrapWidth=1300, color='white',
                                   font='Arial')
instructions_top_txt = visual.TextStim(win=win, text="Instructions", height=40, pos=[0, 270], wrapWidth=1200,
                                       color='white', font='Arial')
left_side_txt = visual.TextStim(win=win, text='Points', height=70, pos=(-300, 60), color='white', bold=True,
                                font='Arial')
upper_button = visual.Rect(win=win, units="pix", width=160, height=60, pos=(0, -250), fillColor='white')
upper_button_txt = visual.TextStim(win=win, text='ACCEPT', height=25, pos=upper_button.pos, color='black', bold=True,
                                   font='Arial')
lower_button = visual.Rect(win=win, units="pix", width=160, height=60, pos=(0, -330), fillColor='white')
lower_button_txt = visual.TextStim(win=win, text='REJECT', height=25, pos=lower_button.pos, color='black', bold=True,
                                   font='Arial')
heart_rate_stimulus = visual.ImageStim(win, image="pictures/heart.png", pos=(260, 244), size=(65, 65))
reward_rate_stimulus = visual.ImageStim(win, image="pictures/money.png", pos=(280, 180), size=(65, 65))
heart_cue = visual.ImageStim(win, image="pictures/heart.png", pos=(0, 0), size=(70, 70))
reward_cue = visual.ImageStim(win, image="pictures/money.png", pos=heart_cue.pos, size=(70, 70))
accept_txt = visual.TextStim(win=win, text='A', height=30, pos=(-35, -300), color='white', bold=True, font='Arial')
oval_accept = visual.Circle(win=win, radius=24, pos=accept_txt.pos, edges=180, lineColor='white', lineWidth=2, fillColor=None)
reject_txt = visual.TextStim(win=win, text='R', height=30, pos=(35, -300), color='white', bold=True, font='Arial')
oval_reject = visual.Circle(win=win, radius=24, pos=reject_txt.pos, edges=180, lineColor='white', lineWidth=2, fillColor=None)
fixation_cross = visual.TextStim(win, text='+', height=60, color='white')

###################################
# INSTRUCTIONS
###################################
# Welcome
big_txt.text = "Welcome!"
if gv['training']:
    instructions_txt.text = (
        "\n\n\n\nIn this training session, you will learn about the task \nand do a few practice trials!\n\n "
        "When you're ready, press SPACE."
    )
else:
    instructions_txt.text = (
        "\n\n\n\nPrepare to embark on your space adventure!\n\n "
        "When you're ready, press SPACE."
    )
big_txt.draw()
instructions_txt.draw()
win.flip()
event.waitKeys(keyList=['space'])  # show instructions until space is pressed
hf.exit_q(win)
event.clearEvents()

# Calibrate hand gripper
if gv['training']:
    instructions_txt.text = (
        "In this task, you will use a hand gripper to power a spaceship.\n\n"
        "Before starting your training, we must recalibrate this equipment. "
        "Therefore, please keep your hands clear of the hand gripper for now.\n\n"
        "Press SPACE to begin the calibration process."
    )
else:
    instructions_txt.text = (
        "As you'll remember, your primary control interface is the hand gripper which powers your ship's engines.\n\n"
        "Before you start, we must recalibrate this equipment. "
        "Therefore, please keep your hands clear of the hand gripper for now.\n\n"
        "Press SPACE to begin the calibration process."
    )
instructions_txt.draw()
win.flip()
event.waitKeys(keyList=['space'])  # show instructions until space is pressed
hf.exit_q(win)
event.clearEvents()

# CALIBRATE HAND GRIPPER ZERO BASELINE
win.flip()
instructions_top_txt.text = (
    "Calibration in progress.\n\n"
    "Please keep your hands away from the hand gripper."
)
hf.draw_all_stimuli(win, [instructions_top_txt], 1)
big_txt.pos = [0, 20]
for countdown in range(3, 0, -1):
    big_txt.text = f"{countdown}"
    hf.draw_all_stimuli(win, [instructions_top_txt, big_txt], 1)
    if not DUMMY and countdown == 1:
        gv['gripper_zero_baseline'] = gripper.sample()[0]
win.flip()
core.wait(0.6)

# Task overview
instructions_txt.text = (
    "Excellent! Calibration is complete.\n\n"
    "In this task, you'll pilot a spaceship through the cosmos, encountering star clouds and meteor fields. "
    "Each encounter will require you to make a decision and potentially exert effort.\n\n"
    "Press SPACE to review the key elements of the task."
)
instructions_txt.draw()
win.flip()
event.waitKeys(keyList=['space'])
hf.exit_q(win)
event.clearEvents()

# Trial Structure
instructions_txt.text = (
    "Each trial consists of the following steps:\n\n"
    "1. Spaceship & Effort Bar: A spaceship appears with an effort bar, indicating the amount of effort required for the trial.\n"
    "2. Fixation Cross: A brief fixation cross is shown on the screen.\n"
    f"3. Encounter: You'll face either a star cloud (potential win) or a meteor field (potential loss).\n"
    f"4. Decision: A second fixation cross appears, signaling you to make a choice. Press the designated response keys to accept or reject an encounter.\n"
    f"5. Outcome: If you accept, you'll need to exert the required effort to either approach the stars or avoid the meteors. "
    "Rejecting the encounter means no effort is required, but you forgo the chance to win a reward or avoid a loss. After your choice, the outcome is displayed, and the next trial begins."
    "\n\nPress SPACE to continue."
)
instructions_txt.draw()
win.flip()
event.waitKeys(keyList=['space'])
hf.exit_q(win)
event.clearEvents()

# Block types
instructions_txt.text = (
    "There are two types of encounters:\n\n"
    "1. In approach encounters, you'll face clouds of stars. More stars mean higher potential rewards. "
    "If you choose to accept the encounter, it becomes a mission where you must exert effort to approach the stars and collect the reward. "
    "Rejecting the encounter or failing to exert the required effort during the mission results in no reward.\n\n"
    "2. In avoid encounters, you'll face meteor fields. More meteors indicate a greater potential loss. "
    "If you accept the encounter, it becomes a mission where you must exert effort to avoid the meteors and evade the loss. "
    "Rejecting the encounter or failing to exert the required effort during the mission results in a loss."
    "\n\nPress SPACE to continue."
)
instructions_txt.draw()
win.flip()
event.waitKeys(keyList=['space'])  # show instructions until space is pressed
hf.exit_q(win)
event.clearEvents()

# Effort
instructions_txt.text = (
    f"When you accept an encounter, squeeze the gripper to power your spaceship. "
    f"Your goal is to reach the target power level as quickly as possible. "
    f"Once at target, maintain the power for 1 second until your spaceship starts moving. "
    f"You have {gv['time_limit']} seconds for each mission attempt. Therefore, starting too slow may result in mission failure.\n\n"
    f"Your adventure consists of {max(gv['block_number'])} blocks, each with {gv['num_trials_per_block']} encounters.\n"
    f"Choose which encounters to accept wisely to not run out of energy whilst maximising your rewards and minimising your losses!"
    f"\n\nPress SPACE to continue."
)
instructions_txt.draw()
win.flip()
event.waitKeys(keyList=['space'])  # show instructions until space is pressed
hf.exit_q(win)
event.clearEvents()

# Monetary reward
instructions_txt.text = (
    f"You start your adventure with a base reward of £{gv['base_bonus_payment']}.\n"
    "At the end, we'll randomly select 10 encounters (5 star clouds and 5 meteor fields). "
    "Your choices and performance in these encounters will adjust your final reward.\n\n"
    "Each point is worth 1p. For example, if an encounter where you accepted the mission and collected an 80-point star cloud is chosen, you'll earn 80p. "
    "However, if you rejected that encounter or failed the mission, you'll earn nothing. "
    "Similarly, if an encounter where you accepted the mission and successfully evaded an 80-point meteor field is chosen, nothing will be subtracted from your base reward. "
    "But if you rejected that encounter or failed the mission, you'll lose 80p."
    "\n\nPress SPACE to continue."
)
instructions_txt.draw()
win.flip()
event.waitKeys(keyList=['space'])  # show instructions until space is pressed
hf.exit_q(win)
event.clearEvents()

# Ratings
instructions_txt.text = (
    "Throughout your adventure, you'll occasionally report on two metrics:\n\n"
    "\n\n\n\n"
    "Consider your recent experiences relative to your overall adventure.\n\n"
    "To report these metrics, use the response keys (the same ones you use for accept/reject) to move the slider marker left or right and "
    "confirm your selection by pressing the SPACE key. "
    "Note that the slider marker will always start out at a random position."
    "\n\nPress SPACE to continue."
)
heart_rate_text = visual.TextStim(win, text="• Your current heart rate\n\n\n\n\n\n\n\n", pos=instructions_txt.pos,
                                  height=instructions_txt.height)
reward_rate_text = visual.TextStim(win, text="\n• Your current reward rate\n\n\n\n\n\n", pos=instructions_txt.pos,
                                   height=instructions_txt.height)
stimuli = [instructions_txt, heart_rate_text, reward_rate_text, heart_rate_stimulus,
           reward_rate_stimulus]
hf.draw_all_stimuli(win, stimuli)
event.waitKeys(keyList=['space'])  # show instructions until space is pressed
event.clearEvents()

instructions_txt.text = (
    "You'll see an icon flashing at the beginning of each trial, reminding you which metric (reward or heart rate) you are currently tracking.\n\n"
    "In avoid blocks, even though you are losing points, you should still use the complete scale from low to high "
    "reward rate. Consider your reward rate in the current context: if the loss is comparatively small, you may still have a high reward rate in that instance."
    "\n\nPress SPACE to continue."
)
instructions_txt.draw()
win.flip()
event.waitKeys(keyList=['space'])  # show instructions until space is pressed
hf.exit_q(win)
event.clearEvents()

# Training quiz
if gv['training']:
    instructions_top_txt.pos = [0, 200]
    big_txt.pos = [0, 150]
    instructions_txt.text = (
        "Let's make sure you're ready! \n\nAnswer the following questions \nto show you know how the task works."
        "\n\n Respond with the number of the correct answer (1, 2, or 3). \n\n\n\nPress SPACE to start."
    )
    instructions_txt.draw()
    win.flip()
    hf.exit_q(win)
    event.waitKeys(keyList=['space'])  # show instructions until space is pressed
    event.clearEvents()

    button_1 = visual.Rect(win=win, units="pix", width=500, height=60, pos=(0, 100), fillColor='white')
    button_1_txt = visual.TextStim(win=win, text='Option A', height=25, pos=button_1.pos, color='black', bold=True,
                                   font='Arial')
    button_2 = visual.Rect(win=win, units="pix", width=500, height=60, pos=(0, 0), fillColor='white')
    button_2_txt = visual.TextStim(win=win, text='Option B', height=25, pos=button_2.pos, color='black', bold=True,
                                   font='Arial')
    button_3 = visual.Rect(win=win, units="pix", width=500, height=60, pos=(0, -100), fillColor='white')
    button_3_txt = visual.TextStim(win=win, text='Option C', height=25, pos=button_3.pos, color='black', bold=True,
                                   font='Arial')

    quiz_questions = [
        ("How do you power your spaceship?", ["1. Squeeze the gripper", "2. Press a button", "3. Shout"], 0),
        ("What do you do in an approach encounter?", ["1. Avoid meteors", "2. Approach stars", "3. Do nothing"], 1),
        ("What happens if you reject an avoid encounter?", ["1. Gain a reward", "2. No change", "3. Experience a loss"], 2),
        ("What do more meteors indicate?", ["1. Higher potential reward", "2. Greater potential loss", "3. Easier mission"], 1),
        ("What happens if you fail to exert the required effort during an approach encounter?", ["1. No reward is given", "2. You still get a reward", "3. You lose points"], 0)
    ]
    incorrect_questions = []

    def ask_question(question, options, correct_option):
        instructions_top_txt.text = question
        button_1_txt.text = options[0]
        button_2_txt.text = options[1]
        button_3_txt.text = options[2]
        stimuli = [instructions_top_txt, button_1, button_1_txt, button_2, button_2_txt, button_3, button_3_txt]
        hf.draw_all_stimuli(win, stimuli)

        keys = event.waitKeys(keyList=['1', '2', '3'])
        response = keys[0]
        if response == '1':
            selected_option = 0
        elif response == '2':
            selected_option = 1
        elif response == '3':
            selected_option = 2

        if selected_option == correct_option:
            big_txt.text = "Correct!"
            instructions_txt.text = "\n\n\n\n\n\nPress SPACE to continue."
        else:
            big_txt.text = f"Incorrect!"
            instructions_txt.text = f"\n\n\n\n\n\n\nThe question was: '{question}'\n\nThe correct answer is: '{options[correct_option]}'. \n\n\nPress SPACE to continue."
            incorrect_questions.append((question, options, correct_option))

        stimuli = [big_txt, instructions_txt]
        hf.draw_all_stimuli(win, stimuli)
        event.waitKeys(keyList=['space'])
        hf.exit_q(win)
        event.clearEvents()

    # Ask all initial questions
    for question, options, correct_option in quiz_questions:
        ask_question(question, options, correct_option)
    # Re-ask incorrect questions
    while incorrect_questions:
        question, options, correct_option = incorrect_questions.pop(0)
        ask_question(question, options, correct_option)

# Start
win.flip()
if gv['training']:
    instructions_txt.text = (
        "Great job!\n\nLet's dive into some practice trials!\n\nThe points from this training session won't count towards your monetary reward, so feel free to explore: "
        "Try out accepting or rejecting offers, and see what happens when you successfully execute or fail to meet the required effort levels."
        "\n\nPress SPACE to start."
    )
else:
    big_txt.text = "Grab the hand gripper to prepare for launch!\n"
    instructions_txt.text = ("\n\n\n\n\n\n\n\n\n\n\nPress SPACE when ready.")
    big_txt.draw()
instructions_txt.draw()
win.flip()
event.waitKeys(keyList=['space'])
hf.exit_q(win)
event.clearEvents()

# MAJA - some break point here so that the actual task only starts after TUS has been completed

###################################
# TASK
###################################
EEG_config.send_trigger(EEG_config.triggers['experiment_start'])
start_time = datetime.now()
info['start_time'] = start_time.strftime("%Y-%m-%d %H:%M:%S")
current_block = 0
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
    rating_time = None
    rating_random_start_pos = None
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
    # rating_trial = "True"
    # action_type = 'approach'
    # attention_focus = 'heart'

    # set trial effort to a constant and then alternate between 'shifted' and 'normal' to test this is working
    # trial_effort = 90
    # if info['trial_count'] % 2 == 0:
    #     effort_state = 'shifted'
    # else:
    #     effort_state = 'normal'
    ##########################################################################################
    ##########################################################################################

    # check if we are at the beginning of a new block
    if block_number != current_block:
        EEG_config.send_trigger(EEG_config.triggers['block_start'])
        current_block = block_number
        win.color = 'black'  # set window color to black for block message
        button_txt.text = 'START'
        win.flip()
        if action_type == 'approach':
            action_text = "collect stars to earn points"
            outcome = hf.draw_star(win, [450, 115], size=25, color=[255, 255, 255])
        elif action_type == 'avoid':
            action_text = "evade meteors to avoid losing points"
            outcome = hf.draw_meteor(win, [540, 115], size=24, color=[255, 255, 255])
        if attention_focus == 'reward':
            reward_rate_stimulus.pos = [550, 25]
            image = reward_rate_stimulus
            cue = reward_cue
        elif attention_focus == 'heart':
            heart_rate_stimulus.pos = [530, 25]
            image = heart_rate_stimulus
            cue = heart_cue
        instructions_txt.text = (
            f"This is block {current_block} of {max(gv['block_number'])}\n\n"
            f"Your mission is to {action_text}\n\n"
            f"Throughout this block, pay attention to your {attention_focus} rate\n\n"
            "When you're ready to continue, press SPACE!"
        )
        stimuli = [instructions_txt, image, outcome]
        hf.draw_all_stimuli(win, stimuli, 1)
        event.waitKeys(keyList=['space'])  # show instructions until space is pressed
        event.clearEvents()
        win.color = hf.convert_rgb_to_psychopy([0, 38, 82])  # set window color back to blue for trials
        win.flip()
    else:
        pass

    # draw stimuli
    spaceship, outline, target, effort_text, outcomes = hf.draw_trial_stimuli(win, trial_effort, trial_outcome_level,
                                                                              action_type, gv)
    # shift stimuli to the center of the screen
    shift = abs(outline.pos[1])
    spaceship.pos = (spaceship.pos[0], spaceship.pos[1] + shift)
    outline.pos = (outline.pos[0], outline.pos[1] + shift)
    target.pos = (target.pos[0], target.pos[1] + shift)
    for outcome in outcomes:
        outcome.pos = (outcome.pos[0], outcome.pos[1] - 220)

    # sequentially show effort and then outcome offer
    hf.draw_all_stimuli(win, [cue], 0.5)
    if action_type == 'approach':
        EEG_config.send_trigger(EEG_config.triggers['effort_presentation_approach'])
    elif action_type == 'avoid':
        EEG_config.send_trigger(EEG_config.triggers['effort_presentation_avoid'])
    hf.draw_all_stimuli(win, [spaceship, outline, target], 1)
    hf.draw_all_stimuli(win, [fixation_cross], 0.5)
    if action_type == 'approach':
        EEG_config.send_trigger(EEG_config.triggers['outcome_presentation_approach'])
    elif action_type == 'avoid':
        EEG_config.send_trigger(EEG_config.triggers['outcome_presentation_avoid'])
    hf.draw_all_stimuli(win, [outcomes], 1)
    hf.draw_all_stimuli(win, [fixation_cross], 0.5)

    # shift back to original position
    spaceship.pos = (spaceship.pos[0], spaceship.pos[1] - shift)
    outline.pos = (outline.pos[0], outline.pos[1] - shift)
    target.pos = (target.pos[0], target.pos[1] - shift)
    for outcome in outcomes:
        outcome.pos = (outcome.pos[0], outcome.pos[1] + 220)

    clicked_button, response_time = hf.check_key_press(win, gv['response_keys'])

    # accept
    if clicked_button == gv['response_keys'][0]:
        EEG_config.send_trigger(EEG_config.triggers['participant_choice_accept'])
        response = 'accept'
        stimuli = [spaceship, outline, target, outcomes]
        result, effort_trace, average_effort, effort_time = hf.sample_effort(win, DUMMY, mouse, gripper, stimuli,
                                                                             trial_effort, target, gv, EEG_config,
                                                                             effort_state)
        # success
        if result == 'success':
            if action_type == 'approach':
                points = trial_actual_outcome
            elif action_type == 'avoid':
                points = 0
            hf.animate_success(win, spaceship, outcomes, target, outline, points, action_type, EEG_config, gv, cue)
        # failure
        elif result == 'failure':
            if action_type == 'approach':
                points = 0
            elif action_type == 'avoid':
                points = trial_actual_outcome
            hf.animate_failure_or_reject(win, spaceship, outline, target, outcomes, points, action_type, result,
                                         EEG_config, gv, cue)

    # reject
    # elif clicked_button == lower_button:  # with accept / reject buttons
    elif clicked_button == gv['response_keys'][1]:
        EEG_config.send_trigger(EEG_config.triggers['participant_choice_reject'])
        response = 'reject'
        result, effort_trace, average_effort, effort_time = None, None, None, None
        if action_type == 'approach':
            points = 0
        elif action_type == 'avoid':
            points = trial_actual_outcome
        hf.animate_failure_or_reject(win, spaceship, outline, target, outcomes, points, action_type, response,
                                     EEG_config, gv, cue)

    # check if we are in a rating trial
    if rating_trial == "True":
        if attention_focus == "reward":
            EEG_config.send_trigger(EEG_config.triggers['rating_question_reward'])
            rating, rating_time, rating_random_start_pos = hf.get_rating(win, attention_focus, reward_rate_stimulus, gv)
            EEG_config.send_trigger(EEG_config.triggers['rating_response_reward'])
        elif attention_focus == "heart":
            EEG_config.send_trigger(EEG_config.triggers['rating_question_heart'])
            rating, rating_time, rating_random_start_pos = hf.get_rating(win, attention_focus, heart_rate_stimulus, gv)
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
    info['trial_rating_time'] = rating_time
    info['trial_rating_random_start_pos'] = rating_random_start_pos
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
    # append a copy of the current trial info to the all_trials list
    all_trials.append(info.copy())

# End of experiment
end_time = datetime.now()
info['end_time'] = end_time.strftime("%Y-%m-%d %H:%M:%S")
duration = end_time - start_time
info['duration'] = str(duration)

big_txt.pos = [0, 200]
if gv['training']:
    big_txt.text = "\n\nWell done! \n\nYou have completed the training session."
    instructions_txt.text = " "
else:
    final_bonus_payment = hf.calculate_bonus_payment(all_trials, gv)
    info['final_bonus_payment'] = final_bonus_payment
    print(f"Final bonus payment: £{final_bonus_payment: .2f}")
    big_txt.text = "Well done! You have completed the task."
    instructions_txt.text = f"\n\n\n\n\n\nYour bonus payment is £{final_bonus_payment: .2f}!"

# Update the last trial with end time, duration, and bonus payment
if all_trials:
    all_trials[-1]['end_time'] = info['end_time']
    all_trials[-1]['duration'] = info['duration']
    all_trials[-1]['final_bonus_payment'] = info['final_bonus_payment']

    # Close the file before reopening it in read/write mode
    datafile.close()

    # Reopen the file in read/write mode
    with open(filename + '.csv', 'r+') as datafile:
        # Read the current content of the file
        lines = datafile.readlines()

        # Replace the last line with the updated trial info
        lines[-1] = ','.join([str(all_trials[-1][var]) for var in log_vars]) + '\n'

        # Write back the modified content
        datafile.seek(0)
        datafile.writelines(lines)
        datafile.flush()

datafile.close()
stimuli = [big_txt, instructions_txt]
hf.draw_all_stimuli(win, stimuli)
EEG_config.send_trigger(EEG_config.triggers['experiment_end'])
hf.exit_q(win, mouse)
core.wait(8)

# CLOSE WINDOW
win.close()
core.quit()
