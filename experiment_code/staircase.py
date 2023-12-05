###################################
# IMPORT PACKAGES
###################################
import random
import os
import math
import numpy as np
from psychopy import gui, visual, core, data, event, logging, misc, clock
from psychopy.hardware import keyboard

###################################
# SESSION INFORMATION
###################################
# Pop up asking for participant number, session, age, and gender
expInfo = {'participant nr': '',
           'session (x/y/s)': '',
           'session nr': '',
           'age': '',
           'gender (f/m/o)': '',
           'handedness (l/r/b)': ''
           }
expName = 'pgACC-TUS-staircase'
curecID = ''
dlg = gui.DlgFromDict(dictionary=expInfo, sortKeys=False, title=expName)
if not dlg.OK:
    core.quit()  # pressed cancel

###################################
# SET EXPERIMENT VARIABLES
###################################
# variables in gv are just used to structure the task
gv = dict(
    max_n_trials=5
)

###################################
# SET DATA SAVING VARIABLES
###################################
# variables in info will be saved as participant data
info = dict(
    expName=expName,
    curec_ID=curecID,
    session=expInfo['session (x/y/s)'],
    session_nr=expInfo['session nr'],
    date=data.getDateStr(),
    end_date=None,

    participant=expInfo['participant nr'],
    age=expInfo['age'],
    gender=expInfo['gender (f/m/o)'],
    handedness=expInfo['handedness (l/r/b)'],

    trial_count=0,
    reward=18,  # initial reward
    effort=6,  # initial effort
    estimated_k=0.5,  # initial estimate
    estimated_net_value=18 - 0.5 * 6 ** 2,  # initial estimate
    participant_response=None
)

# logging
log_vars = list(info.keys())
if not os.path.exists('staircase_data'):
    os.mkdir('staircase_data')
filename = os.path.join('staircase_data', '%s_%s' % (info['participant'], info['date']))
datafile = open(filename + '.csv', 'w')
datafile.write(','.join(log_vars) + '\n')
datafile.flush()

###################################
# SET UP WINDOW
###################################
win = visual.Window(
    gammaErrorPolicy='ignore',
    size=[1000, 800],
    fullscr=False,
    screen=1,
    allowGUI=True, allowStencil=False,
    monitor='testMonitor', color='black',
    blendMode='avg', useFBO=True, units='pix')

###################################
# INSTRUCTIONS
###################################
next_button = visual.Rect(win=win, units="pix", width=160, height=60, pos=(0, -200), fillColor='green', opacity=0.85)
next_button_txt = visual.TextStim(win=win, text='NEXT', height=16, pos=next_button.pos, color='black', bold=True)
next_glow = visual.Rect(win, width=170, height=70, pos=next_button.pos, fillColor='green')
welcome_txt = visual.TextStim(win=win, text='Welcome to this experiment!', height=70, pos=[0, 0], color='white')
welcome2_txt = visual.TextStim(win=win, text='In this experiment, you will be playing a game with dots!', height=50,
                               pos=[0, 0], color='white')
thanks_txt = visual.TextStim(win=win, text='Thank you for completing the study!', height=70, pos=[0, 0], color='white')


###################################
# FUNCTIONS
###################################
# draw all stimuli on win flip
def draw_all_stimuli(stimuli):
    for stimulus in stimuli:
        stimulus.draw()


# calculate net value
def calculate_net_value(reward, effort, k):
    return reward - k * effort ** 2


