###################################
# TRAINING SESSION INSTRUCTIONS
###################################
# Welcome
big_txt.text = "Welcome to the experiment!"
instructions_txt.text = "\n\n\n\n\nYou're about to begin a training session to familiarize yourself with the task. We'll guide you through each step.\n\nWhen you're ready to start, click 'NEXT'."
stimuli = [green_button, button_txt, big_txt, instructions_txt]
hf.draw_all_stimuli(win, stimuli)
hf.check_button(win, [green_button], stimuli, mouse)
EEG_config.send_trigger(EEG_config.triggers['training_start'])

# Introduce hand gripper
instructions_txt.text = ("In this experiment, you'll be using a hand gripper to exert effort.\n\n"
                         "The hand gripper is a small device that you'll squeeze with your dominant hand.\n\n"
                         "Before we begin, we need to calibrate the equipment to your individual strength.\n\n"
                         "Click 'NEXT' to proceed with the calibration.")
stimuli = [green_button, button_txt, instructions_txt]
hf.draw_all_stimuli(win, stimuli)
hf.check_button(win, [green_button], stimuli, mouse)

# Calibrate hand gripper
instructions_txt.text = ("For accurate calibration, please follow these steps:\n\n"
                         "1. Hold the gripper in your dominant hand.\n"
                         "2. When instructed, squeeze the gripper as hard as you can for 3 seconds.\n"
                         "3. Relax your hand when you see 'RELAX' on the screen.\n"
                         "4. We'll repeat this process 3 times to ensure accuracy.\n\n"
                         "Click 'NEXT' when you're ready to start the calibration.")
stimuli = [green_button, button_txt, instructions_txt]
hf.draw_all_stimuli(win, stimuli)
hf.check_button(win, [green_button], stimuli, mouse)

# CALIBRATE HAND GRIPPER (repeated 3 times)
for i in range(3):
    win.flip()
    instructions_top_txt.text = f"Calibration Round {i + 1} of 3"
    big_txt.text = "GET READY"
    hf.draw_all_stimuli(win, [instructions_top_txt, big_txt], 2)

    big_txt.text = "SQUEEZE!"
    hf.draw_all_stimuli(win, [instructions_top_txt, big_txt], 3)
    if not DUMMY:
        gv[f'max_force_{i + 1}'] = max(gripper.sample())

    big_txt.text = "RELAX"
    hf.draw_all_stimuli(win, [instructions_top_txt, big_txt], 2)

# Task overview
instructions_txt.text = ("Great job! Calibration is complete.\n\n"
                         "Now, let's learn about the task. In this experiment, you'll control a virtual spaceship.\n"
                         "Your goal is to fill the spaceship with fuel by exerting effort using the hand gripper.\n\n"
                         "The task consists of multiple trials, each presenting you with a choice.\n\n"
                         "Click 'NEXT' to learn about the different types of trials.")
stimuli = [green_button, button_txt, instructions_txt]
hf.draw_all_stimuli(win, stimuli, 1)
hf.check_button(win, [green_button], stimuli, mouse)

# Block types
instructions_txt.text = ("There are two types of trials in this task:\n\n"
                         "1. Approach Trials: You'll see a cloud of stars.\n"
                         "   - The number of stars represents the reward you can earn.\n"
                         "   - If you accept and successfully exert the required effort, you'll gain the reward.\n"
                         "   - If you reject or fail to exert enough effort, you'll get no reward.\n\n"
                         "2. Avoid Trials: You'll see a cloud of meteors.\n"
                         "   - The number of meteors represents a potential loss.\n"
                         "   - If you accept and successfully exert the required effort, you'll avoid the loss.\n"
                         "   - If you reject or fail to exert enough effort, you'll incur the loss.\n\n"
                         "Click 'NEXT' to continue.")
stimuli = [green_button, button_txt, instructions_txt]
hf.draw_all_stimuli(win, stimuli, 1)
hf.check_button(win, [green_button], stimuli, mouse)

# Trial structure
instructions_txt.text = ("Each trial follows this structure:\n\n"
                         "1. Offer: You'll see either stars (reward) or meteors (potential loss).\n"
                         "2. Decision: Choose to accept or reject the offer.\n"
                         "3. Effort: If accepted, squeeze the hand gripper to the required level.\n"
                         "4. Outcome: See whether you succeeded and your current score.\n\n"
                         "Click 'NEXT' to learn about the effort gauge.")
stimuli = [green_button, button_txt, instructions_txt]
hf.draw_all_stimuli(win, stimuli, 1)
hf.check_button(win, [green_button], stimuli, mouse)

# Effort gauge explanation
instructions_txt.text = ("During the effort phase, you'll see a vertical gauge on the screen:\n\n"
                         "- The gauge fills up as you squeeze the hand gripper.\n"
                         "- A horizontal line shows the required effort level.\n"
                         "- You must keep the gauge above this line for the entire duration.\n"
                         "- The duration is shown by a shrinking bar at the top of the screen.\n\n"
                         "Click 'NEXT' to continue.")
stimuli = [green_button, button_txt, instructions_txt]
hf.draw_all_stimuli(win, stimuli, 1)
hf.check_button(win, [green_button], stimuli, mouse)

# Monetary reward
instructions_txt.text = ("Your performance in this task translates to real money!\n\n"
                         "At the end of the experiment, we'll randomly select xx trials.\n"
                         "Your points from these trials will be converted into a monetary reward.\n\n"
                         "Each point is worth 1p. For example:\n"
                         "- If you have 100 points, you'll win £1\n"
                         "- If you have 500 points, you'll win £5\n\n"
                         "Click 'NEXT' to learn about the ratings.")
stimuli = [green_button, button_txt, instructions_txt]
hf.draw_all_stimuli(win, stimuli, 1)
hf.check_button(win, [green_button], stimuli, mouse)

# Ratings
instructions_txt.text = ("Throughout the experiment, we'll occasionally ask you about two things:\n\n"
                         "1. Your heart rate: How fast do you feel your heart is beating?\n"
                         "2. Your reward rate: How rewarding do you find the task at that moment?\n\n"
                         "When asked, consider your recent experiences compared to your overall average during the experiment.\n"
                         "You'll use a slider to indicate your response.\n\n"
                         "Click 'NEXT' to begin the training trials.")
stimuli = [green_button, button_txt, instructions_txt]
hf.draw_all_stimuli(win, stimuli, 1)
hf.check_button(win, [green_button], stimuli, mouse)

# Start training
big_txt.text = "Let's start the training!"
instructions_txt.text = ("You'll now complete a few practice trials to get familiar with the task.\n"
                         "Remember, this is just for practice. Ask questions if anything is unclear.\n\n"
                         "Good luck!")
stimuli = [big_txt, instructions_txt]
hf.draw_all_stimuli(win, stimuli, 5)