import json

from agents import validator, censor, writer, judge


def writer_judge_loop(writer_messages, judge_messages, user_prompt_history):
    """Run up to 3 writer→judge iterations and return an approved draft.

    If the judge rejects a draft, its feedback is fed back to the writer for
    the next iteration. judge_messages persists so the judge sees its own
    past verdicts. Returns None if no draft is approved after 3 attempts.
    """
    for i in range(3):
        draft = writer.run(writer_messages)
        writer_messages.append({"role": "assistant", "content": draft})

        print(f"Judging draft {i + 1}...")
        prompts_block = "\n".join(f"{n + 1}. {p}" for n, p in enumerate(user_prompt_history))
        judge_messages.append({
            "role": "user",
            "content": f"User requests so far (in order):\n{prompts_block}\n\nDraft to evaluate:\n\n{draft}",
        })
        raw = judge.run(judge_messages)
        result = json.loads(raw)

        # Drop "evaluation" from the judge's response — kept in logs but would bloat judge context across iterations.
        # evaluation is a field I defined in the Judge system prompt, to understand the judge's reasoning
        slim = json.dumps({"pass": result["pass"], "feedback": result.get("feedback", "")})
        judge_messages.append({"role": "assistant", "content": slim})
        if result["pass"]:
            return draft

        print(f"Judge requested revisions: {result['feedback']}")
        writer_messages.append({
            "role": "user",
            "content": f"Judge feedback: {result['feedback']}\n\nPlease revise the story.",
        })
    return None


def validate_and_censor_input(user_input, current_story, intake_log, is_revision):
    """Run validator then censor on the latest user input. Returns True if both passed.

    intake_log is shared between the two gates so they can interpret follow-ups
    after a rejection (e.g. "thrown out of a plane" gets rejected, but a follow-up
    "with a parachute, on his birthday, surprised by friends" reframes it as safe).
    The turn and both verdicts are appended to intake_log in place.
    """
    # Carry the current story so validator/censor can interpret follow-ups in context.
    turn = f"Current story: {current_story or '(none)'}\nUser input: {user_input}"
    intake_log.append({"role": "user", "content": turn})

    intake_label = "your revision" if is_revision else "your request"
    gates = [
        (f"Validating {intake_label}...", "validator", validator),
        ("Checking content is age-appropriate...", "censor", censor),
    ]
    for label, agent_name, agent in gates:
        print(label)
        raw = agent.run(intake_log)
        result = json.loads(raw)
        intake_log.append({"role": "assistant", "content": json.dumps({"agent": agent_name, **result})})
        if not result["pass"]:
            print(f"Hmm, I couldn't help with that — {result['feedback']}")
            return False
    return True


def combine_user_turns(intake_log, user_input):
    """Merge the intake's user inputs into one bullet-list message and clear the log.

    If only one user input accumulated (no prior rejections), returns user_input
    as-is. Either way the intake_log is cleared — both gates have approved at
    this point, so the back-and-forth is no longer needed downstream.
    """
    chain = [m["content"].split("\nUser input: ", 1)[1] for m in intake_log if m["role"] == "user"]
    intake_log.clear()
    if len(chain) > 1:
        bullets = "\n".join(f"- {ui}" for ui in chain)
        return f"The user refined their request through these turns (each refines the previous):\n{bullets}"
    return user_input


def write_story(effective_user_input, current_story, user_prompt_history, judge_messages, is_revision):
    """Run writer/judge loop + final censor, retrying with a safety hint up to 2 times.

    Returns the approved story (also printed for the user), or None if no draft
    passed both the judge and the final censor.
    """
    failure_message = (
        "Could not generate this revision; the previous story still stands. Try a different revision."
        if is_revision
        else "Could not generate a story for that prompt; please try a different one."
    )

    def build_writer_messages(safety_hint: str = "") -> list[dict]:
        # For a revision, seed the writer with the original prompt + current story for context.
        last = f"Revise the story: {effective_user_input}" if is_revision else effective_user_input
        if safety_hint:
            last += f"\n\n(Note: a previous attempt was flagged as inappropriate — {safety_hint}. Write a new, age-appropriate story that avoids this.)"
        if is_revision:
            return [
                {"role": "user", "content": user_prompt_history[0]},
                {"role": "assistant", "content": current_story},
                {"role": "user", "content": last},
            ]
        return [{"role": "user", "content": last}]

    writer_messages = build_writer_messages()
    print("Revising the story..." if is_revision else "Writing the story...")
    # Up to 2 attempts. If the final censor flags the story, restart with a safety hint.
    for attempt in range(2):
        story = writer_judge_loop(writer_messages, judge_messages, user_prompt_history)
        if story is None:
            print(failure_message)
            return None

        print("Final safety check on the revised story..." if is_revision else "Final safety check on the story...")
        # Final censor is single-shot — judges the story standalone, no history.
        censor_input = f"Source: writer story\n\n{story}"
        raw = censor.run([{"role": "user", "content": censor_input}])
        result = json.loads(raw)
        if result["pass"]:
            print(story)
            return story

        print(f"Safety check flagged the story: {result['feedback']} Writing a fresh story...")
        writer_messages = build_writer_messages(safety_hint=result["feedback"])

    print(failure_message)
    return None
