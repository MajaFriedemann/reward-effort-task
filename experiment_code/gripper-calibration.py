# script for calibrating the hand grippers
# needs to be run before main.py
# for the pgACC TUS study probably best to do this on the structural scan day alongside calibrating the dot motion stimulus for the confidence task?
# Maja Friedemann 2024


###################################
# IMPORT PACKAGES
###################################
import os
import numpy as np
from psychopy import gui, visual, core, data, event, monitors
from mpydev import BioPac
import json


###################################
# SESSION INFO & DATA SAVING
###################################
print('Reminder: Press Q to quit.')

# initialise the hand gripper
gripper = BioPac("MP160", n_channels=2, samplerate=200, logfile="test", overwrite=True)

# pop-up window asking for participant number and which hand they will use for the gripper (they need to be happy to use the respective other hand for the keyboard)
expInfo = {'participant nr': '999',
           'gripper hand (l/r)': ''}
expName = 'reward-effort-pgACC-TUS_calibration'
curecID = 'R88533/RE002'
dlg = gui.DlgFromDict(dictionary=expInfo, sortKeys=False, title=expName)
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
# SET UP WINDOW
###################################
win = visual.Window(
    size=None,  # tells PsychoPy to use the native resolution of the screen
    fullscr=True,  # fullscreen mode
    screen=0,  # adjust if using multiple monitors
    allowGUI=False,
    color='black',
    blendMode='avg',
    useFBO=True,  # Frame Buffer Object for rendering (good for complex stimuli)
    units='pix'  # units in pixels (fine for this task but for more complex (e.g. dot motion) stimuli, we probably need visual degrees
)


###################################
# TASK
###################################
# start the hand gripper recording
gripper.start_recording()