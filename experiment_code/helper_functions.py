"""
helper functions for main.py and gripper_calibration.py

Maja Friedemann 2024
"""

###################################
# IMPORT PACKAGES
###################################
import random
from psychopy import gui, visual, core, data, event, core, clock
import pandas as pd
import numpy as np
import serial


###################################
# CLASSES
###################################
class EEGConfig:
    def __init__(self, triggers, send_triggers):
        self.triggers = triggers
        self.send_triggers = send_triggers

    def send_trigger(self, code):
        if self.send_triggers:
            print('write function to trigger code ' + str(code))
        else:
            print('would send trigger: ' + str(code))


###################################
# FUNCTIONS
###################################
def exit_q(win, key_list=None):
    """
    allow exiting the experiment by pressing q when we are in full screen mode
    this just checks if anything has been pressed - it doesn't wait
    """
    if key_list is None:
        key_list = ['q']
    keys = event.getKeys(keyList=key_list)
    res = len(keys) > 0
    if res:
        if 'q' in keys:
            win.close()
            core.quit()
    return res


def draw_all_stimuli(win, stimuli, wait=0.0):
    """
    draw all stimuli, flip window, wait
    """
    flattened_stimuli = [stim for sublist in stimuli for stim in (sublist if isinstance(sublist, list) else [sublist])]  # flatten the list of stimuli to accommodate nested lists
    for stimulus in flattened_stimuli:
        stimulus.draw()
    win.flip(), exit_q(win), core.wait(wait)


def check_button(win, buttons, stimuli, mouse):
    """
    Check for button hover and click for multiple buttons.
    Return the button object that was clicked and the response time.
    """
    response_timer = core.Clock()  # Start the response timer
    button_glows = [
        visual.Rect(win, width=button.width + 15, height=button.height + 15, pos=button.pos, fillColor=button.fillColor,
                    opacity=0.5) for button in buttons]
    while True:  # Use an infinite loop that will break when a button is clicked
        for button, button_glow in zip(buttons, button_glows):
            if button.contains(mouse):  # check for hover
                button_glow.draw()  # hover, draw button glow
            else:
                button.draw()  # draw the button if not hovered
        draw_all_stimuli(win, stimuli)  # redraw stimuli and check again
        # check for mouse press using mouse.getPressed
        if mouse.getPressed()[0]:  # Left mouse button is pressed
            for button in buttons:
                if button.contains(mouse):
                    response_time = response_timer.getTime()  # Get the response time
                    core.wait(0.2)  # add delay to provide feedback of a click
                    return button, response_time  # return the button that was clicked and the response time
        # flush the event queue to avoid stale events
        event.clearEvents()
        mouse.clickReset()


def check_mouse_click(win, mouse):
    mouse.clickReset()
    while True:
        buttons, times = mouse.getPressed(getTime=True)
        if buttons[0]:
            return 'left', times[0]
        if buttons[2]:
            return 'right', times[2]
        # Add a small delay to avoid high CPU usage
        exit_q(win)
        core.wait(0.01)


def check_key_press(win, key_list):
    while True:
        keys = event.getKeys(timeStamped=True)
        for key, time in keys:
            if key in key_list:
                return key, time
        exit_q(win)
        event.clearEvents()
        core.wait(0.01)


def convert_rgb_to_psychopy(color, alpha=1.0):
    """
    Convert RGB values to a range suitable for PsychoPy (-1 to 1) and include alpha for transparency.
    """
    return [(c / 127.5) - 1 for c in color] + [alpha]


def sample_strength(dummy, mouse, gripper, zero_baseline):
    """
    sample strength from gripper or mouse, zero baseline corrected
    used in gripper_calibration.py
    """
    if dummy:
        strength = (mouse.getPos()[1] - zero_baseline) / 80 # vertical movement
    else:
        strength = gripper.sample()[0] - zero_baseline
    core.wait(0.01)
    return strength


