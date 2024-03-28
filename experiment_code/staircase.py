# old script - tried to have a staircase to calibrate reward-effort offers to participants' individual discounting functions
# analysing some pilot data showed that everyone does this similarly though
# also tried out some functions etc., so this is a slightly messy stand-alone script
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

# Pop up asking for participant number, session, age, and gender
expInfo = {'participant nr': '999',
           'dummy (y/n)': '',
           'session nr': '1',
           'age': '',
           'gender (f/m/o)': '',
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
    max_n_trials=45,
    n_trials_per_block=45 / 3,  # give participants a break and indication of how many trials are left every 20 trials
    effort_bar_height=320,
)


# colours
def convert_rgb_to_psychopy(rgb):
    return tuple([(x / 127.5) - 1 for x in rgb])

darkblue = convert_rgb_to_psychopy((0, 102, 0))  # effort exerted
darkblue = darkblue + (0.7,)  # add opacity
lightblue = convert_rgb_to_psychopy((102, 204, 102))  # effort required
green = 'green'  # accept button
red = 'red'  # reject button
gold = convert_rgb_to_psychopy((192, 192, 192))  # coins

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

    # this is the gripper 0 point, for some reason it is often not precisely 0, so we measure it once in the beginning
    # and then subtract it from all other measurements
    gripper_baseline=None,
    # average effort in a half-second window around the peak effort for calibration trial 1
    max_effort_calibration_1=None,
    # average effort in a half-second window around the peak effort for calibration trial 2
    max_effort_calibration_2=None,
    # average effort in a half-second window around the peak effort for calibration trial 3
    max_effort_calibration_3=None,
    max_effort=None,  # average of max_effort_calibration_2 and max_effort_calibration_3
    # max_effort minus gripper_baseline, so it is comparable across sessions / participants
    max_effort_baseline_corrected=None,

    trial_count=0,  # trial counter
    reward_offer=18,  # trial reward offer (initialised at 18)
    next_reward_offer=None,  # reward offer for next trial
    reward_earned=0,  # reward earned on trial
    total_reward=0,  # total reward earned so far
    effort_offer=6,  # trial effort offer (initialised at 6)
    next_effort_offer=None,  # effort offer for next trial
    effort_expended=None,  # actual effort expended on trial during the 1 second where effort is above the threshold,
    # divided by max_effort and times 10 to make comparable with effort_offer
    effort_trace=None,  # trace of effort exerted over the complete trial, baseline corrected
    # estimated k value (initialised at 0.5) - this will be used to calculate appropriate reward and effort offers
    estimated_k=0.5,
    estimated_net_value=18 - 0.5 * 6 ** 2,
    participant_response=None,  # participant response (accepted or rejected)
    participant_choice_response_time=None,  # time taken to make a choice (accept or reject)
    # time taken to exert the required effort (if not within 20 seconds, participant looses 1 point)
    participant_effort_response_time=None,
)

# logging
log_vars = list(info.keys())
if not os.path.exists('staircase_data'):
    os.mkdir('staircase_data')
filename = os.path.join('staircase_data', '%s_%s_%s' % (info['participant'], info['session_nr'], info['date']))
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
next_button = visual.Rect(win=win, units="pix", width=160, height=60, pos=(0, -270), fillColor='green')
next_button_txt = visual.TextStim(win=win, text='NEXT', height=25, pos=next_button.pos, color='black', bold=True,
                                  font='Monospace')
continue_button_txt = visual.TextStim(win=win, text='CONTINUE', height=25, pos=next_button.pos, color='black',
                                      bold=True, font='Monospace')
next_glow = visual.Rect(win, width=170, height=70, pos=next_button.pos, fillColor='green', opacity=0.5)
welcome_txt = visual.TextStim(win=win, text='Welcome to this experiment!', height=90, pos=[0, 40], color='white',
                              wrapWidth=800, font='Monospace')
instructions_calibration_txt = visual.TextStim(win=win,
                                               text="In this task, you will be asked to squeeze a hand gripper. \n\n "
                                                    "When asked to do so, please "
                                                    "take the hand gripper and ensure you have a firm grip.\n\n"
                                                    "We will guide you through the process. \n\nFor now, please refrain"
                                                    " from touching the gripper as it needs to be calibrated first.",
                                               height=40, pos=[0, 80], wrapWidth=900, color='white', font='Monospace')
