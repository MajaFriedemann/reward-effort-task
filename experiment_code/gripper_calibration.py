"""
script for calibrating the hand gripper (gripper labeled as LEFT)
will automatically start the training session after calibration is done
needs to be run before main.py
for the pgACC TUS study probably best to do this on the structural scan day alongside the training session and calibrating the dot motion stimulus for the confidence task?

Maja Friedemann 2024
"""

###################################
# IMPORT PACKAGES
###################################
import os
import json
from psychopy import gui, visual, core, data, event
import helper_functions as hf

print('Reminder: Press Q to quit.')


###################################
# SESSION INFO & DATA SAVING
###################################
expName = 'reward-strength-pgACC-TUS_calibration'
curecID = 'R88533/RE002'
expInfo = {'participant nr': '2',
           'grippers (y/n)': 'y',  # if y, use real grippers, if n, use mouse movement
           }
dlg = gui.DlgFromDict(dictionary=expInfo, sortKeys=False, title=expName)  # pop-up window asking for participant number and which hand they will use for the gripper (they need to be happy to use the respective other hand for the keyboard)
if not dlg.OK:
    core.quit()  # pressed cancel on the pop-up window

# variables in info will be saved as participant data
info = dict(
    expName=expName,
    curec_ID=curecID,
    date=data.getDateStr(),
    participant=expInfo['participant nr'],

    # following variables are all corrected for the gripper 0 baseline
    strength_trace_1='', # strength trace for calibration trial 1
    max_strength_1=0.0, # average strength in a half-second window around the peak strength for calibration trial 1
    strength_trace_2='', # strength trace for calibration trial 2
    max_strength_2=0.0, # average strength in a half-second window around the peak strength for calibration trial 2
    strength_trace_3='', # strength trace for calibration trial 3
    max_strength_3=0.0, # average strength in a half-second window around the peak strength for calibration trial 3
    max_strength=0.0,  # average of max_strength_calibration_2 and max_strength_calibration_3
)

# start a csv file for saving the participant data
log_vars = list(info.keys())
if not os.path.exists('calibration_data'):
    os.mkdir('calibration_data')
filename = os.path.join('calibration_data', '%s_%s' % (info['participant'], info['date']))
datafile = open(filename + '.csv', 'w')
datafile.write(','.join(log_vars) + '\n')
datafile.flush()


###################################
# HAND GRIPPER
###################################
DUMMY = expInfo['grippers (y/n)'].lower() == 'n'
gripper = None
if not DUMMY:
    from mpydev import BioPac
    gripper = BioPac("MP160", n_channels=1, samplerate=200, logfile="test", overwrite=True)
    gripper.start_recording()


