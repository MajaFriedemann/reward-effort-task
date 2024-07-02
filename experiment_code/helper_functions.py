"""
helper functions for main.py and gripper_calibration.py

Maja Friedemann 2024
"""

###################################
# IMPORT PACKAGES
###################################
import random
from psychopy import gui, visual, core, data, event, core
import pandas as pd
import numpy as np
import serial


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


def draw_all_stimuli(win, stimuli, wait=0.01):
    """
    draw all stimuli, flip window, wait (default wait time is 0.01)
    """
    flattened_stimuli = [stim for sublist in stimuli for stim in (sublist if isinstance(sublist, list) else [sublist])]  # flatten the list of stimuli to accommodate nested lists
    for stimulus in flattened_stimuli:
        stimulus.draw()
    win.flip(), exit_q(win), core.wait(wait)


def check_button(win, buttons, stimuli, mouse):
    """
    check for button hover and click for multiple buttons.
    return the button object that was clicked and the response time.
    """
    draw_all_stimuli(win, stimuli, 0.2)
    response_timer = core.Clock()  # Start the response timer
    button_glows = [visual.Rect(win, width=button.width+15, height=button.height+15, pos=button.pos, fillColor=button.fillColor, opacity=0.5) for button in buttons]

    while True:  # Use an infinite loop that will break when a button is clicked
        for button, button_glow in zip(buttons, button_glows):
            if button.contains(mouse):  # check for hover
                button_glow.draw()  # hover, draw button glow
            if mouse.isPressedIn(button):  # check for click
                response_time = response_timer.getTime()  # Get the response time
                core.wait(0.5)  # add delay to provide feedback of a click
                return button, response_time  # return the button that was clicked and the response time

        draw_all_stimuli(win, stimuli)  # redraw stimuli and check again


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
        pos=(-2, -50),
        size=(340, 300)
    )

    # EFFORT BAR
    outline = visual.Rect(
        win,
        width=gv['effort_bar_width']+6,
        height=gv['effort_bar_height']+6,
        pos=(0, -36),
        fillColor='black',
    )

    # EFFORT TARGET
    target_height = gv['effort_bar_height'] * trial_effort / 100
    target = visual.Rect(
        win,
        width=gv['effort_bar_width'],
        height=target_height,
        pos=(0, -36 - (gv['effort_bar_height'] - target_height) / 2),
        fillColor=convert_rgb_to_psychopy([250, 243, 62]),
    )

    # EFFORT TEXT
    effort_text = visual.TextStim(
        win,
        text=f'{trial_effort}% \nEFFORT',
        height=28,
        pos=(200, -20),
        color='white',
        bold=True,
        font='Monospace',
        alignHoriz='center'
    )

    # STARS/METEORS
    x_range = (-250, 250)  # x-coordinate range for stars/meteors
    y_range = (150, 455)  # y-coordinate range for stars/meteors
    min_distance = 24  # Minimum distance between stars/meteors to avoid overlap
    positions = generate_random_positions(abs(trial_outcome), x_range, y_range, min_distance)

    # APPROACH BLOCK - STARS
    outcomes = []
    if action_type == 'approach':
        for pos in positions:
            star = draw_star(win, pos, size=10, color=[249, 244, 245])
            outcomes.append(star)

    # AVOID BLOCK - METEORS
    elif action_type == 'avoid':
        spaceship.ori = 180  # rotate the spaceship to face away from the meteors
        spaceship.pos = (0, -18)  # reposition the spaceship to accommodate the rotation
        for pos in positions:
            meteor = draw_meteor(win, pos, size=10, color=[249, 244, 245])
            outcomes.append(meteor)

    return spaceship, outline, target, effort_text, outcomes


