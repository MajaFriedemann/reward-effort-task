###################################
# IMPORT PACKAGES
###################################
import os
import numpy as np
from psychopy import gui, visual, core, data, event, monitors
from mpydev import BioPac
import json


###################################
# FUNCTIONS
###################################
# allow exiting the experiment by pressing q when we are in full screen mode
def exit_q(win, key_list=None):
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

# draw all stimuli, flip window, wait (default wait time is 0)
def draw_all_stimuli(win, stimuli, wait=0):
    for stimulus in stimuli:
        stimulus.draw()
    exit_q(), win.flip(), core.wait(wait)