def generate_random_positions(num_stars, x_range, y_range, min_distance):
    """
    Generate random, non-overlapping positions for stars within a given x and y range
    """
    positions = []
    for _ in range(num_stars):
        while True:
            pos = (
                np.random.uniform(x_range[0], x_range[1]),
                np.random.uniform(y_range[0], y_range[1])
            )
            if all(np.linalg.norm(np.array(pos) - np.array(existing_pos)) >= min_distance for existing_pos in positions):
                positions.append(pos)
                break
    return positions


def draw_star(win, pos, size=30, color=None):
    """
    Draw a star at a given position with a given size and color
    """
    if color is None:
        color = [255, 255, 255]  # white
    vertices = [
        (0, 1), (0.2, 0.2), (1, 0.2),
        (0.3, -0.1), (0.5, -0.8), (0, -0.3),
        (-0.5, -0.8), (-0.3, -0.1), (-1, 0.2),
        (-0.2, 0.2)
    ]
    vertices = [(x * size, y * size) for x, y in vertices]
    star = visual.ShapeStim(
        win=win,
        vertices=vertices,
        fillColor=convert_rgb_to_psychopy(color),
        lineColor=convert_rgb_to_psychopy(color),
        pos=pos
    )
    return star


def draw_meteor(win, pos, size=30, color=None):
    """
    Draw a meteor at a given position with a given size and color
    """
    if color is None:
        color = [255, 255, 255]  # white
    # Vertices for a meteor-like shape
    vertices = [
        (0, 1), (0.3, 0.8), (0.7, 0.7), (1, 0.2),
        (0.8, 0), (0.5, -0.2), (0.3, -0.5), (0, -0.8),
        (-0.3, -0.5), (-0.5, -0.2), (-0.8, 0), (-1, 0.2),
        (-0.7, 0.7), (-0.3, 0.8)
    ]
    vertices = [(x * size, y * size) for x, y in vertices]
    meteor = visual.ShapeStim(
        win=win,
        vertices=vertices,
        fillColor=convert_rgb_to_psychopy(color),
        lineColor=convert_rgb_to_psychopy(color),
        pos=pos
    )
    return meteor


def draw_trial_stimuli(win, trial_effort, trial_outcome, action_type, gv):
    """
    Draw outcome and effort stimuli for the trial offer
    """
    # SPACESHIP
    spaceship = visual.ImageStim(
        win,
        image='pictures/spaceship.png',
        pos=(-2, -125),
        size=(340, 300)
    )

    # EFFORT BAR
    outline = visual.Rect(
        win,
        width=gv['effort_bar_width']+6,
        height=gv['effort_bar_height']+6,
        pos=(0, -111),
        fillColor='black',
    )

    # EFFORT TARGET
    target_height = gv['effort_bar_height'] * trial_effort / 100
    target = visual.Rect(
        win,
        width=gv['effort_bar_width'],
        height=target_height,
        pos=(0, -111 - (gv['effort_bar_height'] - target_height) / 2),
        fillColor=convert_rgb_to_psychopy([250, 243, 62]),
    )

    # EFFORT TEXT
    effort_text = visual.TextStim(
        win,
        text=f'{trial_effort}% \nEFFORT',
        height=28,
        pos=(200, -95),
        color='white',
        bold=True,
        font='Arial',
        alignText='center'
    )

    # STARS/METEORS
    x_range = (-250, 250)  # x-coordinate range for stars/meteors
    y_range = (75, 380)
    min_distance = 24  # Minimum distance between stars/meteors to avoid overlap
    positions = generate_random_positions(abs(trial_outcome), x_range, y_range, min_distance)

    # APPROACH BLOCK - STARS
    outcomes = []
    if action_type == 'approach':
        for pos in positions:
            star = draw_star(win, pos, size=10, color=[255, 255, 255])
            outcomes.append(star)

    # AVOID BLOCK - METEORS
    elif action_type == 'avoid':
        spaceship.ori = 180  # rotate the spaceship to face away from the meteors
        spaceship.pos = (0, -93)  # Reposition the spaceship to accommodate the rotation
        for pos in positions:
            meteor = draw_meteor(win, pos, size=10, color=[255, 255, 255])
            outcomes.append(meteor)

    return spaceship, outline, target, effort_text, outcomes


