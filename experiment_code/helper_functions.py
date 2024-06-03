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


def convert_rgb_to_psychopy(rgb):
    """
    turn rgp colour code to colour format that PsychoPy needs
    """
    return tuple([(x / 127.5) - 1 for x in rgb])


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


# Function to draw a star
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


def perturb_positions(positions, max_perturbation):
    perturbed_positions = []
    for pos in positions:
        perturbed_pos = (pos[0] + np.random.uniform(-max_perturbation, max_perturbation),
                         pos[1] + np.random.uniform(-max_perturbation, max_perturbation))
        perturbed_positions.append(perturbed_pos)
    return perturbed_positions


def trial_stimuli(win, gv):
    """
    Draw outcome and effort stimuli for the trial offer
    """
    stimulus_elements = []
    # SPACESHIP
    spaceship = visual.ImageStim(
        win,
        image='pictures/spaceship.png',
        pos=(-2, -23),
        size=(340, 300)
    )
    # EFFORT BAR
    outline = visual.Rect(
        win,
        width=gv['effort_bar_width'],
        height=gv['effort_bar_height'],
        pos=(0, 0),
        fillColor='black',
        lineColor='darkblue',
        lineWidth=4
    )
    # TARGET LINE
    target_y_pos = 0 - (gv['effort_bar_height']/ 2) + (gv['effort_level'] / 100) * gv['effort_bar_height']
    target_line = visual.Line(
        win,
        start=(-gv['effort_bar_width'] / 2, target_y_pos),
        end=(gv['effort_bar_width']/ 2, target_y_pos),
        lineColor="orangered",
        lineWidth=4
    )
    # EFFORT TEXT
    effort_text = visual.TextStim(
        win,
        text=f'EFFORT: {gv["effort_level"]}%',
        height=24,
        pos=(180, 60),
        color='white',
        bold=True,
        font='Monospace',
        alignHoriz='center'
    )
    # STARS
    predefined_positions = {
        1: [(0, 350)],
        2: [(-100, 320), (100, 300)],
        3: [(-100, 310), (100, 300), (0, 270)],
        4: [(-100, 340), (100, 320), (-100, 270), (100, 280)],
        5: [(-100, 340), (100, 310), (0, 290), (-100, 270), (100, 230)],
        6: [(-120, 350), (-40, 340), (40, 330), (120, 310), (-60, 270), (60, 280)],
        7: [(-120, 320), (-40, 330), (40, 320), (120, 310), (-80, 240), (0, 290), (80, 250)],
        8: [(-120, 330), (-40, 320), (40, 310), (120, 300), (-80, 260), (0, 280), (80, 250), (0, 270)],
        9: [(-120, 310), (-40, 330), (40, 320), (120, 300), (-80, 250), (0, 260), (80, 250), (-60, 210), (60, 220)],
        10: [(-120, 320), (-40, 300), (40, 340), (120, 340), (-80, 260), (0, 280), (80, 260), (-80, 210), (0, 240), (80, 220)],
        11: [(-120, 340), (-40, 320), (40, 310), (120, 300), (-80, 260), (0, 250), (80, 240), (-100, 240), (-20, 210), (60, 200), (100, 220)]
    }

    num_stars = 10
    num_stars = max(1, min(num_stars, 11))
    positions = predefined_positions[num_stars]
    positions = perturb_positions(positions, max_perturbation=5)
    for pos in positions:
        star = draw_star(win, pos, size=30, color=[227, 240, 155])
        stimulus_elements.append(star)

    stimulus_elements.extend([spaceship, outline, target_line, effort_text])
    return stimulus_elements


def sample_effort(win, dummy, mouse, gripper, stimuli, gv):
    """
    Sample effort from gripper or mouse, zero_baseline and max_strength corrected.
    Effort needs to exceed a defined level for one consecutive second to be successful.
    If success is not achieved within a set time window, the trial is considered a failure.
    Outputs success/failure, the complete effort trace, and the average effort expended during the successful time window.
    """
    effort_expended = 0
    effort_trace = []
    average_effort = 0
    temp_effort_trace = []  # Temporary list to track efforts during success duration
    success = False
    trial_failed = False
    success_time = None  # Track the time when effort first exceeds the target
    trial_start_time = core.Clock()  # Initialize a clock to measure total trial time
    dynamic_bar = visual.Rect(
        win,
        width=gv['effort_bar_width']-6,
        height=0,  # Start with a height of 0
        pos=(0, -70),  # Position at the bottom of the outline
        fillColor='lightsalmon'
    )
    target_y_pos = 0 - (gv['effort_bar_height'] / 2) + (gv['effort_level'] / 100) * gv['effort_bar_height']
    target_line = visual.Line(
        win,
        start=(-gv['effort_bar_width'] / 2, target_y_pos),
        end=(gv['effort_bar_width'] / 2, target_y_pos),
        lineColor="orangered",
        lineWidth=4
    )
    stimuli.append(dynamic_bar)
    stimuli.append(target_line)

    while not success and not trial_failed:
        if trial_start_time.getTime() > 20:  # Check if max time allowed has passed MAJA
            break  # Exit the loop if the trial is considered a failure

        if dummy:
            effort_expended = mouse.getPos()[1]  # vertical movement
        else:
            effort_expended = (gripper.sample()[0] - gv['gripper_zero_baseline']) / gv['max_strength'] * 100
        effort_trace.append(effort_expended)
        dynamic_height = min(max(0, effort_expended), 100) * (138 / 100)
        dynamic_bar.height = dynamic_height
        dynamic_bar.pos = (0, -70 + (dynamic_height / 2))  # Adjust position to ensure bottom alignment
        draw_all_stimuli(win, stimuli)

        # Track effort for potential success duration
        if effort_expended > gv['effort_level']:
            if success_time is None:
                success_time = trial_start_time.getTime()  # Mark the time when effort first exceeds target
                temp_effort_trace = [effort_expended]  # Start tracking from this point
            else:
                temp_effort_trace.append(effort_expended)  # Continue tracking
            if trial_start_time.getTime() - success_time >= 10.0:  # Check if it's been over a second MAJA
                success = True
                average_effort = sum(temp_effort_trace) / len(temp_effort_trace) if temp_effort_trace else 0
        else:
            success_time = None  # Reset if effort drops below target
            temp_effort_trace.clear()  # Clear temporary efforts since condition was not met

    result = "success" if success else "failure"
    return result, effort_trace, average_effort  # Return outcome, the complete effort trace, and the average of successful efforts

