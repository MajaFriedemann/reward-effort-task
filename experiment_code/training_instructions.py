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
        "When you're ready, press SPACE."
    )
    big_txt.draw()
    instructions_txt.draw()
    win.flip()
    event.waitKeys(keyList=['space'])  # show instructions until space is pressed
    hf.exit_q(win)
    event.clearEvents()

    # Calibrate hand gripper
    instructions_txt.text = (
        "In this task, you will use a hand gripper to power a spaceship.\n\n"
        "Before we start your training, we must recalibrate this equipment. "
        "Therefore, please keep your hands clear of the hand gripper for now.\n\n"
        "Press SPACE to begin the calibration process."
    )
    instructions_txt.draw()
    win.flip()
    event.waitKeys(keyList=['space'])  # show instructions until space is pressed
    hf.exit_q(win)
    event.clearEvents()


def instructions_2(win, green_button, button_txt, instructions_txt, instructions_top_txt, big_txt, heart_rate_stimulus,
                   reward_rate_stimulus, mouse, gv):
    # Task overview
    instructions_txt.text = (
        "Excellent! Calibration is complete.\n\n"
        "In this task, you'll pilot a spaceship through the cosmos, "
        "encountering stars and meteors. Each of these encounters will require you to make a decision "
        "on your space journey."
        "\n\nPress SPACE to continue."
    )
    instructions_txt.draw()
    win.flip()
    event.waitKeys(keyList=['space'])  # show instructions until space is pressed
    hf.exit_q(win)
    event.clearEvents()

    # Block types
    instructions_txt.text = (
        "There are two types of encounters:\n\n"
        "1. In approach encounters, you'll face clouds of stars. More stars mean higher potential rewards. "
        "If you choose to accept the encounter with a left-click, it becomes a mission where you must exert effort to approach the stars and collect the reward. "
        "Rejecting the encounter with a right-click or failing to exert the required effort during the mission results in no reward.\n\n"
        "2. In avoid encounters, you'll face meteor fields. More meteors indicate a greater potential loss. "
        "If you accept the encounter with a left-click, it becomes a mission where you must exert effort to avoid the meteors and evade the loss. "
        "Rejecting the encounter with a right-click or failing to exert the required effort during the mission results in a loss."
        "\n\nPress SPACE to continue."
    )
    instructions_txt.draw()
    win.flip()
    event.waitKeys(keyList=['space'])  # show instructions until space is pressed
    hf.exit_q(win)
    event.clearEvents()

    # Effort
    instructions_txt.text = (
        f"When you accept an encounter with a left-click, squeeze the gripper to power your spaceship. "
        f"Your goal is to reach the target power level as quickly as possible. "
        f"Once at target, maintain the power for 1 second until your spaceship starts moving. "
        f"You have {gv['time_limit']} seconds for each mission attempt. Therefore, starting too slow may result in mission failure.\n\n"
        f"Choose which encounters to accept wisely to not run out of energy whilst maximising your rewards and minimising your losses!"
        "\n\nPress SPACE to continue."
    )
    instructions_txt.draw()
    win.flip()
    event.waitKeys(keyList=['space'])  # show instructions until space is pressed
    hf.exit_q(win)
    event.clearEvents()

    # Monetary reward
    instructions_txt.text = (
        f"In the real task, you will start your adventure with a base reward.\n"
        "At the end of your adventure, we'll randomly select 10 encounters (5 star clouds, 5 meteor fields), and "
        "your choices and performance in these encounters will adjust your final reward."
        "\n\nPress SPACE to continue."
    )
    instructions_txt.draw()
    win.flip()
    event.waitKeys(keyList=['space'])  # show instructions until space is pressed
    hf.exit_q(win)
    event.clearEvents()

    # Ratings
    instructions_txt.text = (
        "During your space adventure, you'll occasionally need to report on two key metrics:\n\n\n\n"
        "\n\nWhen prompted, consider your recent experiences in the context of your overall average experiences during your adventure."
        "\n\nPress SPACE to continue."
    )
    heart_rate_text = visual.TextStim(win, text="• Your current heart rate\n\n\n", pos=instructions_txt.pos + 10,
                                      height=instructions_txt.height)
    reward_rate_text = visual.TextStim(win, text="\n• Your current reward rate\n", pos=instructions_txt.pos + 10,
                                       height=instructions_txt.height)
    stimuli = [instructions_txt, heart_rate_text, reward_rate_text, heart_rate_stimulus,
               reward_rate_stimulus]
    hf.draw_all_stimuli(win, stimuli)
    event.waitKeys(keyList=['space'])  # show instructions until space is pressed
    event.clearEvents()

    instructions_txt.text = (
        "An icon in the top right corner of the screen will act as a cue, reminding you whether you are currently tracking your reward or heart rate.\n\n"
        "In avoid blocks, even though you are losing points, you should still use the complete scale from low to high reward rate.\n"
        "Consider your reward rate in the current context: if the loss is comparatively small, you may still have a high reward rate in that instance."
        "\n\nPress SPACE to continue."
    )
    instructions_txt.draw()
    win.flip()
    event.waitKeys(keyList=['space'])  # show instructions until space is pressed
    hf.exit_q(win)
    event.clearEvents()

    # Quiz
    instructions_top_txt.pos = [0, 200]
    big_txt.pos = [0, 150]
    instructions_txt.text = (
        "Let's make sure you're ready! \n\nAnswer the following questions \nto show you know how the task works."
    )
    instructions_txt.draw()
    win.flip()
    hf.exit_q(win)
    event.waitKeys(keyList=['space'])  # show instructions until space is pressed
    event.clearEvents()

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
        ("How do you power your spaceship?", ["1. Squeeze the gripper", "2. Press a button", "3. Shout"]),
        ("What do you do in an approach encounter?", ["1. Avoid meteors", "2. Approach stars", "3. Do nothing"]),
        ("What happens if you reject an avoid encounter?", ["1. Gain a reward", "2. No change", "3. Experience a loss"]),
        ("What do more meteors indicate?", ["1. Higher potential reward", "2. Greater potential loss", "3. Easier mission"]),
        ("What happens if you fail to exert the required effort during an approach encounter?",
         ["1. No reward is given", "2. You still get a reward", "3. You lose points"]),
        ("How do you reject an encounter?", ["1. Left-click", "2. Right-click", "3. Double-click"])
    ]

    incorrect_questions = []

    def ask_question(question, options, correct_option):
        instructions_top_txt.text = question
        button_1_txt.text = options[0]
        button_2_txt.text = options[1]
        button_3_txt.text = options[2]
        stimuli = [instructions_top_txt, button_1, button_1_txt, button_2, button_2_txt, button_3, button_3_txt]
        hf.draw_all_stimuli(win, stimuli)

        keys = event.waitKeys(keyList=['1', '2', '3'])
        response = keys[0]
        if response == '1':
            selected_option = 0
        elif response == '2':
            selected_option = 1
        elif response == '3':
            selected_option = 2

        if selected_option == correct_option:
            big_txt.text = "Correct!"
            instructions_txt.text = "\n\n\n\n\n\nPress SPACE to continue."
        else:
            big_txt.text = f"Incorrect!"
            instructions_txt.text = f"\n\n\n\n\n\n\n\nThe question was: '{question}'\n\nThe correct answer is: '{options[correct_option]}'. \n\nPress SPACE to continue."
            incorrect_questions.append((question, options, correct_option))

        stimuli = [big_txt, instructions_txt]
        hf.draw_all_stimuli(win, stimuli)
        event.waitKeys(keyList=['space'])
        hf.exit_q(win)
        event.clearEvents()

    # Ask all initial questions
    for question, options in quiz_questions:
        ask_question(question, options, 0)  # assuming correct answer is option 0 for all questions

    # Re-ask incorrect questions
    while incorrect_questions:
        question, options, correct_option = incorrect_questions.pop(0)
        ask_question(question, options, correct_option)

    # Start
    instructions_top_txt.pos = [0, 300]
    instructions_txt.text = (
        "Great job!\n\nLet's dive into some practice trials!\n\nThe points from this training session won't count towards your monetary reward, so feel free to explore: "
        "Try out accepting or rejecting offers, and see what happens when you successfully execute or fail to meet the required effort levels."
        "\n\nPress SPACE to start."
    )
    instructions_txt.draw()
    win.flip()
    event.waitKeys(keyList=['space'])  # show instructions until space is pressed
    hf.exit_q(win)
    event.clearEvents()


