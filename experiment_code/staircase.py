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
print('Reminder: Press Q to quit.')  # press Q and experiment will quit on next win flip
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
    monitor='testMonitor', color='white',
    blendMode='avg', useFBO=True, units='pix')

###################################
# INSTRUCTIONS
###################################
th = 35
button = visual.Rect(
    win=win,
    units="pix",
    width=160,
    height=60,
    pos=(0, -200),
    fillColor=[-1, 1, -1],
    lineColor=[-1, .8, -1]
)
button_txt = visual.TextStim(win=win, text='NEXT', height=th, pos=button.pos, color=[-1, -1, -1], bold=True)
welcome_txt = visual.TextStim(win=win, text='Welcome to this experiment!', height=70, pos=[0, 0], color='black')
welcome2_txt = visual.TextStim(win=win, text='In this experiment, you will be playing a game with dots!', height=50,
                               pos=[0, 0], color='black')
thanks_txt = visual.TextStim(win=win, text='Thank you for completing the study!', height=70, pos=[0, 0], color='black')


###################################
# FUNCTIONS
###################################
# allow exiting the experiment when we are in full screen mode
def exit_q(key_list=None):
    # this just checks if anything has been pressed - it doesn't wait
    if key_list is None:
        key_list = ['q']
    keys = event.getKeys(keyList=key_list)
    res = len(keys) > 0
    if res:
        if 'q' in keys:
            win.close()
            core.quit()
    return res


# calculate net value
def calculate_net_value(reward, effort, k):
    return reward - k * effort ** 2


# show reward-effort offer
def do_trial(win, mouse, info):
    # draw reward effort offer
    effort_outline = visual.Rect(win, width=100, height=300, pos=(200, 0), lineColor='blue', fillColor=None)
    effort_fill = visual.Rect(win, width=100, height=info['effort'] / 10.0 * 300,
                              pos=(200, -150 + (info['effort'] / 10.0 * 300) / 2),
                              lineColor=None, fillColor='blue')
    effort_text = visual.TextStim(win, text=f"effort level: {info['effort']}", pos=(200, -200), color='black',
                                  height=20)
    reward_text = visual.TextStim(win, text=f"{info['reward']} points", pos=(-200, 200), color='black', height=20)
    accept_button = visual.ButtonStim(win, text='Accept', pos=(0, -100), size=(100, 50), color='green')
    reject_button = visual.ButtonStim(win, text='Reject', pos=(0, -200), size=(100, 50), color='red')
    effort_outline.draw(), effort_fill.draw(), effort_text.draw(), reward_text.draw(), accept_button.draw(), reject_button.draw()
    win.flip()

    # get participant response
    response = None
    while response is None:
        if accept_button.contains(mouse) and mouse.getPressed()[0]:
            response = 'accepted'
        elif reject_button.contains(mouse) and mouse.getPressed()[0]:
            response = 'rejected'
        core.wait(0.01)

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
    info['reward'], info['effort'] = max(min(next_reward, 28), 8), next_effort

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
welcome_txt.draw(), button.draw(), button_txt.draw()
win.flip(), exit_q(), core.wait(0.2)
while not mouse.isPressedIn(button):
    pass

welcome2_txt.draw(), button.draw(), button_txt.draw()
win.flip(), exit_q(), core.wait(0.2)
while not mouse.isPressedIn(button):
    pass

# actual trials
for trial in range(gv['max_n_trials']):
    info = do_trial(win, mouse, info)
    info['trial_count'] += 1
    dataline = ','.join([str(info[v]) for v in log_vars])
    datafile.write(dataline + '\n')
    datafile.flush()

print(info)

# thank you
thanks_txt.draw()
win.flip()
core.wait(5)

# close window
win.close()
core.quit()