# do trial and estimate k
def do_trial(win, mouse, info):
    win.flip(), core.wait(0.5)  # blank screen in between trials

    # stimuli
    effort_outline = visual.Rect(win, width=120, height=320, pos=(100, 100), lineColor='grey', fillColor=None)
    effort_fill = visual.Rect(win, width=120, height=int(info['effort'] / 10.0 * 320), pos=(100, 100 - 160 + int(info['effort'] / 10.0 * 320) / 2), lineColor=None, fillColor='lightblue')
    # the below is for animating the effort bar, so it fills up over time
    # effort_fill = visual.Rect(win, width=120, height=0, pos=(100, 100 - 160), lineColor=None, fillColor='lightblue')
    # for h in range(int(info['effort'] / 10.0 * 320)):
    #     effort_fill.height = h
    #     effort_fill.pos = (100, 100 - 160 + h / 2)
    #     stimuli = [effort_outline, effort_fill]
    #     draw_all_stimuli(stimuli), win.flip(), core.wait(0.005)
    effort_text = visual.TextStim(win, text=f"Effort: {info['effort']}", pos=(100, -80), color='white', height=22)

    reward_text = visual.TextStim(win, text=f"{info['reward']} Points", pos=(-120, 100), color='white', height=42,
                                  bold=True)

    accept_button = visual.Rect(win, width=150, height=60, pos=(0, -270), fillColor='green', opacity=0.85)
    accept_button_txt = visual.TextStim(win=win, text='ACCEPT', height=16, pos=accept_button.pos, color='black',
                                        bold=True)
    accept_glow = visual.Rect(win, width=160, height=70, pos=accept_button.pos, fillColor='green')

    reject_button = visual.Rect(win, width=accept_button.width, height=accept_button.height, pos=(0, -350), fillColor='red', opacity=0.85)
    reject_button_txt = visual.TextStim(win=win, text='REJECT', height=accept_button_txt.height, pos=reject_button.pos, color='black',
                                        bold=True)
    reject_glow = visual.Rect(win, width=accept_glow.width, height=accept_glow.height, pos=reject_button.pos, fillColor='red')

    stimuli = [effort_outline, effort_fill, effort_text, reward_text, accept_button, accept_button_txt, reject_button,
               reject_button_txt]
    draw_all_stimuli(stimuli), win.flip(), core.wait(0.2)

    # get participant response
    response = None
    while response is None:
        # Check for mouse hover over either button
        accept_hover = accept_button.contains(mouse)
        reject_hover = reject_button.contains(mouse)

        # Draw glow effect if mouse is hovering over buttons
        if accept_hover:
            accept_glow.draw()
        if reject_hover:
            reject_glow.draw()

        # Check for mouse click
        if mouse.getPressed()[0]:  # If the mouse is clicked
            core.wait(0.5)
            if accept_hover:
                response = 'accepted'
            elif reject_hover:
                response = 'rejected'

        # Draw all stimuli and flip the window
        draw_all_stimuli(stimuli)
        core.wait(0.05), win.flip()

    # update k based on response
    # adaptive step size using logarithmic decay
    step_size = 0.15 / np.log(info['trial_count'] + 4)
    info['estimated_net_value'] = calculate_net_value(info['reward'], info['effort'], info['estimated_k'])
    if info['estimated_net_value'] < 0 and response == 'accepted':
        info['estimated_k'] = info['estimated_k'] - step_size
    elif info['estimated_net_value'] > 0 and response == 'rejected':
        info['estimated_k'] = info['estimated_k'] + step_size

    # adjust reward and effort for next trial to aim for a net value close to zero
    # reward between 10 and 30, effort between 1 and 10
    target_net_value = np.random.uniform(-1, 1)
    next_effort = int(np.random.uniform(1, 10))
    next_reward = int(info['estimated_k'] * next_effort ** 2 + target_net_value)
    info['next_reward'], info['next_effort'] = max(min(next_reward, 28), 8), next_effort

    # get updated info dict back out
    return info


###################################
# EXPERIMENT
###################################

# initialise clock and mouse
globalClock = core.Clock()
mouse = event.Mouse()
win.mouseVisible = True

# welcome
stimuli = [welcome_txt, next_button, next_button_txt]
draw_all_stimuli(stimuli), win.flip(), core.wait(0.2)
while not mouse.isPressedIn(next_button):
    # check if the mouse is hovering over the button
    if next_button.contains(mouse):
        next_glow.draw()
    # draw all stimuli and flip the window
    draw_all_stimuli(stimuli)
    win.flip(), core.wait(0.05)

stimuli = [welcome2_txt, next_button, next_button_txt]
draw_all_stimuli(stimuli), win.flip(), core.wait(0.2)
while not mouse.isPressedIn(next_button):
    # check if the mouse is hovering over the button
    if next_button.contains(mouse):
        next_glow.draw()
    # draw all stimuli and flip the window
    draw_all_stimuli(stimuli)
    win.flip(), core.wait(0.05)
core.wait(0.5)

# actual trials
for trial in range(gv['max_n_trials']):
    info = do_trial(win, mouse, info)
    info['trial_count'] += 1
    dataline = ','.join([str(info[v]) for v in log_vars])
    datafile.write(dataline + '\n')
    datafile.flush()
    info['reward'] = info['next_reward']
    info['effort'] = info['next_effort']
core.wait(0.5)

# thank you
thanks_txt.draw()
win.flip()
core.wait(5)

# close window
win.close()
core.quit()
