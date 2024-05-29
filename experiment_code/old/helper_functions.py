"""
THIS IS NOW IN 'OLD' BECAUSE I WAS USING THE MONEY STACK REWARD STIMULI
NOW WE USE AN ANIMATION AND HAVE DIFFERENT REWARD LEVELS, EFFORT LEVELS, REWARD UNCERTAINTY

helper functions for main.py and gripper_calibration.py

Maja Friedemann 2024
"""

###################################
# IMPORT PACKAGES
###################################
import random
from psychopy import gui, visual, core, data, event
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


from psychopy import core  # Ensure this import is at the top of your script

def check_button(win, buttons, stimuli, mouse):
    """
    Check for button hover and click for multiple buttons.
    Return the button object that was clicked and the response time.
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
    """
    if dummy:
        strength = (mouse.getPos()[1] - zero_baseline) / 80 # vertical movement
    else:
        strength = gripper.sample()[0] - zero_baseline
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


def trial_stimuli(win, effort_level, outcome_mean_magnitude, outcome_uncertainty, outcome_mean_max, block_type, gv):
    """
    Generate the heights of 4 stacks of coins based on the mean magnitude and the type of uncertainty,
    and return them as visual.Rect objects stacked to represent coins. For 'avoid' blocks, the coins are aligned
    to the top of the outline, whereas for 'approach' blocks, they are aligned to the bottom.
    Also generate the effort bar and return it as visual.Rect object.
    """
    # COIN STACKS
    coin_height = (outcome_mean_max + gv['uncertain_point_difference']) * gv['coin_scaling_factor'] / (outcome_mean_max + gv['uncertain_point_difference'])  # height of one coin
    if outcome_uncertainty == 'safe':
        heights = [outcome_mean_magnitude, outcome_mean_magnitude, outcome_mean_magnitude, outcome_mean_magnitude]
    elif outcome_uncertainty == '25/50/25':
        heights = [outcome_mean_magnitude - gv['uncertain_point_difference'], outcome_mean_magnitude, outcome_mean_magnitude, outcome_mean_magnitude + gv['uncertain_point_difference']]
    elif outcome_uncertainty == '50/50':
        heights = [outcome_mean_magnitude - gv['uncertain_point_difference'], outcome_mean_magnitude - gv['uncertain_point_difference'], outcome_mean_magnitude + gv['uncertain_point_difference'], outcome_mean_magnitude + gv['uncertain_point_difference']]
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
                win.color = convert_rgb_to_psychopy(gv['avoid_block_colour'])
                coin_pos_y = ((outcome_mean_max + gv['uncertain_point_difference']) * gv['coin_scaling_factor']) - (coin_height / 2 + coin_height * coin_index) + gv['coin_pos_y']
            else:
                # For 'approach', align coins to the bottom of the outline and set the background colour.
                win.color = convert_rgb_to_psychopy(gv['approach_block_colour'])
                coin_pos_y = (coin_height / 2 + coin_height * coin_index) + gv['coin_pos_y']
            coin = visual.Rect(win,
                               width=gv['coin_distance_x']-20,
                               height=coin_height,
                               pos=[gv['coin_pos_x'] + gv['coin_distance_x'] * i, coin_pos_y],
                               fillColor='gold',
                               lineColor='black',
                               lineWidth=2
                               )
            coins.append(coin)
        outline = visual.Rect(win,
                              width=gv['coin_distance_x'],
                              height=(outcome_mean_max + gv['uncertain_point_difference']) * gv['coin_scaling_factor'] + 2,
                              pos=[gv['coin_pos_x']  + gv['coin_distance_x'] * i, ((outcome_mean_max + gv['uncertain_point_difference']) * gv['coin_scaling_factor']) / 2 + gv['coin_pos_y'] ],
                              lineColor='white',
                              lineWidth=3
                              )
        outlines.append(outline)
        coin_stacks.extend(coins)

    # EFFORT BAR
    bar_elements = []
    outline = visual.Rect(
        win,
        width=100 * gv['effort_scaling_factor'],
        height=gv['bar_height'] + 2,
        pos=(gv['bar_pos_x'] + (100 * gv['effort_scaling_factor']) / 2, gv['bar_pos_y']),
        lineColor='white',
        lineWidth=5
    )
    filled_bar = visual.Rect(
        win,
        width=effort_level * gv['effort_scaling_factor'],
        height=gv['bar_height'],
        pos=(gv['bar_pos_x'] + (effort_level * gv['effort_scaling_factor']) / 2, gv['bar_pos_y']),
        fillColor='white'
    )
    effort_text = 'EFFORT: {}%'.format(effort_level)
    text = visual.TextStim(
        win,
        text=effort_text,
        height=26,
        pos=(gv['bar_pos_x'], gv['bar_pos_y'] + 65),
        color='white',
        bold=True,
        font='Monospace',
        alignHoriz='left'
    )
    bar_elements.extend([outline, filled_bar, text])

    return outlines, coin_stacks, bar_elements, heights