###################################
# SET UP WINDOW
###################################
win = visual.Window(
    size=[1920, 1080],  # set correct monitor size
    fullscr=True,  # fullscreen mode
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
green_button = visual.Rect(win=win, units="pix", width=160, height=80, pos=(0, -280), fillColor='green')
button_txt = visual.TextStim(win=win, text='NEXT', height=28, pos=green_button.pos, color='black', bold=True,font='Arial')
big_txt = visual.TextStim(win=win, text='Welcome to the \ngrip strength test!', height=90, pos=[0, 40], color='white', wrapWidth=800, font='Arial')
instructions_txt = visual.TextStim(win=win, text="Instructions", height=40, pos=[0, 80], wrapWidth=900, color='white', font='Arial')
instructions_top_txt = visual.TextStim(win=win, text="Instructions", height=40, pos=[0, 220], wrapWidth=1200, color='white', font='Arial')

graph_start_x = -300
graph_length = 600
graph_start_y = -280
graph_height = 400
horizontal_graph_line = visual.Line(win, start=(graph_start_x, graph_start_y), end=(graph_start_x + graph_length, graph_start_y), lineWidth=2, lineColor='white')
vertical_graph_line = visual.Line(win, start=(graph_start_x, graph_start_y), end=(graph_start_x, graph_start_y + graph_height), lineWidth=2, lineColor='white')


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
hf.check_button(win, [green_button], stimuli, mouse) # show instructions until button is pressed


# INSTRUCTIONS
instructions_txt.text = ("Let's get ready to measure your grip strength! \n\n"
                         "First up, we need to calibrate the equipment. So please do not touch the hand gripper yet. \n\n"
                         "Click the 'NEXT' button to begin the calibration process.")
stimuli = [green_button, button_txt, instructions_txt]
hf.draw_all_stimuli(win, stimuli)
hf.check_button(win, [green_button], stimuli, mouse) # show instructions until button is pressed


# CALIBRATE HAND GRIPPER ZERO BASELINE
instructions_top_txt.text = "Calibration in progress. Do not touch the hand gripper."
hf.draw_all_stimuli(win, [instructions_top_txt], 1)
gripper_zero_baseline = graph_start_y  # set the gripper zero baseline to the bottom of the graph if we are in dummy mode
for countdown in range(3, 0, -1):
    big_txt.text = str(countdown)
    hf.draw_all_stimuli(win, [instructions_top_txt, big_txt], 1) # display a 3, 2, 1 countdown
    if not DUMMY and countdown == 3:
        gripper_zero_baseline = gripper.sample()[0]  # on 1, sample the gripper 0 baseline
win.flip()
core.wait(1)


# INSTRUCTIONS
instructions_txt.text = ("Great! Calibration is done. \n\n"
                         "Now, please pick up the hand gripper with the hand you're not using for the mouse. Make sure you have a comfortable yet firm grip. \n\n"
                         "There will be 3 trials. When you feel ready to show us how strong your grip is, press 'NEXT' to begin.")
stimuli = [green_button, button_txt, instructions_txt]
hf.draw_all_stimuli(win, stimuli, 1)
hf.check_button(win, [green_button], stimuli, mouse) # show instructions until button is pressed


# CALIBRATE PARTICIPANT MAX GRIP STRENGTH
strength_samples = []  # list to store strength values
times = []  # list to store time values
max_trial_strengths = []
trial_strength_samples = []

for trial in range(3):  # 3 calibration trials
    prev_strength_samples = strength_samples.copy()  # get previous trial's strength_samples
    prev_times = times.copy()  # get previous trial's times
    strength_samples = []  # reset the current trial's strength_samples
    times = []  # reset the current trial's times

    # instructions and draw graph
    if trial == 0:
        instructions_top_txt.text = f"Trial {trial+1}: When ready, squeeze as hard as you can!"
    else:
        instructions_top_txt.text = f"Trial {trial+1}: Try to squeeze harder than on your last trial!"
    stimuli = [instructions_top_txt, horizontal_graph_line, vertical_graph_line]
    hf.draw_all_stimuli(win, stimuli, 1)

    # wait for participant to start
    recording_started = False
    start_time = None
    while not recording_started:
        strength = hf.sample_strength(DUMMY, mouse, gripper, gripper_zero_baseline)
        # threshold to start recording
        if strength > 0.1:
            recording_started = True
            start_time = core.getTime()

    # begin recording for 4 seconds after strength threshold is exceeded
    recording_duration = 4
    while core.getTime() - start_time < recording_duration:
        strength = hf.sample_strength(DUMMY, mouse, gripper, gripper_zero_baseline)
        strength_samples.append(strength)
        current_time = core.getTime() - start_time
        times.append(current_time)

        # draw the graph
        instructions_top_txt.draw()
        horizontal_graph_line.draw()
        vertical_graph_line.draw()
        # draw previous strength_samples
        for i in range(1, len(prev_strength_samples)):
            start_point = [graph_start_x + prev_times[i-1] * (graph_length / recording_duration), graph_start_y + prev_strength_samples[i-1] * (graph_height / 6)]
            end_point = [graph_start_x + prev_times[i] * (graph_length / recording_duration), graph_start_y + prev_strength_samples[i] * (graph_height / 6)]
            visual.Line(win, start=start_point, end=end_point, lineWidth=8, lineColor='lightblue').draw()
        # draw current strength_samples
        for i in range(1, len(strength_samples)):
            start_point = [graph_start_x + times[i - 1] * (graph_length / recording_duration), graph_start_y + strength_samples[i - 1] * (graph_height / 6)]
            end_point = [graph_start_x + times[i] * (graph_length / recording_duration), graph_start_y + strength_samples[i] * (graph_height / 6)]
            visual.Line(win, start=start_point, end=end_point, lineWidth=8, lineColor='red').draw()
        win.flip()
        hf.exit_q(win)

    # save strength trace and max strength in a half-second window around the peak for each trial
    quarter_second_window_length = int((len(strength_samples) / recording_duration) / 4) # determine how many samples represent a quarter of a second
    window_start = max(0, strength_samples.index(max(strength_samples)) - quarter_second_window_length)
    window_end = min(strength_samples.index(max(strength_samples)) + quarter_second_window_length + 1, len(strength_samples))
    max_trial_strengths.append(sum(strength_samples[window_start:window_end]) / (window_end - window_start))
    trial_strength_samples.append(strength_samples)

    # rest period message
    core.wait(3)
    instructions_txt.text = "Trial completed. \n\n Relax for a moment."
    hf.draw_all_stimuli(win, [instructions_txt], 5)


# SAVE DATA
info['max_strength_1'] = max_trial_strengths[0]
info['strength_trace_1'] = '"' + json.dumps(trial_strength_samples[0]) + '"'
info['max_strength_2'] = max_trial_strengths[1]
info['strength_trace_2'] = '"' + json.dumps(trial_strength_samples[1]) + '"'
info['max_strength_3'] = max_trial_strengths[2]
info['strength_trace_3'] = '"' + json.dumps(trial_strength_samples[2]) + '"'
info['max_strength'] = (max_trial_strengths[1] + max_trial_strengths[2]) / 2
dataline = ','.join([str(info[v]) for v in log_vars])
datafile.write(dataline + '\n')
datafile.flush()


# THANK YOU
big_txt.text = 'Your grip strength test is completed.'
hf.draw_all_stimuli(win,[big_txt], 8)


# CLOSE WINDOW
win.close()
core.quit()