def sample_effort(win, dummy, mouse, gripper, stimuli, trial_effort, target, gv):
    """
    Sample effort from gripper or mouse, zero_baseline and max_strength corrected.
    Effort needs to exceed a defined level for one consecutive second to be successful.
    If success is not achieved within a set time window, the trial is considered a failure.
    Outputs success/failure, the complete effort trace, and the average effort expended during the successful time window.
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
        pos=(0, -106),  # Position at the bottom of the outline
        fillColor=convert_rgb_to_psychopy([243, 88, 19], alpha=0.7)
    )
    stimuli.append(target)
    stimuli.append(dynamic_bar)

    while not success and not trial_failed:
        if trial_start_time.getTime() > gv['time_limit']:  # check if max time allowed has passed
            break  # exit the loop if the trial is considered a failure

        if dummy:
            effort_expended = mouse.getPos()[1]  # vertical movement
        else:
            effort_expended = (gripper.sample()[0] - gv['gripper_zero_baseline']) / gv['max_strength'] * 100
        effort_trace.append(effort_expended)
        dynamic_height = min(max(0, effort_expended), 100) * (138 / 100)
        dynamic_bar.height = dynamic_height
        dynamic_bar.pos = (0, -106 + (dynamic_height / 2))  # Adjust position to ensure bottom alignment
        draw_all_stimuli(win, stimuli)
        if effort_expended > trial_effort:
            if success_time is None:
                success_time = trial_start_time.getTime()  # mark the time when effort first exceeds target
                temp_effort_trace = [effort_expended]  # start tracking from this point
            else:
                temp_effort_trace.append(effort_expended)  # continue tracking
            if trial_start_time.getTime() - success_time >= gv['effort_duration']:  # check if it's been over a second
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


def animate_success(win, spaceship, outcomes, target, outline, points, action_type):
    """
    Animate the success outcome for either approach or avoid blocks, including displaying points.
    """
    frames = 30  # Number of frames for the animation
    points_text = visual.TextStim(
        win,
        text=f'+{points} POINTS!' if action_type == 'approach' else f'{points} POINTS!',
        height=50,
        pos=(0, 130),
        color=convert_rgb_to_psychopy([250, 243, 62]),
        bold=True,
        font='Monospace',
        alignHoriz='center'
    )
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
        draw_all_stimuli(win, stimuli)

    draw_all_stimuli(win, [points_text])
    core.wait(3)  # Hold the final frame for a few seconds


def animate_failure_or_reject(win, spaceship, outline, target, outcomes, points, action_type):
    """
    Animate the failure outcome for either approach or avoid blocks, showing negative consequences.
    """
    frames = 30  # Number of frames for the animation
    points_text = visual.TextStim(
        win,
        text=f'{points} POINTS!',
        height=50,
        pos=(0, 130),
        color=convert_rgb_to_psychopy([250, 243, 62]),
        bold=True,
        font='Monospace',
        alignHoriz='center'
    )

    for frame in range(frames):
        update_opacity([spaceship, outline, target] + outcomes, frame, frames)
        if action_type == 'avoid':
            for outcome in outcomes:
                outcome.pos = (
                    outcome.pos[0],
                    outcome.pos[1] - (frame / frames) * 50
                )
        stimuli = [spaceship, outline, target] + outcomes
        draw_all_stimuli(win, stimuli)

    draw_all_stimuli(win, [points_text])
    core.wait(3)  # Hold the final frame for a few seconds


def get_rating(win, mouse, attention_focus):
    """
    Get a rating for heart rate of reward rate from the participant using a slider.
    """
    slider = visual.Slider(win,
                           ticks=(1, 2, 3),
                           labels=["Low", "", "High"],
                           pos=(0, -20),
                           size=(500, 70), units="pix", flip=True, style='slider', granularity=0, labelHeight=25)
    slider.tickLines.sizes = (1, 70)

    slider_marker = visual.ShapeStim(
        win=win,
        vertices=((0, -33), (0, 33)),
        lineWidth=8,
        pos=(0, 0),
        closeShape=False,
        lineColor=convert_rgb_to_psychopy([250, 243, 62]),
    )

    slider_question_text = visual.TextStim(
        win,
        text=f'Considering your recent {attention_focus} rate, how does it compare to your average {attention_focus} rate during the experiment?',
        height=35,
        pos=(0, 170),
        color='white',
        bold=True,
        font='Monospace',
        alignHoriz='center'
    )

    while not slider.rating:
        # restrict slider marker to the range of slider
        if mouse.getPos()[0] > (slider.size[0] / 2):
            slider_marker.pos = ((slider.size[0] / 2), slider.pos[1])
        elif mouse.getPos()[0] < -(slider.size[0] / 2):
            slider_marker.pos = (-(slider.size[0] / 2), slider.pos[1])
        else:
            slider_marker.pos = (mouse.getPos()[0], slider.pos[1])
        slider.draw()
        slider_question_text.draw()
        slider_marker.draw()
        win.flip()

    rating = 1 - (slider.size[0] / 2 - slider_marker.pos[0]) / slider.size[0]
    return rating