"""
helper functions for main.py and gripper_calibration.py

Maja Friedemann 2024
"""

from psychopy import visual, core, event

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
    for stimulus in stimuli:
        stimulus.draw()
    win.flip(), exit_q(win), core.wait(wait)


def check_button(win, button, stimuli, mouse):
    """
    check for button hover and click
    """
    draw_all_stimuli(win, stimuli, 0.2)
    button_glow = visual.Rect(win, width=button.width+10, height=button.height+10, pos=button.pos, fillColor=button.fillColor, opacity=0.5)
    while not mouse.isPressedIn(button):
        if button.contains(mouse): # check for hover
            button_glow.draw() # hover, draw button glow
        draw_all_stimuli(win, stimuli, 0.2) # check for mouse click and hove, wait time to not overwhelm CPU
    core.wait(0.5) # clicked button, move on, feels more natural with short wait for button to react


def convert_rgb_to_psychopy(rgb):
    """
    turn rgp colour code to colour format that PsychoPy needs
    """
    return tuple([(x / 127.5) - 1 for x in rgb])



