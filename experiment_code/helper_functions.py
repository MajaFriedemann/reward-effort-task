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


def check_button(win, buttons, stimuli, mouse):
    """
    check for button hover and click for multiple buttons.
    return the button object that was clicked.
    """
    draw_all_stimuli(win, stimuli, 0.2)
    button_glows = [visual.Rect(win, width=button.width+15, height=button.height+15, pos=button.pos, fillColor=button.fillColor, opacity=0.5) for button in buttons]

    while True:  # Use an infinite loop that will break when a button is clicked
        for button, button_glow in zip(buttons, button_glows):
            if button.contains(mouse):  # check for hover
                button_glow.draw()  # hover, draw button glow
            if mouse.isPressedIn(button):  # check for click
                core.wait(0.5)  # add delay to provide feedback of a click
                return button  # return the button that was clicked

        draw_all_stimuli(win, stimuli)  # redraw stimuli and check again



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


def generate_trial_schedule(n_trials_per_combination, effort_levels, outcome_mean_magnitude_levels, outcome_uncertainty_levels, block_types, n_trials_per_block):
    """
    generate a schedule of trials organized into mini-blocks, alternating between block types.
    """
    trials = []
    for block_type in block_types:
        block_type_trials = []
        for eff in effort_levels:
            for mean in outcome_mean_magnitude_levels:
                for unc in outcome_uncertainty_levels:
                    for _ in range(n_trials_per_combination):
                        trial = {
                            'effort': eff,
                            'mean_magnitude': mean,
                            'uncertainty': unc,
                            'block_type': block_type
                        }
                        block_type_trials.append(trial)

        block_type_trials = pd.DataFrame(block_type_trials).sample(frac=1).reset_index(drop=True)  # shuffle trials within each block type

        # Split into blocks
        for i in range(0, len(block_type_trials), n_trials_per_block):
            block = block_type_trials.iloc[i:i + n_trials_per_block]
            if not block.empty:
                trials.append(block)

    # Interleave blocks between block types
    trial_schedule = pd.DataFrame()
    while trials:
        for block_type in block_types:
            for i, block in enumerate(trials):
                if block.iloc[0]['block_type'] == block_type:
                    trial_schedule = pd.concat([trial_schedule, block], ignore_index=True)
                    trials.pop(i)  # Remove the block from trials using its index
                    break  # Exit the loop to start with the next block type

    return trial_schedule


def trial_stimuli(win, effort_level, outcome_mean_magnitude, outcome_uncertainty, outcome_mean_max, block_type):
    """
    Generate the heights of 4 stacks of coins based on the mean magnitude and the type of uncertainty,
    and return them as visual.Rect objects stacked to represent coins. For 'avoid' blocks, the coins are aligned
    to the top of the outline, whereas for 'approach' blocks, they are aligned to the bottom.
    Also generate the effort bar and return it as visual.Rect object.
    """
    # COIN STACKS
    scaling_factor = 20  # scaling factor for the height of the coins
    coin_height = (outcome_mean_max + 4) * scaling_factor / (outcome_mean_max + 4)  # height of one coin
    if outcome_uncertainty == 'safe':
        heights = [outcome_mean_magnitude, outcome_mean_magnitude, outcome_mean_magnitude, outcome_mean_magnitude]
    elif outcome_uncertainty == '25/50/25':
        heights = [outcome_mean_magnitude - 4, outcome_mean_magnitude, outcome_mean_magnitude, outcome_mean_magnitude + 4]
    elif outcome_uncertainty == '50/50':
        heights = [outcome_mean_magnitude - 4, outcome_mean_magnitude - 4, outcome_mean_magnitude + 4, outcome_mean_magnitude + 4]
    else:
        raise ValueError('Invalid uncertainty type')
    random.shuffle(heights)  # randomize the order of bars
    outlines = []
    coin_stacks = []
    for i, height in enumerate(heights):
        coins = []
        for coin_index in range(height):
            if block_type == 'avoid':
                # For 'avoid', align coins to the top of the outline and set the background colour.
                win.color = tuple([(x / 127.5) - 1 for x in [135, 45, 11]])
                coin_pos_y = ((outcome_mean_max + 4) * scaling_factor) - (coin_height / 2 + coin_height * coin_index) - 60
            else:
                # For 'approach', align coins to the bottom of the outline and set the background colour.
                win.color = tuple([(x / 127.5) - 1 for x in [64, 83, 27]])
                coin_pos_y = (coin_height / 2 + coin_height * coin_index) - 60
            coin = visual.Rect(win,
                               width=70,
                               height=coin_height,
                               pos=[150 + 90 * i, coin_pos_y],
                               fillColor='gold',
                               lineColor='black',
                               lineWidth=2
                               )
            coins.append(coin)
        outline = visual.Rect(win,
                              width=90,
                              height=(outcome_mean_max + 4) * scaling_factor + 2,
                              pos=[150 + 90 * i, ((outcome_mean_max + 4) * scaling_factor) / 2 - 60],
                              lineColor='white',
                              lineWidth=3
                              )
        outlines.append(outline)
        coin_stacks.extend(coins)

    # EFFORT BAR
    bar_elements = []
    bar_pos_x = -400  # x position where the left side of the effort bar should start
    outline = visual.Rect(
        win,
        width=100 * 3,
        height=80 + 2,
        pos=(bar_pos_x + (100 * 3) / 2, 135),
        lineColor='white',
        lineWidth=5
    )
    filled_bar = visual.Rect(
        win,
        width=effort_level * 3,
        height=80,
        pos=(bar_pos_x + (effort_level * 3) / 2, 135),
        fillColor='white'
    )
    effort_text = 'EFFORT: {}%'.format(effort_level)
    text = visual.TextStim(
        win,
        text=effort_text,
        height=26,
        pos=(bar_pos_x, 200),
        color='white',
        bold=True,
        font='Monospace',
        alignHoriz='left'
    )
    bar_elements.extend([outline, filled_bar, text])

    return outlines + coin_stacks + bar_elements



