"""
training instructions for main.py

Maja Friedemann 2024
"""
import helper_functions as hf
from psychopy import core, visual, event


def instructions_1(win, green_button, button_txt, instructions_txt, instructions_top_txt, big_txt, mouse, gv):
    # Welcome
    big_txt.text = "Welcome!"
    instructions_txt.text = (
        "\n\n\n\nIn this training session, you will learn about the task \nand do a few practice trials!\n\n "
        "When you're ready, click 'NEXT'."
    )
    stimuli = [green_button, button_txt, big_txt, instructions_txt]
    hf.draw_all_stimuli(win, stimuli)
    hf.check_button(win, [green_button], stimuli, mouse)

    # Calibrate hand gripper
    instructions_txt.text = (
        "In this task, you will use a hand gripper to power a spaceship.\n\n"
        "Before we start your training, we must recalibrate this equipment. "
        "Therefore, please keep your hands clear of the hand gripper for now.\n\n"
        "Click 'NEXT' to begin the calibration process."
    )
    stimuli = [green_button, button_txt, instructions_txt]
    hf.draw_all_stimuli(win, stimuli)
    hf.check_button(win, [green_button], stimuli, mouse)


def instructions_2(win, green_button, button_txt, instructions_txt, instructions_top_txt, big_txt, heart_rate_stimulus,
                   reward_rate_stimulus, mouse, gv):
    # Task overview
    instructions_txt.text = (
        "Excellent! Calibration is complete.\n\n"
        "In this task, you'll pilot a spaceship through the cosmos, "
        "encountering stars and meteors. Each of these encounters will require you to make a decision "
        "on your space journey."
    )
    stimuli = [green_button, button_txt, instructions_txt]
    hf.draw_all_stimuli(win, stimuli)
    hf.check_button(win, [green_button], stimuli, mouse)

    # Block types
    instructions_txt.text = (
        "There are two types of encounters:\n\n"
        "1. In approach encounters, you'll face clouds of stars. More stars mean higher potential rewards. "
        "If you choose to accept the encounter, it becomes a mission where you must exert effort to approach the stars and collect the reward. "
        "Rejecting the encounter or failing to exert the required effort during the mission results in no reward.\n\n"
        "2. In avoid encounters, you'll face meteor fields. More meteors indicate a greater potential loss. "
        "If you accept the encounter, it becomes a mission where you must exert effort to avoid the meteors and evade the loss. "
        "Rejecting the encounter or failing to exert the required effort during the mission results in a loss."
    )
    stimuli = [green_button, button_txt, instructions_txt]
    hf.draw_all_stimuli(win, stimuli)
    hf.check_button(win, [green_button], stimuli, mouse)

    # Effort
    instructions_txt.text = (
        f"When you accept an encounter, squeeze the gripper to power your spaceship. "
        f"Your goal is to reach the target power level as quickly as possible. "
        f"Once at target, maintain the power for 1 second until your spaceship starts moving. "
        f"You have {gv['time_limit']} seconds for each mission attempt. Therefore, starting too slow may result in mission failure.\n\n"
        f"Choose which encounters to accept wisely to not run out of energy whilst maximising your rewards and minimising your losses!"
    )
    stimuli = [green_button, button_txt, instructions_txt]
    hf.draw_all_stimuli(win, stimuli)
    hf.check_button(win, [green_button], stimuli, mouse)

    # Monetary reward
    instructions_txt.text = (
        f"In the real task, you will start your adventure with a base reward.\n"
        "At the end of your adventure, we'll randomly select 10 encounters (5 star clouds, 5 meteor fields), and "
        "your choices and performance in these encounters will adjust your final reward."
        "Each point is worth 10p."
    )
    stimuli = [green_button, button_txt, instructions_txt]
    hf.draw_all_stimuli(win, stimuli)
    hf.check_button(win, [green_button], stimuli, mouse)

    # Ratings
    instructions_txt.text = (
        "During your space adventure, you'll occasionally need to report on two key metrics:\n\n\n\n\n\n"
        "When prompted, consider your recent experiences in the context of your overall average experiences during your adventure."
    )
    heart_rate_text = visual.TextStim(win, text="• Your current heart rate\n\n", pos=instructions_txt.pos,
                                      height=instructions_txt.height)
    reward_rate_text = visual.TextStim(win, text="\n• Your current reward rate", pos=instructions_txt.pos,
                                       height=instructions_txt.height)
    stimuli = [green_button, button_txt, instructions_txt, heart_rate_text, reward_rate_text, heart_rate_stimulus,
               reward_rate_stimulus]
    hf.draw_all_stimuli(win, stimuli)
    hf.check_button(win, [green_button], stimuli, mouse)

    # Quiz
    instructions_top_txt.pos = [0, 200]
    big_txt.pos = [0, 150]
    instructions_txt.text = (
        "Let's make sure you're ready! \n\nAnswer the following questions \nto show you know how the task works."
    )
    stimuli = [green_button, button_txt, instructions_txt]
    hf.draw_all_stimuli(win, stimuli)
    hf.check_button(win, [green_button], stimuli, mouse)

    button_1 = visual.Rect(win=win, units="pix", width=500, height=60, pos=(0, 100), fillColor='white')
    button_1_txt = visual.TextStim(win=win, text='Option A', height=25, pos=button_1.pos, color='black', bold=True,
                                   font='Arial')
    button_2 = visual.Rect(win=win, units="pix", width=500, height=60, pos=(0, 0), fillColor='white')
    button_2_txt = visual.TextStim(win=win, text='Option B', height=25, pos=button_2.pos, color='black', bold=True,
                                   font='Arial')
    button_3 = visual.Rect(win=win, units="pix", width=500, height=60, pos=(0, -100), fillColor='white')
    button_3_txt = visual.TextStim(win=win, text='Option C', height=25, pos=button_3.pos, color='black', bold=True,
                                   font='Arial')

    quiz_questions = [
        ("How do you power your spaceship?", ["Squeeze the gripper", "Press a button", "Shout"], button_1),
        ("What do you do in an approach encounter?", ["Avoid meteors", "Approach stars", "Do nothing"], button_2),
        ("What happens if you reject an avoid encounter?", ["Gain a reward", "No change", "Experience a loss"],
         button_3),
        ("What do more meteors indicate?", ["Higher potential reward", "Greater potential loss", "Easier mission"],
         button_2),
        ("What happens if you fail to exert the required effort during an approach encounter?",
         ["No reward is given", "You still get a reward", "You lose points"], button_1),
        ("How much is each point worth?", ["5p", "10p", "20p"], button_2)
    ]

    incorrect_questions = []

    def ask_question(question, options, correct_button):
        instructions_top_txt.text = question
        button_1_txt.text = options[0]
        button_2_txt.text = options[1]
        button_3_txt.text = options[2]
        stimuli = [instructions_top_txt, button_1, button_1_txt, button_2, button_2_txt, button_3, button_3_txt]
        hf.draw_all_stimuli(win, stimuli)
        clicked_button, response_time = hf.check_button(win, [button_1, button_2, button_3], stimuli, mouse)

        # Determine the correct answer text based on the correct button
        if correct_button == button_1:
            correct_option_text = options[0]
        elif correct_button == button_2:
            correct_option_text = options[1]
        elif correct_button == button_3:
            correct_option_text = options[2]

        if clicked_button == correct_button:
            big_txt.text = "Correct!"
            instructions_txt.text = " "
        else:
            big_txt.text = f"Incorrect!"
            instructions_txt.text = f"\n\n\n\n\n\nThe question was: '{question}'\n\nThe correct answer is: '{correct_option_text}'."
            incorrect_questions.append((question, options, correct_button))

        stimuli = [big_txt, green_button, button_txt, instructions_txt]
        hf.draw_all_stimuli(win, stimuli)
        hf.check_button(win, [green_button], stimuli, mouse)

    # Ask all initial questions
    for question, options, correct_button in quiz_questions:
        ask_question(question, options, correct_button)

    # Re-ask incorrect questions
    while incorrect_questions:
        question, options, correct_button = incorrect_questions.pop(0)
        ask_question(question, options, correct_button)

    # Start
    instructions_top_txt.pos = [0, 300]
    instructions_txt.text = (
        "Great job!\n\nLet's dive into some practice trials!\n\nThe points from this training session won't count towards your monetary reward, so feel free to explore: "
        "Try out accepting or rejecting offers, and see what happens when you successfully execute or fail to meet the required effort levels."
    )
    stimuli = [green_button, button_txt, instructions_txt]
    hf.draw_all_stimuli(win, stimuli)
    hf.check_button(win, [green_button], stimuli, mouse)