calibration_done_txt = visual.TextStim(win=win,
                                       text="The calibration process is now complete. \n\n Please take the hand "
                                            "gripper in the hand that you are not currently using for the computer "
                                            "mouse and ensure you have a firm grip.\n\n"
                                            "When you are ready to try out how hard you can squeeze, click the 'Next' "
                                            "button.",
                                       height=40, pos=[0, 80], wrapWidth=900, color='white', font='Monospace')
calibration_txt = visual.TextStim(win=win, text='Squeeze the hand gripper until the bar is filled up to the threshold!',
                                  height=40, pos=[0, 300], color='white', wrapWidth=2000, font='Monospace')
instructions1_txt = visual.TextStim(win=win,
                                    text="Now you can start earning points - each worth 1 penny - for your effort! \n\n"
                                         "Each trial will present an offer of up to 30 points and an amount of effort "
                                         "required to "
                                         "get them. Carefully assess if the points "
                                         "justify the effort. \n\nUse the mouse to click 'Accept' if it's worth it, "
                                         "and 'Reject' if it's not.",
                                    height=40, pos=[0, 80], wrapWidth=900, color='white', font='Monospace')
instructions2_txt = visual.TextStim(win=win,
                                    text="When you 'Accept', squeeze the hand gripper to exert the specified "
                                         "effort. \n\n"
                                         "As you squeeze, a bar on the screen fills to represent your effort "
                                         "level. \n\nMatch your squeezing effort to at least the indicated level and "
                                         "hold it for 1 second.",
                                    height=40, pos=[0, 80], wrapWidth=900, color='white', font='Monospace')

instructions3_txt = visual.TextStim(win=win,
                                    text="Meeting the required level earns you the points offered on that trial. "
                                         "\n\nFailing to reach "
                                         "it within 8 seconds results in a loss of 1 point."
                                         "\n\n Click 'Next' to complete " + str(gv['max_n_trials']) + " trials!",
                                    height=40, pos=[0, 80], wrapWidth=900, color='white', font='Monospace')
instructions4_txt = visual.TextStim(win=win, text="Let's begin!", height=90, pos=[0, 40], color='white',
                                    wrapWidth=800, font='Monospace')

effort_outline = visual.Rect(win, width=120, height=gv['effort_bar_height'], pos=(-220, 25), lineColor='grey',
                             fillColor=None)
effort_fill = visual.Rect(win, width=120, height=int(info['effort_offer'] / 10.0 * gv['effort_bar_height']),
                          pos=(-220, 25 - 160 + int(info['effort_offer'] / 10.0 * gv['effort_bar_height']) / 2),
                          lineColor=None,
                          fillColor=lightblue)
effort_fill_dynamic = visual.Rect(win, width=120, fillColor=darkblue, lineColor=None)
effort_text = visual.TextStim(win, text="Effort: ", pos=(-300, 230), color='white', height=42, alignText='left',
                              font='Monospace')

reward_text = visual.TextStim(win, text=f"Points: {info['reward_offer']}", pos=(200, 230), color='white', height=42,
                              font='Monospace')

accept_button = visual.Rect(win, width=150, height=60, pos=(0, -270), fillColor=green)
accept_button_txt = visual.TextStim(win=win, text='ACCEPT', height=22, pos=accept_button.pos, color='black',
                                    bold=True, font='Monospace')
accept_glow = visual.Rect(win, width=160, height=70, pos=accept_button.pos, fillColor=green, opacity=0.5)

reject_button = visual.Rect(win, width=accept_button.width, height=accept_button.height, pos=(0, -350), fillColor=red)
reject_button_txt = visual.TextStim(win=win, text='REJECT', height=accept_button_txt.height, pos=reject_button.pos,
                                    color='black',
                                    bold=True, font='Monospace')
reject_glow = visual.Rect(win, width=accept_glow.width, height=accept_glow.height, pos=reject_button.pos,
                          fillColor=red, opacity=0.5)
