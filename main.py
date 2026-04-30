import json

from agents import validator, censor, writer, judge

"""
Before submitting the assignment, describe here in a few sentences what you would have built next if you spent 2 more
hours on this project:

"""

example_requests = "A story about a girl named Alice and her best friend Bob, who happens to be a cat."

def writer_judge_loop(writer_messages, judge_messages, user_prompt_history):
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
        judge_messages.append({"role": "assistant", "content": raw})
        result = json.loads(raw)
        if result["pass"]:
            return draft

        print(f"Judge requested revisions: {result['feedback']}")
        writer_messages.append({
            "role": "user",
            "content": f"Judge feedback: {result['feedback']}\n\nPlease revise the story.",
        })
    return None


def process_input(user_input, current_story, user_prompt_history, judge_messages):
    is_revision = current_story is not None
    failure_message = (
        "Could not generate this revision; the previous story still stands. Try a different revision."
        if is_revision
        else "Could not generate a story for that prompt; please try a different one."
    )

    print("Validating your revision..." if is_revision else "Validating your request...")
    validator_input = f"Current story: {current_story or '(none)'}\n\nUser input: {user_input}"
    raw = validator.run([{"role": "user", "content": validator_input}])
    result = json.loads(raw)
    if not result["pass"]:
        print(f"Hmm, I couldn't help with that — {result['feedback']}")
        return None

    print("Checking content is age-appropriate...")
    raw = censor.run([{"role": "user", "content": user_input}])
    result = json.loads(raw)
    if not result["pass"]:
        print(f"Hmm, I couldn't help with that — {result['feedback']}")
        return None

    user_prompt_history.append(user_input)

    def build_writer_messages(safety_hint: str = "") -> list[dict]:
        last = f"Revise the story: {user_input}" if is_revision else user_input
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
    for attempt in range(2):
        story = writer_judge_loop(writer_messages, judge_messages, user_prompt_history)
        if story is None:
            print(failure_message)
            return None

        print("Final safety check on the revised story..." if is_revision else "Final safety check on the story...")
        raw = censor.run([{"role": "user", "content": story}])
        result = json.loads(raw)
        if result["pass"]:
            break

        print(f"Safety check flagged the story: {result['feedback']} Writing a fresh story...")
        writer_messages = build_writer_messages(safety_hint=result["feedback"])
    else:
        print(failure_message)
        return None

    print(story)
    return story


def main():
    while True:
        user_input = input("What kind of story do you want to hear? ")
        user_prompt_history = []
        judge_messages = []

        story = process_input(user_input, None, user_prompt_history, judge_messages)
        if story is None:
            continue
        current_story = story

        while True:
            nxt = input("\nAny changes, or type '/new' to start a fresh story? ")
            if nxt.strip() == "/new":
                break

            story = process_input(nxt, current_story, user_prompt_history, judge_messages)
            if story is None:
                continue
            current_story = story

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nGoodnight!")
