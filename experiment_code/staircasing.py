###################################
# IMPORT PACKAGES
###################################
import os
import numpy as np
from psychopy import gui, visual, core, data, event
from mpydev import BioPac

###################################
# CONSTANTS AND CONFIGURATION
###################################
EXP_NAME = 'pgACC-TUS-staircase'
DATA_DIR = 'staircase_data'
MAX_TRIALS = 5
WINDOW_SIZE = [1920, 1080]
REWARD_INITIAL = 18
EFFORT_INITIAL = 6
K_ESTIMATE_INITIAL = 0.5

###################################
# HELPER FUNCTIONS
###################################
def create_directory(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)

def save_data(datafile, info):
    dataline = ','.join([str(info[v]) for v in info])
    datafile.write(dataline + '\n')
    datafile.flush()

def setup_info(expInfo):
    return {
        # Initialize the info dictionary with experiment info and initial values
    }

def setup_datafile(info):
    filename = os.path.join(DATA_DIR, f"{info['participant']}_{info['date']}.csv")
    datafile = open(filename, 'w')
    datafile.write(','.join(info.keys()) + '\n')
    return datafile

def create_stimuli(win):
    # Initialize and return a dictionary of stimuli
    return {}

###################################
# MAIN EXPERIMENT FUNCTIONS
###################################
def do_calibration(win, mouse, info, DUMMY, mp, calibration_text):
    graph_start_x = -200
    graph_base_y = -200
    graph_length = 400  # Total length of the x-axis
    graph_height = 250  # Total height of the y-axis

    max_efforts = []  # List to store max_trial_effort for each trial
    efforts = []  # List to store current trial's effort values
    times = []  # List to store current trial's time values

    # Display initial instructions
    calibration_text.text = "Do not touch the hand grippers!"
    draw_all_stimuli([calibration_text])
    win.flip(), exit_q(), core.wait(2)  # Display instructions for 2 seconds

    # Countdown: 3, 2, 1
    for countdown in range(3, 0, -1):
        calibration_text.text = str(countdown)
        draw_all_stimuli([calibration_text])
        # Save the mp.sample()[0] from second 3 as the gripper zero baseline
        if not DUMMY and countdown == 3:
            gripper_zero_baseline = mp.sample()[0]
            info['gripper_baseline'] = gripper_zero_baseline
        win.flip()
        core.wait(1)

    for trial in range(1, 4):  # Conduct 3 calibration trials
        prev_efforts = efforts.copy()  # Copy the previous trial's efforts
        prev_times = times.copy()  # Copy the previous trial's times
        efforts = []  # Reset the current trial's efforts
        times = []  # Reset the current trial's times
        # Display initial instructions
        if trial == 1:
            calibration_text.text = f"Trial {trial}: When ready, squeeze as hard as you can!"
        else:
            calibration_text.text = f"Trial {trial}: Try to squeeze harder than on your last trial!"
        visual.Line(win, start=(graph_start_x, graph_base_y), end=(graph_start_x + graph_length, graph_base_y),
                    lineWidth=2,
                    lineColor='white').draw()
        visual.Line(win, start=(graph_start_x, graph_base_y), end=(graph_start_x, graph_base_y + graph_height),
                    lineWidth=2,
                    lineColor='white').draw()
        draw_all_stimuli([calibration_text])
        win.flip()
        exit_q()
        core.wait(1)  # Short wait to ensure participant is ready

        # Wait for participant to start
        recording_started = False
        start_time = None
        mouse_y_start = mouse.getPos()[1]
        while not recording_started:
            if DUMMY:
                effort = mouse.getPos()[1] - mouse_y_start
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
                effort = mouse.getPos()[1] - mouse_y_start
            else:
                current_effort = mp.sample()[0]
                effort = current_effort - gripper_zero_baseline
            efforts.append(effort)
            current_time = core.getTime() - start_time
            times.append(current_time)

            # Draw the graph with the current and previous efforts
            draw_graph_with_efforts(win, graph_start_x, graph_base_y, graph_length, graph_height, prev_efforts,
                                    prev_times, efforts, times, calibration_text)

        # Calculate the length of a 1-second window and its boundaries
        max_effort_index = efforts.index(max(efforts))
        quarter_second_window_length = int((len(efforts) / recording_second_duration) / 4)
        window_start = max(0, max_effort_index - quarter_second_window_length)
        window_end = min(len(efforts), max_effort_index + quarter_second_window_length + 1)
        # Calculate the average effort within the 1-second window around the maximum effort
        max_trial_effort = sum(efforts[window_start:window_end]) / (window_end - window_start)
        max_efforts.append(max_trial_effort)

        # Rest period message
        calibration_text.text = "Trial completed. Relax for a moment."
        draw_graph_with_efforts(win, graph_start_x, graph_base_y, graph_length, graph_height, prev_efforts, prev_times,
                                efforts, times, calibration_text)
        core.wait(3)  # Rest period

    # Finish calibration
    # Calculate max_effort as the average of max_trial_effort for trials 2 and 3
    max_effort = sum(max_efforts[1:3]) / 2  # Trials 2 and 3
    info['max_effort_calibration_1'] = max_efforts[0]
    info['max_effort_calibration_2'] = max_efforts[1]
    info['max_effort_calibration_3'] = max_efforts[2]
    info['max_effort'] = max_effort

    calibration_text.text = f"Well done!"
    draw_all_stimuli([calibration_text])
    win.flip(), exit_q(), core.wait(3)

    return info

def perform_trial(win, mouse, info, DUMMY, mp, stimuli):
    # Implement the logic of a single trial here
    return info

def perform_trials(win, mouse, info, DUMMY, mp, stimuli, datafile):
    for trial in range(MAX_TRIALS):
        info = perform_trial(win, mouse, info, DUMMY, mp, stimuli)
        save_data(datafile, info)

def display_thank_you(win):
    thank_you_text = visual.TextStim(win, text='Thank you for participating!', height=70, pos=[0, 40], color='white')
    thank_you_text.draw()
    win.flip()
    core.wait(5)

def cleanup(win):
    win.close()
    core.quit()

def main():
    DUMMY = False  # set to True to use the mouse instead of hand grippers
    expInfo = gui.DlgFromDict(dictionary={}, title=EXP_NAME).dictionary
    if not expInfo:  # Dialog box was canceled
        return

    mp = BioPac("MP160", n_channels=2, samplerate=200, logfile="test", overwrite=True) if not DUMMY else None
    info = setup_info(expInfo)
    create_directory(DATA_DIR)
    datafile = setup_datafile(info)

    win = visual.Window(size=WINDOW_SIZE, fullscr=True, units='pix')
    stimuli = create_stimuli(win)

    info = do_calibration(win, event.Mouse(win=win), info, DUMMY, mp)
    perform_trials(win, event.Mouse(win=win), info, DUMMY, mp, stimuli, datafile)
    display_thank_you(win)

    cleanup(win)

if __name__ == "__main__":
    main()