def sample_effort(win, dummy, mouse, gripper, zero_baseline, max_strength, effort, stimuli, gv):
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
        width=effort * gv['effort_scaling_factor'],
        height=gv['bar_height'],
        pos=(gv['bar_pos_x'] + (effort_expended * gv['effort_scaling_factor']) / 2, gv['bar_pos_y']),
        fillColor=convert_rgb_to_psychopy([255, 113, 91]),
        opacity=0.9
    )
    stimuli.append(dynamic_bar)

    while not success and not trial_failed:
        if trial_start_time.getTime() > 8:  # Check if max time allowed has passed
            break  # Exit the loop if the trial is considered a failure

        if dummy:
            effort_expended = (mouse.getPos()[0] - zero_baseline)  # horizontal movement
        else:
            effort_expended = (gripper.sample()[0] - zero_baseline) / max_strength * 100
        effort_trace.append(effort_expended)
        dynamic_width = min(max(0, effort_expended * gv['effort_scaling_factor']), 100 * gv['effort_scaling_factor'])
        dynamic_bar.width = dynamic_width
        dynamic_bar.pos = (gv['bar_pos_x'] + dynamic_width / 2, gv['bar_pos_y'])
        draw_all_stimuli(win, stimuli)

        # Track effort for potential success duration
        if effort_expended > effort:
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


def handle_outcome_accept_approach(win, result, heights, outlines, left_side_txt, instructions_top_txt, coin_stacks):
    """
    Handle the outcome of an accepted 'approach' block.
    """
    if result == 'success':
        selected_stack_index = random.randint(0, 3)  # randomly select one of the four stacks of coins
        selected_stack_height = heights[selected_stack_index]  # get the number of coins of the selected stack
        selected_stack_outline = outlines[selected_stack_index]
        # selected_stack_outline.lineColor = 'white' # highlight the selected stack
        selected_stack_outline.lineWidth = 6
        points = selected_stack_height
        instructions_top_txt.text = "Well done!"
        left_side_txt.text = str(points) + ' points'
        stimuli = [coin_stacks, instructions_top_txt, selected_stack_outline, left_side_txt]
    else:
        points = -1
        instructions_top_txt.text = "You did not reach the required effort."
        left_side_txt.text = str(points) + ' points'
        stimuli = [instructions_top_txt, left_side_txt]
    draw_all_stimuli(win, stimuli)
    core.wait(5)
    return points


def handle_outcome_accept_avoid(win, result, instructions_top_txt, left_side_txt):
    """
    Handle the outcome of an accepted 'avoid' block.
    """
    if result == 'success':
        points = 0
        instructions_top_txt.text = "Well done! You avoided the loss."
    else:
        points = -14
        instructions_top_txt.text = "You did not reach the required effort."
    left_side_txt.text = str(points) + ' points'
    stimuli = [instructions_top_txt, left_side_txt]
    draw_all_stimuli(win, stimuli)
    core.wait(5)
    return points


def handle_outcome_reject_approach(win, instructions_top_txt, left_side_txt):
    """
    Handle the outcome of a rejected 'approach' block.
    """
    points = 0
    instructions_top_txt.text = "You rejected the offer."
    left_side_txt.text = str(points) + ' points'
    stimuli = [instructions_top_txt]
    draw_all_stimuli(win, stimuli)
    core.wait(5)
    return points


def handle_outcome_reject_avoid(win, heights, outlines, left_side_txt, instructions_top_txt, coin_stacks):
    """
    Handle the outcome of a rejected 'avoid' block.
    """
    selected_stack_index = random.randint(0, 3)  # randomly select one of the four stacks of coins
    selected_stack_height = heights[selected_stack_index]  # get the number of coins of the selected stack
    selected_stack_outline = outlines[selected_stack_index]
    # selected_stack_outline.lineColor = 'white' # highlight the selected stack
    selected_stack_outline.lineWidth = 6
    points = 0 - selected_stack_height
    instructions_top_txt.text = "You rejected the offer."
    left_side_txt.text = str(points) + ' points'
    stimuli = [coin_stacks, instructions_top_txt, selected_stack_outline, left_side_txt]
    draw_all_stimuli(win, stimuli)
    core.wait(5)
    return points