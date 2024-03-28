# script for the main task
# if using the hand-grippers (rather than DUMMY version), run gripper-calibration.py before this to determine the participant's max grip strength
# Maja Friedemann 2024

###################################
# IMPORT PACKAGES
###################################
import os
import numpy as np
from psychopy import gui, visual, core, data, event
from mpydev import BioPac
import json


###################################
# SESSION INFORMATION
###################################
print('Reminder: Press Q to quit.')  # press Q and experiment will quit on next win flip

# Pop-up window asking for participant number, session, age, and gender
expInfo = {'participant nr': '999',
           'dummy (y/n)': 'y',
           'session nr': '1',
           'age': '',
           'gender (f/m/o)': '',
           }
expName = 'reward-effort-pgACC-TUS'
curecID = 'R88533/RE002'
dlg = gui.DlgFromDict(dictionary=expInfo, sortKeys=False, title=expName)
if not dlg.OK:
    core.quit()  # pressed cancel on the pop-up window


###################################
# SET EXPERIMENT VARIABLES
###################################
# hand grippers
if expInfo['dummy (y/n)'] == 'y':
    # if DUMMY is set to True, we will use the mouse y position instead of the hand grippers for effort exertion
    DUMMY = True
else:
    # if DUMMY is set to False, we initialise the hand grippers
    DUMMY = False
    gripper = BioPac("MP160", n_channels=2, samplerate=200, logfile="test", overwrite=True)

# variables in gv are used to structure the task
gv = dict(
    max_n_trials=45,
    n_trials_per_block=45 / 3
)


###################################
# SET DATA SAVING VARIABLES
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

    gripper_baseline=None, # this is the gripper 0 point, for some reason it is often not precisely 0, so we measure it once in the beginning and then subtract it from all other measurements
    max_strength=None, # get this info from files saved by gripper-calibration.py

    block_count=0, # block counter
    trial_count=0, # trial counter

    offer_value_mean=None, # mean reward/loss value of current offer
    offer_value_uncertainty=None, # uncertainty of current offer
    offer_effort_required=None, # effort required to approach a reward / avoid a loss
    approach_avoid_effort=None, # approach of avoid trial

    participant_respnse=None, # accept or reject
    participant_choice_response_time=None,  # time taken to make a choice (accept or reject)
    effort_expended=None, # actual effort expended on trial during the 1 second where effort is above the threshold
    effort_trace=None, # trace of effort exerted over the complete trial (baseline corrected)
    participant_effort_response_time=None, # time taken to exert the required effort
)

# start a csv file for saving the participant data
log_vars = list(info.keys())
if not os.path.exists('task_data'):
    os.mkdir('task_data')
filename = os.path.join('task_data', '%s_%s_%s' % (info['participant'], info['session_nr'], info['date']))
datafile = open(filename + '.csv', 'w')
datafile.write(','.join(log_vars) + '\n')
datafile.flush()
