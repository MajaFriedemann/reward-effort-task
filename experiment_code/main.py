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
import numpy as np
from psychopy import gui, visual, core, data, event
import helper_functions as hf
import random

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
    outcome_mean_magnitude_levels= [5, 7, 9],  # min cannot be below uncertain_point_difference
    outcome_uncertainty_levels = ['safe', '25/50/25', '50/50'],
    block_types = ['approach', 'avoid'],
    n_trials_per_block = 2,
    effort_duration = 1,  # second duration for which the effort needs to be exerted

    # visual parameters
    bar_pos_x = -400,  # x position of the effort bar
    bar_pos_y = 60,  # y position of the effort bar
    bar_height = 80,  # height of the effort bar
    effort_scaling_factor = 3,  # scaling factor for the width of the effort bar
    coin_pos_y = -110,  # y position of the coins
    coin_pos_x = 150,  # x position of the coins
    coin_distance_x = 90,  # distance between coin stacks
    coin_scaling_factor = 20,  # scaling factor for the height of the coins
    uncertain_point_difference = 4,  # value increase/decrease for uncertain offers
    avoid_block_colour = (145, 45, 11),  # RGB colour for avoid block
    approach_block_colour = (64, 83, 27),  # RGB colour for approach block
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
    fullscr=False,  # fullscreen mode
    screen=1,  # adjust if using multiple monitors
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
instructions_top_txt = visual.TextStim(win=win, text="Instructions", height=40, pos=[0, 300], wrapWidth=1200, color='white', font='Monospace')
left_side_txt = visual.TextStim(win=win, text='Points', height=70, pos=(-300, 60), color='white', bold=True,font='Monospace')
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


# # WELCOME
# stimuli = [green_button, button_txt, big_txt]
# hf.draw_all_stimuli(win, stimuli)
# hf.check_button(win, [green_button], stimuli, mouse) # show instructions until button is pressed


# # INSTRUCTIONS
# instructions_txt.text = ("Let's get ready to measure your grip strength! \n\n"
#                          "First up, we need to calibrate the equipment. So please do not touch the hand gripper yet. \n\n"
#                          "Click the 'NEXT' button to begin the calibration process.")
# stimuli = [green_button, button_txt, instructions_txt]
# hf.draw_all_stimuli(win, stimuli)
# hf.check_button(win, [green_button], stimuli, mouse) # show instructions until button is pressed
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
# hf.check_button(win, [green_button], stimuli, mouse) # show instructions until button is pressed


# TASK TRIALS
# generate trial schedule
trial_schedule = hf.generate_trial_schedule(gv['n_trials_per_combination'], gv['effort_levels'], gv['outcome_mean_magnitude_levels'], gv['outcome_uncertainty_levels'], gv['block_types'], gv['n_trials_per_block'])
last_block_type = None

# loop over the trials
for i, trial in trial_schedule.iterrows():
    response = None
    effort_trace = None
    average_effort = None
    result = None

    # break between blocks
    current_block_type = trial['block_type']
    if current_block_type != last_block_type:
        info['block_count'] += 1
        last_block_type = current_block_type
        win.color = 'black'
        stimuli = [instructions_txt, green_button, button_txt]
        hf.draw_all_stimuli(win, stimuli)
        hf.check_button(win, [green_button], stimuli, mouse)

    # present trial offer
    outlines, coin_stacks, bar_elements, heights = hf.trial_stimuli(win, trial['effort'], trial['mean_magnitude'], trial['uncertainty'], np.max(gv['outcome_mean_magnitude_levels']), trial['block_type'], gv)
    stimuli = [outlines, coin_stacks, bar_elements, upper_button, upper_button_txt, lower_button, lower_button_txt]
    hf.draw_all_stimuli(win, stimuli)
    clicked_button, response_time = hf.check_button(win, [upper_button, lower_button], stimuli, mouse)

    # if accepted, make the participant exert the effort
    if clicked_button == upper_button:
        response = 'accept'
        instructions_top_txt.text = "You accepted the offer. Squeeze the hand gripper to the required level for 1 second."
        stimuli = [instructions_top_txt, outlines, coin_stacks, bar_elements]
        result, effort_trace, average_effort = hf.sample_effort(win, DUMMY, mouse, gripper, 0, max_strength, trial['effort'], stimuli, gv)

        # approach block
        if current_block_type == 'approach':
            if result == 'success':
                instructions_top_txt.text = "Well done! You get points."
                selected_stack_index = random.randint(0, 3)  # randomly select one of the four stacks of coins
                selected_stack_height = heights[selected_stack_index] # get the number of coins of the selected stack
                selected_stack_outline = outlines[selected_stack_index]
                selected_stack_outline.lineColor = 'gold' # highlight the selected stack
                left_side_txt.text = '+'+ str(selected_stack_height) # show the number of coins of the selected stack
                stimuli = [coin_stacks, instructions_top_txt, selected_stack_outline, left_side_txt]
                hf.draw_all_stimuli(win, stimuli)
                core.wait(10)



            else:
                instructions_top_txt.text = "You did not reach the required effort. Minus points for you."

        # avoid block
        else:
            if result == 'success':
                instructions_top_txt.text = "Well done! You avoided the loss."
            else:
                instructions_top_txt.text = "You did not reach the required effort. Double minus points for you."




    # if rejected
    elif clicked_button == lower_button:
        response = 'reject'

        # approach block
        if current_block_type == 'approach':
            instructions_top_txt.text = "You rejected the offer. No points for you."

        # avoid block
        else:
            instructions_top_txt.text = "You rejected the offer. You get a loss."







    # save trial data
    info['trial_count'] += 1
    info['block_type'] = trial['block_type']
    info['outcome_mean_magnitude'] = trial['mean_magnitude']
    info['outcome_uncertainty'] = trial['uncertainty']
    info['effort_required'] = trial['effort']
    info['effort_trace'] = '"' + json.dumps(effort_trace) + '"'
    info['effort_expended'] = average_effort
    info['effort_response_time'] = None
    info['response'] = response
    info['response_time'] = response_time
    info['result'] = result
    info['points'] = None
    info['cumulative_points'] = None
    datafile.write(','.join([str(info[var]) for var in log_vars]) + '\n')
    datafile.flush()



# CLOSE WINDOW
win.close()
core.quit()