def sample_effort(win, dummy, mouse, gripper, stimuli, trial_effort, target, gv, EEG_config, effort_state):
    """
    Sample effort from gripper or mouse, zero_baseline and max_strength corrected.
    Effort needs to exceed a defined level for one consecutive second to be successful.
    If success is not achieved within a set time window, the trial is considered a failure.
    Outputs success/failure, the complete effort trace, and the average effort expended during the successful time window.
    When global effort state is shifted, we manipulate the visual display of the effort and the threshold crossing (the shift will be subtracted from the dynamic effort bar).
    However, the effort trace will still save the actual effort.
    """
    effort_trace = []
    average_effort = 0
    temp_effort_trace = []  # Temporary list to track efforts during success duration
    success = False
    trial_failed = False
    success_time = None  # Track the time when effort first exceeds the target
    trial_start_time = core.Clock()  # Initialize a clock to measure total trial time
    dynamic_bar = visual.Rect(
        win,
        width=gv['effort_bar_width'],
        height=0,  # Start with a height of 0
        pos=(0, -181),  # Position at the bottom of the outline
        fillColor=convert_rgb_to_psychopy([243, 88, 19], alpha=0.7)
    )
    stimuli.append(target)
    stimuli.append(dynamic_bar)
    effort_started = False
    threshold_crossed = False

    while not success and not trial_failed:
        if trial_start_time.getTime() > gv['time_limit']:  # check if max time allowed has passed
            break  # exit the loop if the trial is considered a failure

        if dummy:
            effort_expended = mouse.getPos()[1]  # vertical movement
            if effort_expended < 0:
                effort_expended = 0
        else:
            effort_expended = (gripper.sample()[0] - gv['gripper_zero_baseline']) / gv['max_strength'] * 100

        # if effort state is 'shifted', adjust the effort for visual display and threshold crossing
        actual_effort_expended = effort_expended  # preserve the actual effort value
        if effort_state == 'shifted':
            actual_effort_expended_level = actual_effort_expended / 10
            shifted_effort_expended_level = np.sqrt((gv['assumed_k'] * actual_effort_expended_level ** 2 + gv['net_value_shift']) / gv['assumed_k'])
            shifted_effort_expended = shifted_effort_expended_level * 10
            extra_effort_required = shifted_effort_expended - actual_effort_expended
            effort_expended -= extra_effort_required

        effort_trace.append(actual_effort_expended)  # append the actual effort to the trace we are saving

        if effort_expended > gv['effort_started_threshold'] and not effort_started:
            effort_started = True
            EEG_config.send_trigger(EEG_config.triggers['effort_started'])

        dynamic_height = min(max(0, effort_expended), 100) * (138 / 100)
        dynamic_bar.height = dynamic_height
        dynamic_bar.pos = (0, -181 + (dynamic_height / 2))  # Adjust position to ensure bottom alignment
        draw_all_stimuli(win, stimuli)

        if effort_expended > (0.95*trial_effort):
            if not threshold_crossed:
                EEG_config.send_trigger(EEG_config.triggers['effort_threshold_crossed'])
                threshold_crossed = True

            if success_time is None:
                success_time = trial_start_time.getTime()  # mark the time when effort first exceeds target
                temp_effort_trace = [actual_effort_expended]  # start tracking the actual effort from this point
            else:
                temp_effort_trace.append(actual_effort_expended)  # continue tracking the actual effort

            if trial_start_time.getTime() - success_time >= gv['effort_duration']:  # check if it's been over a second
                EEG_config.send_trigger(EEG_config.triggers['effort_success'])
                success = True
                average_effort = sum(temp_effort_trace) / len(temp_effort_trace) if temp_effort_trace else 0
        else:
            success_time = None  # reset if effort drops below target
            temp_effort_trace.clear()  # clear temporary efforts since condition was not met

    result = "success" if success else "failure"
    effort_time = trial_start_time.getTime()
    return result, effort_trace, average_effort, effort_time  # return outcome, the complete effort trace, the average of successful efforts, and the time taken to complete the trial


