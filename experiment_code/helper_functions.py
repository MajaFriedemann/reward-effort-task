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


def trial_stimuli(win, gv):
    """
    Draw outcome and effort stimuli for the trial offer
    """
    # SPACESHIP
    spaceship = visual.ImageStim(
        win,
        image='pictures/spaceship.png',
        pos=(0, -23),
        size=(340, 300)
    )
    # EFFORT BAR
    effort_elements = []
    outline = visual.Rect(
        win,
        width=65,
        height=140,
        pos=(0, 0),
        fillColor='white',
        lineColor='darkblue',
        lineWidth=4
    )
    # TARGET LINE
    target_y_pos = outline.pos[1] - (outline.height / 2) + (gv['effort_level'] / 100) * outline.height
    target_line = visual.Line(
        win,
        start=(-outline.width / 2, target_y_pos),
        end=(outline.width / 2, target_y_pos),
        lineColor='red',
        lineWidth=4
    )
    # EFFORT TEXT
    effort_text = visual.TextStim(
        win,
        text=f'EFFORT: {gv["effort_level"]}%',
        height=20,
        pos=(160, 70),
        color='white',
        bold=True,
        font='Monospace',
        alignHoriz='center'
    )
    effort_elements.extend([spaceship, outline, target_line, effort_text])
    return effort_elements


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
        width=65,
        height=140,
        pos=(0, 0),
        fillColor='green'
    )
    stimuli.append(dynamic_bar)

    while not success and not trial_failed:
        if trial_start_time.getTime() > 8:  # Check if max time allowed has passed
            break  # Exit the loop if the trial is considered a failure

        if dummy:
            effort_expended = mouse.getPos()[1] # vertical movement
        else:
            effort_expended = (gripper.sample()[0] - gv['gripper_zero_baseline']) / gv['max_strength'] * 100
        effort_trace.append(effort_expended)
        dynamic_height = min(max(0, effort_expended), 100)
        dynamic_bar.height = dynamic_height
        draw_all_stimuli(win, stimuli)

        # Track effort for potential success duration
        if effort_expended > gv['effort_level']:
            if success_time is None:
                success_time = trial_start_time.getTime()  # Mark the time when effort first exceeds target
                temp_effort_trace = [effort_expended]  # Start tracking from this point
            else:
                temp_effort_trace.append(effort_expended)  # Continue tracking
            if trial_start_time.getTime() - success_time >= 1.0:  # Check if it's been over a second
                success = True
                average_effort = sum(temp_effort_trace) / len(temp_effort_trace) if temp_effort_trace else 0
        else:
            success_time = None  # Reset if effort drops below target
            temp_effort_trace.clear()  # Clear temporary efforts since condition was not met

    result = "success" if success else "failure"
    return result, effort_trace, average_effort  # Return outcome, the complete effort trace, and the average of successful efforts