squeeze_txt = visual.TextStim(win=win, text='Squeeze until you are above the threshold!',
                              height=40, pos=[0, 300], color='white', wrapWidth=2000, font='Monospace')
countdown_txt = visual.TextStim(win, text='Keep going!', pos=(200, 80), color='white', height=42, font='Monospace')


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


# draw points
def create_points(win, num_points, start_x=200, start_y=10):
    coin_radius = 20  # Size of the coins
    coin_spacing_horizontal = 40  # Horizontal spacing between columns
    coin_spacing_vertical = 10  # Vertical spacing between coins in a stack
    max_coins_per_column = 5  # Maximum number of coins per column before starting a new column

    # Calculate the number of columns needed
    num_columns = (num_points + max_coins_per_column - 1) // max_coins_per_column

    # Calculate the starting x-coordinate for the first coin
    coin_x_start = start_x - ((num_columns - 1) * coin_spacing_horizontal) / 2

    coins = []  # List to store the coin visual objects

    for i in range(num_points):
        column = i // max_coins_per_column
        row = i % max_coins_per_column

        coin_x = coin_x_start + column * coin_spacing_horizontal
        coin_y = start_y + row * (coin_radius + coin_spacing_vertical) - (max_coins_per_column * coin_radius) / 2

        coin = visual.Circle(win, units='pix', radius=coin_radius, fillColor=gold, lineColor='black')
        coin.pos = (coin_x, coin_y)
        coins.append(coin)

    return coins


def draw_points(coins):
    for coin in coins:
        coin.draw()


