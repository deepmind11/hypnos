from pipeline import validate_and_censor_input, combine_user_turns, write_story

"""
Before submitting the assignment, describe here in a few sentences what you would have built next if you spent 2 more
hours on this project:

If I had two more hours, I'd focus on:

1. Cleaner context handoff between agents — auditing what each agent receives
   and pruning anything that isn't actually used for its job. Right now I'm
   not confident that's tight.

2. Decomposing the writing step. The writer currently does outlining,
   character work, and prose in one shot. I'd split it into smaller agents
   (outliner → character developer → prose writer) so each layer is deliberate.

3. More validation. I have content gates (validator/censor) but no structural
   checks on agent outputs — I'd add schema enforcement, length limits, and
   graceful handling when the model returns malformed JSON, so bad responses
   fail clearly instead of bubbling through.

Hypothetical, probably more than two hours: a judge-panel quality bar — keep
five strong reference bedtime stories, have a small panel of judges score
each draft, and only ship if the writer's draft lands above the bottom half.
Fine-tuning the model to sound more like a children's bedtime story is
another option, but it can't be done in two hours.
"""


def process_user_request(user_input, current_story, user_prompt_history, judge_messages, intake_log):
    """Run one user turn through the full pipeline.

    Pipeline: validate_and_censor_input → combine_user_turns → write_story.
    Returns the approved story, or None if any stage failed.
    """
    is_revision = current_story is not None

    # Run validator → censor on the input. They share intake_log so they can
    # interpret follow-ups after a rejection.
    if not validate_and_censor_input(user_input, current_story, intake_log, is_revision):
        return None

    # If multiple turns accumulated before approval, merge them into one
    # combined message for the writer; clears the intake log.
    effective_user_input = combine_user_turns(intake_log, user_input)
    user_prompt_history.append(effective_user_input)

    # Run writer/judge + final censor with up to 2 safety-hint retries.
    return write_story(effective_user_input, current_story, user_prompt_history, judge_messages, is_revision)


def main():
    """Interactive REPL: prompt for a story, then accept revisions or /new commands.

    Commands:
      /new        — start a fresh story
      /new <text> — start a fresh story with <text> as the first prompt
    """
    # Holds text after `/new <text>` so the next iteration uses it without re-prompting.
    pending_input = None
    # Persists across rejected turns; cleared on /new or after both gates approve.
    intake_log = []
    while True:
        if pending_input is None:
            user_input = input("What kind of story do you want to hear? ")
        else:
            user_input, pending_input = pending_input, None
        user_prompt_history = []
        judge_messages = []

        story = process_user_request(user_input, None, user_prompt_history, judge_messages, intake_log)
        if story is None:
            continue
        current_story = story

        while True:
            nxt = input("\nAny changes, or type '/new' to start a fresh story? ").strip()
            if nxt == "/new":
                intake_log.clear()
                break
            if nxt.startswith("/new "):
                pending_input = nxt[len("/new "):].strip()
                intake_log.clear()
                break

            judge_messages.clear()  # fresh judge session per revision
            story = process_user_request(nxt, current_story, user_prompt_history, judge_messages, intake_log)
            if story is None:
                continue
            current_story = story

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nGoodnight!")
