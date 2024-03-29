"""
script for calibrating the hand grippers
needs to be run before main.py
for the pgACC TUS study probably best to do this on the structural scan day alongside calibrating the dot motion stimulus for the confidence task?

Maja Friedemann 2024
"""

###################################
# IMPORT PACKAGES
###################################
import os
import numpy as np
import json
from psychopy import gui, visual, core, data, event
import helper_functions as hf

print('Reminder: Press Q to quit.')


###################################
# SESSION INFO & DATA SAVING
###################################
expName = 'reward-effort-pgACC-TUS_calibration'
curecID = 'R88533/RE002'
expInfo = {'participant nr': '999',
           'gripper hand (l/r)': '',
           'dummy (y/n)': 'y'}
dlg = gui.DlgFromDict(dictionary=expInfo, sortKeys=False, title=expName) # pop-up window asking for participant number and which hand they will use for the gripper (they need to be happy to use the respective other hand for the keyboard)
if not dlg.OK:
    core.quit()  # pressed cancel on the pop-up window

# variables in info will be saved as participant data
info = dict(
    expName=expName,
    curec_ID=curecID,
    session_nr=0,
    date=data.getDateStr(),
    participant=expInfo['participant nr'],
    gripper_baseline=None, # this is the gripper 0 point, for some reason it is often not precisely 0, so we measure it once in the beginning and then subtract it from all other measurements

    # following variables are all baseline corrected
    strength_trace_1=None, # strength trace for calibration trial 1
    max_strength_1=None, # average strength in a half-second window around the peak effort for calibration trial 1
    strength_trace_2=None, # strength trace for calibration trial 2
    max_strength__2=None, # average strength in a half-second window around the peak effort for calibration trial 2
    strength_trace_3=None, # strength trace for calibration trial 3
    max_strength_3=None, # average strength in a half-second window around the peak effort for calibration trial 3
    max_strength=None,  # average of max_strength_calibration_2 and max_strength_calibration_3
)

# start a csv file for saving the participant data
log_vars = list(info.keys())
if not os.path.exists('calibration_data'):
    os.mkdir('calibration_data')
filename = os.path.join('calibration_data', '%s_%s_%s' % (info['participant'], info['session_nr'], info['date']))
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
    gripper = BioPac("MP160", n_channels=2, samplerate=200, logfile="test", overwrite=True)
    gripper.start_recording()


###################################
# SET UP WINDOW
###################################
win = visual.Window(
    size=[1920, 1080],  # set correct monitor size
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
hf.check_button(win, green_button, stimuli, mouse) # show instructions until button is pressed

# INSTRUCTIONS
instructions_txt.text = "We are going to test your grip strength! \n\nTo do this, we first need to calibrate the hand gripper. Please do not touch the gripper. Click NEXT to start the calibration."
stimuli = [green_button, button_txt, instructions_txt]
hf.draw_all_stimuli(win, stimuli)
hf.check_button(win, green_button, stimuli, mouse) # show instructions until button is pressed

# CALIBRATE HAND GRIPPER ZERO BASELINE
instructions_txt.text = "Calibration in process! Do not touch the hand gripper."
hf.draw_all_stimuli(win, [instructions_txt], 2) # show instructions for 2 seconds
for countdown in range(3, 0, -1):
    big_txt.text = str(countdown)
    hf.draw_all_stimuli(win, [big_txt, instructions_txt]) # display a 3, 2, 1 countdown
    if not DUMMY and countdown == 3:
        gripper_zero_baseline = gripper.sample()[0] # on 1, sample the gripper 0 baseline
        info['gripper_baseline'] = gripper_zero_baseline

# INSTRUCTIONS
instructions_txt.text = ("The calibration process is now complete. \n\n Please take the hand gripper in the hand that you are not currently using for the computer mouse and ensure you have a firm grip.\n\n"
                         "When you are ready to try out how hard you can squeeze, click NEXT.")
stimuli = [green_button, button_txt, instructions_txt]
hf.draw_all_stimuli(win, stimuli)
hf.check_button(win, green_button, stimuli, mouse) # show instructions until button is pressed







# CALIBRATE PARTICIPANT MAX GRIP STRENGTH - make function! MAJA 
efforts = []  # list to store effort values
times = []  # list to store time values

for trial in range(1, 4):  # 3 calibration trials
    prev_efforts = efforts.copy() # get previous trial's efforts
    prev_times = times.copy() # get previous trial's times
    efforts = []  # reset the current trial's efforts
    times = []  # reset the current trial's times

    # instructions and draw graph
    if trial == 1:
        instructions_txt.text = f"Trial {trial}: When ready, squeeze as hard as you can!"
    else:
        instructions_txt.text = f"Trial {trial}: Try to squeeze harder than on your last trial!"
    stimuli = [instructions_txt, horizontal_graph_line, vertical_graph_line]
    hf.draw_all_stimuli(win, stimuli, 1)

    # wait for participant to start
    recording_started = False
    start_time = None
    mouse_y_start = mouse.getPos()[1]
    while not recording_started:
        if DUMMY:
            effort = (mouse.getPos()[1] - mouse_y_start) / 100
        else:
            effort = gripper.sample()[0] - gripper_zero_baseline
        # threshold to start recording
        if effort > 0.1:
            recording_started = True
            start_time = core.getTime()
        core.wait(0.1)

    # begin recording for 4 seconds after effort threshold is exceeded
    while core.getTime() - start_time < 4:
        if DUMMY:
            effort = (mouse.getPos()[1] - mouse_y_start) / 100
        else:
            effort = gripper.sample()[0] - gripper_zero_baseline
        current_time = core.getTime() - start_time
        efforts.append(effort)
        times.append(current_time)

        # draw the graph with the current and previous efforts
        horizontal_graph_line.draw()
        vertical_graph_line.draw()

        # Function to calculate point coordinates
        def calculate_point(time, effort, time_scale, effort_scale):
            x = graph_start_x + time * time_scale
            y = graph_start_y + effort * effort_scale
            return [x, y]

        # Time and effort scales
        time_scale = graph_length / 4
        effort_scale = graph_height / 5

        # Draw previous efforts
        for i in range(len(prev_efforts)):
            if i == 0:
                start_point = calculate_point(0, 0, time_scale, effort_scale)  # Start from origin
            else:
                start_point = calculate_point(prev_times[i - 1], prev_efforts[i - 1], time_scale, effort_scale)
            end_point = calculate_point(prev_times[i], prev_efforts[i], time_scale, effort_scale)
            visual.Line(win, start=start_point, end=end_point, lineWidth=2, lineColor='lightblue').draw()

        # Draw current efforts
        for i in range(len(efforts)):
            if i == 0:
                start_point = calculate_point(0, 0, time_scale, effort_scale)  # Start from origin
            else:
                start_point = calculate_point(times[i - 1], efforts[i - 1], time_scale, effort_scale)
            end_point = calculate_point(times[i], efforts[i], time_scale, effort_scale)
            visual.Line(win, start=start_point, end=end_point, lineWidth=4, lineColor='red').draw()

    # Rest period message
    instructions_txt.text = "Trial completed. Relax for a moment."
    hf.draw_all_stimuli(win, [instructions_txt], 4)