# do trial and estimate k
def do_trial(win, mouse, info, gv, DUMMY, mp, effort_outline, effort_fill, effort_text, reward_text, accept_button,
             accept_button_txt,
             reject_button, reject_button_txt, countdown_txt):
    win.flip(), core.wait(1), exit_q()  # blank screen in between trials

    gripper_zero_baseline = info['gripper_baseline']
    max_effort = info['max_effort']
    effort_trace = []
    info['effort_expended'] = 0
    elapsed_time = 0

    # update stimuli
    effort_fill.height = int(info['effort_offer'] / 10.0 * gv['effort_bar_height'])
    effort_fill.pos = (-220, 25 - 160 + int(info['effort_offer'] / 10.0 * gv['effort_bar_height']) / 2)
    effort_text.text = f"Effort: {info['effort_offer']}0%"
    reward_text.text = f"Points: {info['reward_offer']}"
    coins = create_points(win, info['reward_offer'])

    # get participant response
    response = None
    response_start_time = core.getTime()
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
            info['participant_choice_response_time'] = core.getTime() - response_start_time
            info['participant_response'] = response
            core.wait(0.5)
            if accept_hover:
                response = 'accepted'
            elif reject_hover:
                response = 'rejected'
                info['reward_earned'] = 0
            info['participant_response'] = response

        # Draw all stimuli and flip the window
        stimuli = [effort_outline, effort_fill, effort_text, accept_button, accept_button_txt,
                   reject_button, reject_button_txt, reward_text]
        draw_all_stimuli(stimuli)
        draw_points(coins)
        core.wait(0.02), win.flip(), exit_q()

    # update k based on response
    # adaptive step size using logarithmic decay
    current_k = info['estimated_k']
    step_size = 0.15 / np.log(info['trial_count'] + 4)
    info['estimated_net_value'] = calculate_net_value(info['reward_offer'], info['effort_offer'], info['estimated_k'])
    if info['estimated_net_value'] < 0 and response == 'accepted':
        info['estimated_k'] = current_k - step_size
    elif info['estimated_net_value'] > 0 and response == 'rejected':
        info['estimated_k'] = current_k + step_size

    # adjust reward and effort for next trial to aim for a net value close to zero
    # reward between 4 and 30, effort between 1 and 10
    target_net_value = np.random.uniform(-1, 1)
    next_reward_offer = int(np.random.uniform(4, 31))  # Randomly sample next_reward_offer between 4 and 30
    while abs(next_reward_offer - info['reward_offer']) < 2:
        next_reward_offer = int(np.random.uniform(4, 31))
    current_k = info['estimated_k']
    if (next_reward_offer - target_net_value) / current_k > 0:
        next_effort_offer = np.sqrt((next_reward_offer - target_net_value) / current_k)
        next_effort_offer = np.clip(round(next_effort_offer), 1, 10)
    else:
        next_effort_offer = 1

    info['next_effort_offer'], info['next_reward_offer'] = next_effort_offer, next_reward_offer

    # if participant accepted, make them exert the effort
    if response == 'accepted':
        success = None
        time_window_start_time = core.getTime()  # time when the 20-second window starts during which they need to be
        # successful if they do not want to lose 1 point
        start_time = None  # time when effort condition is first met
        while success is None:
            elapsed_time = core.getTime() - time_window_start_time
            if elapsed_time >= 8:  # Check if 8 seconds have elapsed
                success = False  # Participant failed, exit the loop
                break
            effort_bar_bottom_y = effort_outline.pos[1] - (effort_outline.height / 2)
            if DUMMY:
                # calculate the dynamic height of the dark blue bar based on mouse position
                mouse_y = mouse.getPos()[1]  # get the vertical position of the mouse
                dynamic_height = max(min(mouse_y - effort_bar_bottom_y, gv['effort_bar_height']), 0)
            else:
                # calculate the dynamic height of the dark blue bar based on current effort
                current_effort = mp.sample()[0] - gripper_zero_baseline
                effort_trace.append(current_effort)
                effort_ratio = current_effort / max_effort
                dynamic_height = max(min(effort_ratio * gv['effort_bar_height'], gv['effort_bar_height']), 0)
            # ensure that the height cannot exceed the total height of the effort bar
            effort_fill_dynamic.height = dynamic_height
            effort_fill_dynamic.pos = (-220, effort_bar_bottom_y + dynamic_height / 2)

            # Check condition for dynamic height
            total_efforts_in_window = []
            if effort_fill_dynamic.height >= effort_fill.height:
                # Accumulate effort samples during the 1-second period
                if not DUMMY:
                    current_effort = mp.sample()[0] - gripper_zero_baseline
                    effort_trace.append(current_effort)
                else:
                    current_effort = mouse.getPos()[1]
                total_efforts_in_window.append(current_effort)
                if start_time is None:  # condition just met
                    start_time = core.getTime()
                elapsed_condition_time = core.getTime() - start_time
                if elapsed_condition_time >= 1:  # Participant met the effort condition for 1 second
                    success = True
                    effort_exerted_in_window = sum(total_efforts_in_window) / len(total_efforts_in_window)
                    info['effort_expended'] = (effort_exerted_in_window / max_effort) * 10
                    break  # Exit the while loop to declare success
                else:  # Update countdown text during the effort condition
                    countdown_txt.text = f"{round(1.5 - elapsed_condition_time, 1)} seconds left"
            else:
                start_time = None  # Reset timer if condition not met
                countdown_txt.text = "Keep going!"

            # Update stimuli
            stimuli = [squeeze_txt, effort_outline, effort_fill, effort_fill_dynamic, countdown_txt]
            draw_all_stimuli(stimuli)
            win.flip(), exit_q()

            core.wait(0.01)  # Short wait to prevent overwhelming the CPU

        if success:
            countdown_txt.text = f"Well done! \n\n+ {info['reward_offer']} Points"
            info['reward_earned'] = info['reward_offer']
            stimuli = [countdown_txt]
            draw_all_stimuli(stimuli)
            coins = create_points(win, info['reward_offer'], start_x=-140)
            draw_points(coins)
            win.flip(), exit_q(), core.wait(2.4)
        else:
            # Participant failed to meet the effort condition within 20 seconds, deduct 1 point
            info['reward_earned'] = -1
            countdown_txt.text = "Effort condition not met within 8 seconds. \n\nYou lost 1 point."
            stimuli = [countdown_txt]
            draw_all_stimuli(stimuli)
            win.flip(), exit_q(), core.wait(2.4)

    info['total_reward'] = int(info['total_reward']) + int(info['reward_earned'])
    info['effort_trace'] = '"' + json.dumps(effort_trace) + '"'
    info['participant_effort_response_time'] = elapsed_time
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
    effort_scale = graph_height / 5

    # Draw previous efforts
    for i in range(len(prev_efforts)):
        if i == 0:
            start_point = calculate_point(0, 0, time_scale, effort_scale)  # Start from origin
        else:
            start_point = calculate_point(prev_times[i - 1], prev_efforts[i - 1], time_scale, effort_scale)
        end_point = calculate_point(prev_times[i], prev_efforts[i], time_scale, effort_scale)
        visual.Line(win, start=start_point, end=end_point, lineWidth=2, lineColor=lightblue).draw()

    # Draw current efforts
    for i in range(len(efforts)):
        if i == 0:
            start_point = calculate_point(0, 0, time_scale, effort_scale)  # Start from origin
        else:
            start_point = calculate_point(times[i - 1], efforts[i - 1], time_scale, effort_scale)
        end_point = calculate_point(times[i], efforts[i], time_scale, effort_scale)
        visual.Line(win, start=start_point, end=end_point, lineWidth=4, lineColor=red).draw()

    draw_all_stimuli([calibration_text])
    core.wait(0.01)  # Short wait to prevent overwhelming the CPU
    win.flip()