def update_opacity(stimuli, frame, frames):
    opacity_factor = 1 - (frame / frames)
    for stim in stimuli:
        stim.opacity = opacity_factor


def update_position(stimuli, delta_pos):
    for stim in stimuli:
        stim.pos += delta_pos


def animate_success(win, spaceship, outcomes, target, outline, points, action_type, EEG_config, gv, cue):
    """
    Animate the success outcome for either approach or avoid blocks, including displaying points.
    """
    frames = 30  # Number of frames for the animation
    points_text = visual.TextStim(
        win,
        text=f'+ {points}' if action_type == 'approach' else f'{points}',
        height=60,
        pos=(0, 0),
        color='white',
        bold=True,
        font='Arial',
        alignText='center',
        wrapWidth=800,
    )

    if gv['training']:
        if action_type == 'approach':
            points_text.text = f'+ {points} POINTS \n\nYou reached the stars!'
        if action_type == 'avoid':
            points_text.text = f'{points} POINTS \n\nYou evaded the meteors!'
    else:
        pass

    flame = visual.ImageStim(
        win,
        image='pictures/flame.png',
        pos=(spaceship.pos[0], spaceship.pos[1]),
        size=(200, 200),
        ori=0 if action_type == 'approach' else 180
    )
    target.fillColor = convert_rgb_to_psychopy([243, 133, 19], alpha=0.95)
    move_delta = (0, 5) if action_type == 'approach' else (0, -5)
    flame_delta = (0, -170) if action_type == 'approach' else (0, 170)

    for frame in range(frames):
        update_position([spaceship, outline, target], move_delta)
        flame.pos = (spaceship.pos[0], spaceship.pos[1] + flame_delta[1])
        stimuli = [spaceship, outline, target, flame] + outcomes
        draw_all_stimuli(win, stimuli, 0.008)

    draw_all_stimuli(win, [points_text])
    if action_type == 'approach':
        EEG_config.send_trigger(EEG_config.triggers['outcome_presentation_approach_success'])
    elif action_type == 'avoid':
        EEG_config.send_trigger(EEG_config.triggers['outcome_presentation_avoid_success'])
    core.wait(gv['outcome_presentation_time'])  # Hold the final frame for a few seconds
    if gv['training']:
        core.wait(2)


def animate_failure_or_reject(win, spaceship, outline, target, outcomes, points, action_type, result, EEG_config, gv, cue):
    """
    Animate the failure outcome for either approach or avoid blocks, showing negative consequences.
    """
    frames = 30  # Number of frames for the animation
    points_text = visual.TextStim(
        win,
        text=f'{points}',
        height=60,
        pos=(0, 0),
        color='white',
        bold=True,
        font='Arial',
        alignText='center',
        wrapWidth=800
    )
    if points < 0:
        points_text.text = f'- {abs(points)}'
    if gv['training']:
        if result == 'failure':
            points_text.text = f'{points} POINTS \n\nYou failed to exert the required effort!'
            if points < 0:
                points_text.text = f'- {abs(points)} POINTS \n\nYou failed to exert the required effort!'
        if result == 'reject':
            points_text.text = f'{points} POINTS \n\nYou rejected the offer!'
            if points < 0:
                points_text.text = f'- {abs(points)} POINTS \n\nYou rejected the offer!'
    else:
        pass

    for frame in range(frames):
        update_opacity([spaceship, outline, target] + outcomes, frame, frames)
        if action_type == 'avoid':
            for outcome in outcomes:
                outcome.pos = (
                    outcome.pos[0],
                    outcome.pos[1] - (frame / frames) * 50
                )
        stimuli = [spaceship, outline, target] + outcomes
        draw_all_stimuli(win, stimuli, 0.008)

    draw_all_stimuli(win, [points_text])
    if action_type == 'approach':
        if result == 'failure':
            EEG_config.send_trigger(EEG_config.triggers['outcome_presentation_approach_failure'])
        elif result == 'reject':
            EEG_config.send_trigger(EEG_config.triggers['outcome_presentation_approach_reject'])
    elif action_type == 'avoid':
        if result == 'failure':
            EEG_config.send_trigger(EEG_config.triggers['outcome_presentation_avoid_failure'])
        elif result == 'reject':
            EEG_config.send_trigger(EEG_config.triggers['outcome_presentation_avoid_reject'])
    core.wait(gv['outcome_presentation_time'])  # Hold the final frame for a few seconds
    if gv['training']:
        core.wait(2)


