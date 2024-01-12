###################################
# IMPORT PACKAGES
###################################
import os
import numpy as np
from psychopy import gui, visual, core, data, event, logging, misc, clock
from psychopy.hardware import keyboard
from mpydev import BioPac

###################################
# SESSION INFORMATION
###################################
DUMMY = False  # set this to true to use the mouse instead of the hand grippers

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
if not DUMMY:
    mp = BioPac("MP160", n_channels=2, samplerate=200, logfile="test", overwrite=True)
else:
    mp = 1

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
    size=[1920, 1080],  # set correct monitor size
    fullscr=True,
    screen=1,
    allowGUI=True, allowStencil=False,
    monitor='testMonitor', color='black',
    blendMode='avg', useFBO=True, units='pix')

###################################
# CREATE STIMULI
###################################
next_button = visual.Rect(win=win, units="pix", width=160, height=60, pos=(0, -250), fillColor='mediumspringgreen')
next_button_txt = visual.TextStim(win=win, text='NEXT', height=20, pos=next_button.pos, color='black', bold=True)
next_glow = visual.Rect(win, width=170, height=70, pos=next_button.pos, fillColor='mediumspringgreen', opacity=0.5)
welcome_txt = visual.TextStim(win=win, text='Welcome to this experiment!', height=90, pos=[0, 40], color='white',
                              wrapWidth=800)
instructions1_txt = visual.TextStim(win=win,
                                     text="In this task, you will be offered points in "
                                          "exchange for exerting effort. \n\nYour goal is to decide whether the points "
                                          "offered are worth the effort required.",
                                     height=40, pos=[0, 80], wrapWidth=800, color='white')
instructions2_txt = visual.TextStim(win=win,
                                     text="On each trial, you will be presented with an offer of points. Consider "
                                          "carefully if the points are worth the effort required. \n\nIf you think "
                                          "it's worth it, click 'Accept'. \n\nIf you think it's not, click 'Reject'.",
                                     height=40, pos=[0, 80], wrapWidth=800, color='white')
instructions3_txt = visual.TextStim(win=win,
                                     text="When you click 'Accept', you will use the hand gripper to exert effort. "
                                          "\n\nThe amount of effort required will be "
                                          "indicated on each trial. \n\nSqueeze the hand gripper with effort "
                                          "corresponding to the indicated level.",
                                     height=40, pos=[0, 80], wrapWidth=800, color='white')
instructions4_txt = visual.TextStim(win=win,
                                     text="As you squeeze the hand gripper, a bar on the screen will fill up. This "
                                          "bar shows the amount of effort you are exerting. \n\nIf you reach the "
                                          "required effort level, \nyou earn the points. \n\nIf you fail to reach the "
                                          "required level, \nyou lose points.",
                                     height=40, pos=[0, 80], wrapWidth=800, color='white')
instructions5_txt = visual.TextStim(win=win,
                                     text="Your goal is to accumulate \nas many "
                                          "points as possible. \n\nMake your decisions "
                                          "wisely and exert \nthe right amount of effort. \n\nLet's begin!",
                                     height=40, pos=[0, 80], wrapWidth=800, color='white')
thanks_txt = visual.TextStim(win=win, text='Thank you for completing the study!', height=70, pos=[0, 40], color='white')

effort_outline = visual.Rect(win, width=120, height=320, pos=(100, 50), lineColor='grey', fillColor=None)
effort_fill = visual.Rect(win, width=120, height=int(info['effort'] / 10.0 * 320),
                          pos=(100, 50 - 160 + int(info['effort'] / 10.0 * 320) / 2), lineColor=None,
                          fillColor='lightblue')
effort_fill_dynamic = visual.Rect(win, width=120, fillColor='darkblue', lineColor=None)
effort_text = visual.TextStim(win, text=f"Effort: {info['effort']}", pos=(100, -130), color='white', height=22)

reward_text = visual.TextStim(win, text=f"{info['reward']} Points", pos=(-150, 100), color='white', height=42,
                              bold=True)

accept_button = visual.Rect(win, width=150, height=60, pos=(0, -270), fillColor='springgreen')
accept_button_txt = visual.TextStim(win=win, text='ACCEPT', height=16, pos=accept_button.pos, color='black',
                                    bold=True)
accept_glow = visual.Rect(win, width=160, height=70, pos=accept_button.pos, fillColor='springgreen', opacity=0.5)

reject_button = visual.Rect(win, width=accept_button.width, height=accept_button.height, pos=(0, -350), fillColor='red')
reject_button_txt = visual.TextStim(win=win, text='REJECT', height=accept_button_txt.height, pos=reject_button.pos,
                                    color='black',
                                    bold=True)
reject_glow = visual.Rect(win, width=accept_glow.width, height=accept_glow.height, pos=reject_button.pos,
                          fillColor='red', opacity=0.5)
squeeze_txt = visual.TextStim(win=win, text='Squeeze the hand gripper until the bar is filled up to the threshold!',
                              height=40, pos=[0, 300], color='white', wrapWidth=2000)


###################################
# FUNCTIONS
###################################
# add this in to allow exiting the experiment when we are in full screen mode
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

# draw all stimuli on win flip
def draw_all_stimuli(stimuli):
    for stimulus in stimuli:
        stimulus.draw()