# calibration of hand grippers for 3 trials
# takes the average of average effort in a half-second window around the peak effort of trials 2 and 3
def do_calibration(win, mouse, info, gv, DUMMY, mp, calibration_txt, welcome_txt, calibration_done_txt, next_button):
    graph_start_x = -300
    graph_base_y = -280
    graph_length = 600  # Total length of the x-axis
    graph_height = 400  # Total height of the y-axis

    max_efforts = []  # List to store max_trial_effort for each trial
    efforts = []  # List to store current trial's effort values
    times = []  # List to store current trial's time values
    gripper_zero_baseline = 0
    effort_trace = []

    # Display initial instructions
    calibration_txt.text = "Calilbration in process! Do not touch the hand gripper."
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
                effort = (mouse.getPos()[1] - mouse_y_start) / 100
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
                effort = (mouse.getPos()[1] - mouse_y_start) / 100
            else:
                current_effort = mp.sample()[0]
                effort = current_effort - gripper_zero_baseline
                effort_trace.append(effort)
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
    info['max_effort_baseline_corrected'] = max_effort - gripper_zero_baseline
    info['effort_trace'] = '"' + json.dumps(effort_trace) + '"'

    welcome_txt.text = f"Well done!"
    draw_all_stimuli([welcome_txt])
    win.flip(), exit_q(), core.wait(2)

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
info = do_calibration(win, mouse, info, gv, DUMMY, mp, calibration_txt, welcome_txt, calibration_done_txt, next_button)
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
instructions4_txt.draw(), win.flip(), exit_q(), core.wait(1)

# actual trials
for trial in range(gv['max_n_trials']):
    if trial > 0 and trial % gv['n_trials_per_block'] == 0:
        break_txt = visual.TextStim(win=win, text='You have completed ' + str(info['trial_count']) + ' out of ' +
                                                  str(gv['max_n_trials']) + ' trials. \n\n Take a break if you like.',
                                    height=60, pos=[0, 40], color='white', wrapWidth=800, font='Monospace')
        stimuli = [break_txt, next_button, continue_button_txt]
        display_instructions(stimuli, mouse)
    info = do_trial(win, mouse, info, gv, DUMMY, mp, effort_outline, effort_fill, effort_text, reward_text,
                    accept_button,
                    accept_button_txt, reject_button, reject_button_txt, countdown_txt)
    info['trial_count'] += 1
    dataline = ','.join([str(info[v]) for v in log_vars])
    datafile.write(dataline + '\n')
    datafile.flush()
    info['reward_offer'] = info['next_reward_offer']
    info['effort_offer'] = info['next_effort_offer']
core.wait(0.5)

# save data
info['end_date'] = data.getDateStr()
dataline = ','.join([str(info[v]) for v in log_vars])
datafile.write(dataline + '\n')
datafile.flush()

# thank you
thanks_txt = visual.TextStim(win=win, text='You earned ' + str(info['total_reward']) + ' points. \n\nThank you for '
                                                                                       'completing the study!',
                             height=70, pos=[0, 40], color='white', font='Monospace')
thanks_txt.draw()
win.flip(), exit_q()
print(info['total_reward'])
core.wait(6)

# close window
win.close()
core.quit()
