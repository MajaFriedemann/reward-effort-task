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
print('Reminder: Press Q to quit.')  # press Q and experiment will quit on next win flip

# Pop up asking for participant number, session, age, and gender
expInfo = {'participant nr': '',
           'dummy (y/n)': '',
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
if expInfo['dummy (y/n)'] == 'y':
    DUMMY = True
    mp = 1
else:
    DUMMY = False
    mp = BioPac("MP160", n_channels=2, samplerate=200, logfile="test", overwrite=True)

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

    gripper_baseline=None,
    max_effort_calibration_1=None,
    max_effort_calibration_2=None,
    max_effort_calibration_3=None,
    max_effort=None,

    trial_count=0,
    reward=18,  # initial reward
    effort=6,  # initial effort
    estimated_k=0.5,  # initial estimate
    estimated_net_value=18 - 0.5 * 6 ** 2,  # initial estimate
    participant_response=None

    # consider what info to save MAJA
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
    screen=0,
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
instructions_calibration_txt = visual.TextStim(win=win,
                                               text="In this task, you will be asked to squeeze a hand gripper. \n\n "
                                                    "When asked to do so, please "
                                                    "take the hand gripper in the hand that you are not currently "
                                                    "using for the computer mouse "
                                                    "and ensure you have a firm grip.\n\n"
                                                    "We will guide you through the process. \nFor now, please refrain "
                                                    "from touching the gripper as it needs to be calibrated first.",
                                               height=40, pos=[0, 80], wrapWidth=800, color='white')
calibration_done_txt = visual.TextStim(win=win,
                                       text="The calibration process is now complete. \n\n Please take the hand "
                                            "gripper in the hand that you are not currently using for the computer "
                                            "mouse and ensure you have a firm grip.\n\n"
                                            "When you are ready to get squeezing, click the 'Next' button.",
                                       height=40, pos=[0, 80], wrapWidth=800, color='white')
calibration_txt = visual.TextStim(win=win, text='Squeeze the hand gripper until the bar is filled up to the threshold!',
                                  height=40, pos=[0, 300], color='white', wrapWidth=2000)
instructions1_txt = visual.TextStim(win=win,
                                    text="Now we can start the task! You will earn points for your effort. \n\nYour objective "
                                         "is to evaluate if the points offered are worth the effort required.",
                                    height=40, pos=[0, 80], wrapWidth=800, color='white')
instructions2_txt = visual.TextStim(win=win,
                                    text="Each trial presents an offer of points. Carefully assess if the points "
                                         "justify the effort. \n\nClick 'Accept' if it's worth it, and 'Reject' if it's not.",
                                    height=40, pos=[0, 80], wrapWidth=800, color='white')
instructions3_txt = visual.TextStim(win=win,
                                    text="When you 'Accept', use the hand gripper to exert the specified effort. \n\nMatch "
                                         "your grip effort to the indicated level and hold it for 1 second. If you do "
                                         "not reach the required effort within 20 seconds, it counts as a failure and results in a loss.",
                                    height=40, pos=[0, 80], wrapWidth=800, color='white')

instructions4_txt = visual.TextStim(win=win,
                                    text="While gripping, a bar on the screen fills to represent your effort "
                                         "level. \n\nMeeting the required level for 1 second earns you points. Failing to reach "
                                         "it within 20 seconds results in a loss. \n\nRemember, every point you earn is worth 1 penny.",
                                    height=40, pos=[0, 80], wrapWidth=800, color='white')
instructions5_txt = visual.TextStim(win=win,
                                    text="Your objective is to maximize your point total. \n\nMake thoughtful decisions "
                                         "and apply the right effort. \n\nLet's begin!",
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
def do_trial(win, mouse, info, DUMMY, mp, effort_outline, effort_fill, effort_text, reward_text, accept_button,
             accept_button_txt,
             reject_button, reject_button_txt):
    win.flip(), core.wait(0.5), exit_q()  # blank screen in between trials

    gripper_zero_baseline = info['gripper_baseline']
    max_effort = info['max_effort']

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
        start_time = None  # Time when condition first met

        while success is None:
            effort_bar_bottom_y = effort_outline.pos[1] - (effort_outline.height / 2)
            if DUMMY:
                # calculate the dynamic height of the dark blue bar based on mouse position
                mouse_y = mouse.getPos()[1]  # get the vertical position of the mouse
                dynamic_height = max(min(mouse_y - effort_bar_bottom_y, 320), 0)
            else:
                # calculate the dynamic height of the dark blue bar based on current effort
                current_effort = mp.sample()[0] - gripper_zero_baseline
                effort_ratio = current_effort / max_effort
                dynamic_height = max(min(effort_ratio * 320, 320), 0)

                # ensure that the height cannot exceed the total height of the effort bar (320 in this case)
            effort_fill_dynamic.height = dynamic_height
            effort_fill_dynamic.pos = (100, effort_bar_bottom_y + dynamic_height / 2)

            # Check condition for dynamic height
            if effort_fill_dynamic.height >= effort_fill.height:
                if start_time is None:  # Condition just met
                    start_time = core.getTime()
                elapsed_time = core.getTime() - start_time
                time_left = 1 - elapsed_time
                if time_left <= 0:  # Countdown finished
                    success = True
                    break  # Exit the while loop to declare success
                else:  # Update countdown text during the countdown
                    reward_text.text = f"{round(time_left, 1)} seconds left"
            else:
                start_time = None  # Reset timer if condition not met
                reward_text.text = "Keep going!"  # Or any other feedback for the participant

            # Update stimuli and check for quit condition
            stimuli = [squeeze_txt, effort_outline, effort_fill, effort_fill_dynamic, effort_text, reward_text]
            draw_all_stimuli(stimuli)
            win.flip(), exit_q()

            core.wait(0.01)  # Short wait to prevent overwhelming the CPU

        if success:
            reward_text.text = f"Well done! \n\n+ {info['reward']} Points"
            stimuli = [effort_outline, effort_fill, effort_fill_dynamic, effort_text, reward_text]
            draw_all_stimuli(stimuli)
            win.flip(), exit_q(), core.wait(1.6)

    # get updated info dict back out
    return info

    # consider adding an early stopping rule - MAJA


def draw_graph_with_efforts(win, graph_start_x, graph_base_y, graph_length, graph_height, prev_efforts, prev_times,
                            efforts, times, calibration_text):
    # Draw graph axes
    visual.Line(win, start=(graph_start_x, graph_base_y), end=(graph_start_x + graph_length, graph_base_y), lineWidth=2,
                lineColor='white').draw()  # X-axis
    visual.Line(win, start=(graph_start_x, graph_base_y), end=(graph_start_x, graph_base_y + graph_height), lineWidth=2,
                lineColor='white').draw()  # Y-axis

    # Function to calculate point coordinates
    def calculate_point(time, effort, time_scale, effort_scale):
        x = graph_start_x + time * time_scale
        y = graph_base_y + effort * effort_scale
        return [x, y]

    # Time and effort scales
    time_scale = graph_length / 4
    effort_scale = graph_height / 4

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

    draw_all_stimuli([calibration_text])
    core.wait(0.01)  # Short wait to prevent overwhelming the CPU
    win.flip()


# calibration of hand grippers for 3 trials
# takes the average of average effort in a half-second window around the peak effort of trials 2 and 3
def do_calibration(win, mouse, info, DUMMY, mp, calibration_txt, welcome_txt, calibration_done_txt, next_button):
    graph_start_x = -200
    graph_base_y = -200
    graph_length = 400  # Total length of the x-axis
    graph_height = 250  # Total height of the y-axis

    max_efforts = []  # List to store max_trial_effort for each trial
    efforts = []  # List to store current trial's effort values
    times = []  # List to store current trial's time values

    # Display initial instructions
    calibration_txt.text = "Calilbration in process. Do not touch the hand gripper!"
    draw_all_stimuli([calibration_txt])
    win.flip(), exit_q(), core.wait(1)  # Display instructions for 2 seconds

    # Countdown: 3, 2, 1
    for countdown in range(3, 0, -1):
        welcome_txt.text = str(countdown)
        draw_all_stimuli([welcome_txt, calibration_txt])
        # Save the mp.sample()[0] from second 3 as the gripper zero baseline
        if not DUMMY and countdown == 3:
            gripper_zero_baseline = mp.sample()[0]
            info['gripper_baseline'] = gripper_zero_baseline
        win.flip()
        core.wait(1)

    stimuli = [calibration_done_txt, next_button, next_button_txt]
    display_instructions(stimuli, mouse)

    for trial in range(1, 4):  # Conduct 3 calibration trials
        prev_efforts = efforts.copy()  # Copy the previous trial's efforts
        prev_times = times.copy()  # Copy the previous trial's times
        efforts = []  # Reset the current trial's efforts
        times = []  # Reset the current trial's times
        # Display initial instructions
        if trial == 1:
            calibration_txt.text = f"Trial {trial}: When ready, squeeze as hard as you can!"
        else:
            calibration_txt.text = f"Trial {trial}: Try to squeeze harder than on your last trial!"
        visual.Line(win, start=(graph_start_x, graph_base_y), end=(graph_start_x + graph_length, graph_base_y),
                    lineWidth=2,
                    lineColor='white').draw()
        visual.Line(win, start=(graph_start_x, graph_base_y), end=(graph_start_x, graph_base_y + graph_height),
                    lineWidth=2,
                    lineColor='white').draw()
        draw_all_stimuli([calibration_txt])
        win.flip()
        exit_q()
        core.wait(1)  # Short wait to ensure participant is ready

        # Wait for participant to start
        recording_started = False
        start_time = None
        mouse_y_start = mouse.getPos()[1]
        while not recording_started:
            if DUMMY:
                effort = mouse.getPos()[1] - mouse_y_start
            else:
                current_effort = mp.sample()[0]
                effort = current_effort - gripper_zero_baseline

            if effort > 0.1:  # Threshold to start recording
                recording_started = True
                start_time = core.getTime()
            core.wait(0.1)

        # Begin recording for 4 seconds after effort threshold is exceeded
        recording_second_duration = 4
        while core.getTime() - start_time < recording_second_duration:
            if DUMMY:
                effort = mouse.getPos()[1] - mouse_y_start
            else:
                current_effort = mp.sample()[0]
                effort = current_effort - gripper_zero_baseline
            efforts.append(effort)
            current_time = core.getTime() - start_time
            times.append(current_time)

            # Draw the graph with the current and previous efforts
            draw_graph_with_efforts(win, graph_start_x, graph_base_y, graph_length, graph_height, prev_efforts,
                                    prev_times, efforts, times, calibration_txt)

        # Calculate the length of a 1-second window and its boundaries
        max_effort_index = efforts.index(max(efforts))
        quarter_second_window_length = int((len(efforts) / recording_second_duration) / 4)
        window_start = max(0, max_effort_index - quarter_second_window_length)
        window_end = min(len(efforts), max_effort_index + quarter_second_window_length + 1)
        # Calculate the average effort within the 1-second window around the maximum effort
        max_trial_effort = sum(efforts[window_start:window_end]) / (window_end - window_start)
        max_efforts.append(max_trial_effort)

        # Rest period message
        calibration_txt.text = "Trial completed. Relax for a moment."
        draw_graph_with_efforts(win, graph_start_x, graph_base_y, graph_length, graph_height, prev_efforts, prev_times,
                                efforts, times, calibration_txt)
        core.wait(3)  # Rest period

    # Finish calibration
    # Calculate max_effort as the average of max_trial_effort for trials 2 and 3
    max_effort = sum(max_efforts[1:3]) / 2  # Trials 2 and 3
    info['max_effort_calibration_1'] = max_efforts[0]
    info['max_effort_calibration_2'] = max_efforts[1]
    info['max_effort_calibration_3'] = max_efforts[2]
    info['max_effort'] = max_effort

    welcome_txt.text = f"Well done!"
    draw_all_stimuli([welcome_txt])
    win.flip(), exit_q(), core.wait(3)

    return info


###################################
# EXPERIMENT
###################################
# start the hand gripper recording
if not DUMMY:
    mp.start_recording()

# initialise clock and mouse
globalClock = core.Clock()
mouse = event.Mouse()
win.mouseVisible = True

# welcome
stimuli = [welcome_txt, next_button, next_button_txt]
display_instructions(stimuli, mouse)

# calibration instructions
stimuli = [instructions_calibration_txt, next_button, next_button_txt]
display_instructions(stimuli, mouse)

# calibration of hand grippers
info = do_calibration(win, mouse, info, DUMMY, mp, calibration_txt, welcome_txt, calibration_done_txt, next_button)
dataline = ','.join([str(info[v]) for v in log_vars])
datafile.write(dataline + '\n')
datafile.flush()

# task instructions
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
    info = do_trial(win, mouse, info, DUMMY, mp, effort_outline, effort_fill, effort_text, reward_text, accept_button,
                    accept_button_txt, reject_button, reject_button_txt)
    info['trial_count'] += 1
    dataline = ','.join([str(info[v]) for v in log_vars])
    datafile.write(dataline + '\n')
    datafile.flush()
    info['reward'] = info['next_reward']
    info['effort'] = info['next_effort']
    dataline = ','.join([str(info[v]) for v in log_vars])
    datafile.write(dataline + '\n')
    datafile.flush()
core.wait(0.5)

# save data
dataline = ','.join([str(info[v]) for v in log_vars])
datafile.write(dataline + '\n')
datafile.flush()

# thank you
thanks_txt.draw()
win.flip(), exit_q()
core.wait(5)

# close window
win.close()
core.quit()