def display_instructions(stimuli, mouse):
    draw_all_stimuli(stimuli), win.flip(), exit_q(), core.wait(0.2)
    while not mouse.isPressedIn(next_button):
        # check if the mouse is hovering over the button
        if next_button.contains(mouse):
            next_glow.draw()
        # draw all stimuli and flip the window
        draw_all_stimuli(stimuli)
        win.flip(), exit_q(), core.wait(0.05)
    core.wait(0.5)

# calculate net value
def calculate_net_value(reward, effort, k):
    return reward - k * effort ** 2

# do trial and estimate k
def do_trial(win, mouse, info, effort_outline, effort_fill, effort_text, reward_text, accept_button, accept_button_txt,
             reject_button, reject_button_txt):
    win.flip(), exit_q(), core.wait(0.5)  # blank screen in between trials

    # update stimuli
    effort_fill.height = int(info['effort'] / 10.0 * 320)
    effort_fill.pos = (100, 50 - 160 + int(info['effort'] / 10.0 * 320) / 2)
    effort_text.text = f"Effort: {info['effort']}"
    reward_text.text = f"{info['reward']} Points"

    # draw all stimuli
    stimuli = [effort_outline, effort_fill, effort_text, reward_text, accept_button, accept_button_txt, reject_button,
               reject_button_txt]
    draw_all_stimuli(stimuli), win.flip(), exit_q(), core.wait(0.2)

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
            info['participant_response'] = response
            core.wait(0.5)
            if accept_hover:
                response = 'accepted'

            elif reject_hover:
                response = 'rejected'

        # Draw all stimuli and flip the window
        draw_all_stimuli(stimuli), core.wait(0.05), win.flip(), exit_q()

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

    # if participant accepted, make them exert the effort (CONSIDER DOING THIS ONLY ON A SUBSET OF ACCEPT TRIALS!!!)
    if response == 'accepted':
        success = None
        while success is None:
            effort_bar_bottom_y = effort_outline.pos[1] - (effort_outline.height / 2)
            mouse_y = mouse.getPos()[1]  # get the vertical position of the mouse

            # calculate the dynamic height of the dark blue bar based on mouse position
            # ensure that the height cannot exceed the total height of the effort bar (320 in this case)
            dynamic_height = max(min(mouse_y - effort_bar_bottom_y, 320), 0)
            effort_fill_dynamic.height = dynamic_height
            effort_fill_dynamic.pos = (100, effort_bar_bottom_y + dynamic_height / 2)

            stimuli = [squeeze_txt, effort_outline, effort_fill, effort_fill_dynamic, effort_text]
            draw_all_stimuli(stimuli)
            win.flip(), exit_q()

            if effort_fill_dynamic.height > effort_fill.height:
                success = True
                reward_text.text = f"Well done! \n\n+ {info['reward']} Points"
                stimuli = [effort_outline, effort_fill, effort_fill_dynamic, effort_text, reward_text]
                draw_all_stimuli(stimuli)
                win.flip(), exit_q(), core.wait(1.6)

    # get updated info dict back out
    return info

    # CONSIDER ADDING AN EARLY STOPPING RULE!!!


###################################
# EXPERIMENT
###################################
# start the hand gripper recording
if not DUMMY:
    mp.start_recording()



# TRYING OUT THE HAND GRIPPERS!!!!!!!!!!!!!!
text1 = visual.TextStim(win, text='', color='white', pos=(0, 30))
text2 = visual.TextStim(win, text='', color='white', pos=(0, -30))
while True:
    sample = mp.sample()
    text1.setText("Left gripper = %.3f" % sample[0])
    text2.setText("Right gripper = %.3f" % sample[1])
    text1.draw()
    text2.draw()
    win.flip(), exit_q()
    core.wait(0.1)






# initialise clock and mouse
globalClock = core.Clock()
mouse = event.Mouse()
win.mouseVisible = True

# welcome
stimuli = [welcome_txt, next_button, next_button_txt]
display_instructions(stimuli, mouse)

# instructions
stimuli = [instructions1_txt, next_button, next_button_txt]
display_instructions(stimuli, mouse)

stimuli = [instructions2_txt, next_button, next_button_txt]
display_instructions(stimuli, mouse)

stimuli = [instructions3_txt, next_button, next_button_txt]
display_instructions(stimuli, mouse)

stimuli = [instructions4_txt, next_button, next_button_txt]
display_instructions(stimuli, mouse)

stimuli = [instructions5_txt, next_button, next_button_txt]
display_instructions(stimuli, mouse)

# actual trials
for trial in range(gv['max_n_trials']):
    info = do_trial(win, mouse, info, effort_outline, effort_fill, effort_text, reward_text, accept_button,
                    accept_button_txt, reject_button, reject_button_txt)
    info['trial_count'] += 1
    dataline = ','.join([str(info[v]) for v in log_vars])
    datafile.write(dataline + '\n')
    datafile.flush()
    info['reward'] = info['next_reward']
    info['effort'] = info['next_effort']
core.wait(0.5)

# thank you
thanks_txt.draw()
win.flip(), exit_q()
core.wait(5)

# close window
win.close()
core.quit()
