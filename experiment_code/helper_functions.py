"""
helper functions for main.py and gripper_calibration.py

Maja Friedemann 2024
"""

###################################
# IMPORT PACKAGES
###################################
import os
import csv
import json
import random
from psychopy import gui, visual, core, data, event
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


def check_button(win, button, stimuli, mouse):
    """
    check for button hover and click
    """
    draw_all_stimuli(win, stimuli, 0.2)
    button_glow = visual.Rect(win, width=button.width+15, height=button.height+15, pos=button.pos, fillColor=button.fillColor, opacity=0.5)
    while not mouse.isPressedIn(button):
        if button.contains(mouse): # check for hover
            button_glow.draw() # hover, draw button glow
        draw_all_stimuli(win, stimuli) # check for mouse click and hover
    core.wait(0.5) # clicked button, move on, feels more natural with short wait for button to react


def convert_rgb_to_psychopy(rgb):
    """
    turn rgp colour code to colour format that PsychoPy needs
    """
    return tuple([(x / 127.5) - 1 for x in rgb])


def sample_strength(DUMMY, mouse, gripper, gripper_zero_baseline, mouse_zero_baseline):
    """
    sample strength from gripper or mouse, zero baseline corrected
    """
    if DUMMY:
        strength = (mouse.getPos()[1] - mouse_zero_baseline) / 80
    else:
        strength = gripper.sample()[0] - gripper_zero_baseline
    core.wait(0.01)
    return strength


def generate_trial_schedule(n_trials_per_combination, effort_levels, outcome_mean_magnitude_levels, outcome_uncertainty_levels):
    """
    Generate a schedule of trials by crossing the specified levels for
    effort, reward expectation, and uncertainty, with each combination repeated
    as specified by n_trials_per_combination.
    """
    trials = []
    for eff in effort_levels:
        for mean in outcome_mean_magnitude_levels:
            for unc in outcome_uncertainty_levels:
                for _ in range(n_trials_per_combination):  # repeat addition for n_trials_per_combination times
                    trial = {
                        'effort': eff,
                        'mean_magnitude': mean,
                        'uncertainty': unc
                    }
                    trials.append(trial)

    trials_df = pd.DataFrame(trials)  # convert the list of trials to a DataFrame
    trials_df = trials_df.sample(frac=1).reset_index(drop=True)  # shuffle the trials

    return trials_df


def outcome_bars(win, outcome_mean_magnitude, outcome_uncertainty, outcome_mean_max):
    """
    Generate the heights of 4 bars based on the mean magnitude and the type of uncertainty,
    and return them as visual.Rect objects.
    """
    if outcome_uncertainty == 'safe':
        heights = [outcome_mean_magnitude, outcome_mean_magnitude, outcome_mean_magnitude, outcome_mean_magnitude]
    elif outcome_uncertainty == '25/50/25':
        heights = [outcome_mean_magnitude-4, outcome_mean_magnitude, outcome_mean_magnitude, outcome_mean_magnitude+4]
    elif outcome_uncertainty == '50/50':
        heights = [outcome_mean_magnitude-4, outcome_mean_magnitude-4, outcome_mean_magnitude+4, outcome_mean_magnitude+4]
    else:
        raise ValueError('Invalid uncertainty type')
    random.shuffle(heights)  # randomize the order of bars

    outlines = []
    filled_bars = []
    for i, height in enumerate(heights):
        outline = visual.Rect(win, width=71, height=(outcome_mean_max+4)*18, pos=[-380+71*i, ((outcome_mean_max+4)*18)/2-60], lineColor='white')
        filled_bar = visual.Rect(win, width=70, height=height*18, pos=[-380+71*i, (height*18)/2-60], fillColor='salmon', lineColor='white')
        outlines.append(outline)
        filled_bars.append(filled_bar)

    return outlines + filled_bars


def effort_bar(win, effort_level):
    bar_elements = []
    bar_pos_x = 50  # x position where the left side of the effort bar should start

    outline = visual.Rect(
        win,
        width=100 * 3,
        height=81,
        pos=(bar_pos_x + (100 * 3) / 2, 10),
        lineColor='white',
        lineWidth=7
    )

    filled_bar = visual.Rect(
        win,
        width=effort_level * 3,
        height=80,
        pos=(bar_pos_x + (effort_level * 3) / 2, 10),
        fillColor='yellow'
    )

    effort_text = 'EFFORT: {}%'.format(effort_level)
    text = visual.TextStim(
        win,
        text=effort_text,
        height=26,
        pos=(bar_pos_x, 75),
        color='white',
        bold=True,
        font='Monospace',
        alignHoriz='left'
    )

    bar_elements.extend([outline, filled_bar, text])
    return bar_elements