def get_rating(win, attention_focus, image, gv):
    """
    Get a rating for heart rate or reward rate from the participant using a discrete slider controlled by keys.
    Outputs the rating, the response time, and the random start position.
    """

    # Define the slider with 11 ticks and vertical lines
    ticks = list(range(11))  # 11 ticks
    labels = ["Low"] + [""] * 9 + ["High"]

    slider = visual.Slider(win,
                           ticks=ticks,
                           labels=labels,
                           pos=(0, 0),
                           size=(600, 70),
                           units="pix",
                           flip=True,
                           style=['radio'],
                           granularity=1,
                           labelHeight=23,
                           color='white',  # Color of the slider and labels
                           markerColor='blue',  # Blue marker color
                           )

    # Start the slider at a random position
    start_pos = random.randint(0, 10)
    slider.markerPos = start_pos

    slider_question_text = visual.TextStim(
        win,
        text=f'How is your current {attention_focus} rate?',
        height=40,
        pos=(0, 220),
        color='white',
        bold=True,
        font='Arial',
        alignText='center',
        wrapWidth=1000
    )

    image.pos = [0, 150]

    # Start timing the response
    response_timer = clock.Clock()

    while True:
        slider.draw()
        slider_question_text.draw()
        image.draw()
        win.flip()

        keys = event.waitKeys(keyList=gv['response_keys'] + ['space'])

        if 'j' in keys:
            slider.markerPos = max(0, slider.markerPos - 1)
        elif 'k' in keys:
            slider.markerPos = min(10, slider.markerPos + 1)

        # To finalize the rating, the 'space' key is used to confirm the selection
        if 'space' in keys:
            break

    # Stop the timer and get the response time
    response_time = response_timer.getTime()

    # Calculate the rating based on the marker position
    rating = slider.markerPos / 10
    rating = round(rating, 3)
    core.wait(0.5)

    return rating, response_time, start_pos



def calculate_bonus_payment(all_trials, gv):
    """
    Calculate the bonus payment based on the points earned in randomly selected trials.
    """
    # Separate trials into approach and avoid blocks
    approach_trials = [trial for trial in all_trials if trial['block_action_type'] == 'approach']
    avoid_trials = [trial for trial in all_trials if trial['block_action_type'] == 'avoid']

    # Ensure there are at least 5 trials in each category
    if len(approach_trials) < 5 or len(avoid_trials) < 5:
        raise ValueError("Not enough trials in one or both categories to select 5 trials each.")

    # Randomly select 5 trials from each block type
    selected_approach_trials = random.sample(approach_trials, 5)
    selected_avoid_trials = random.sample(avoid_trials, 5)

    # Sum up the points from the selected trials
    total_points = sum(trial['points'] for trial in selected_approach_trials + selected_avoid_trials)

    # Calculate the total bonus based on points
    points_per_penny = 0.01  # Each point is worth 1 penny
    bonus_from_points = total_points * points_per_penny

    # Calculate the final payment
    final_bonus_payment = gv['base_bonus_payment'] + bonus_from_points

    return final_bonus_payment

