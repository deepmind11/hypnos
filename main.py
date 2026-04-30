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


def main():
    while True:
        user_input = input("What kind of story do you want to hear? ")

        print("Validating your request...")
        validator_input = f"Current story: (none)\n\nUser input: {user_input}"
        raw = validator.run([{"role": "user", "content": validator_input}])
        result = json.loads(raw)
        if not result["pass"]:
            print(f"Hmm, I couldn't help with that — {result['feedback']}")
            continue

        print("Checking content is age-appropriate...")
        raw = censor.run([{"role": "user", "content": user_input}])
        result = json.loads(raw)
        if not result["pass"]:
            print(f"Hmm, I couldn't help with that — {result['feedback']} How about: \"{result['alternate']}\"?")
            continue

        print("Writing the story...")
        user_prompt_history = [user_input]
        writer_messages = [{"role": "user", "content": user_input}]
        judge_messages = []
        story = writer_judge_loop(writer_messages, judge_messages, user_prompt_history)

        if story is None:
            print("Could not generate a story for that prompt; please try a different one.")
            continue

        print("Final safety check on the story...")
        raw = censor.run([{"role": "user", "content": story}])
        result = json.loads(raw)
        if not result["pass"]:
            print("Could not generate a story for that prompt; please try a different one.")
            continue

        print(story)
        current_story = story

        while True:
            nxt = input("\nAny changes, or type '/new' to start a fresh story? ")
            if nxt.strip() == "/new":
                break

            print("Validating your revision...")
            validator_input = f"Current story: {current_story}\n\nUser input: {nxt}"
            raw = validator.run([{"role": "user", "content": validator_input}])
            result = json.loads(raw)
            if not result["pass"]:
                print(f"Hmm, I couldn't help with that — {result['feedback']}")
                continue

            print("Checking content is age-appropriate...")
            raw = censor.run([{"role": "user", "content": nxt}])
            result = json.loads(raw)
            if not result["pass"]:
                print(f"Hmm, I couldn't help with that — {result['feedback']} How about: \"{result['alternate']}\"?")
                continue

            user_prompt_history.append(nxt)
            writer_messages = [
                {"role": "user", "content": user_prompt_history[0]},
                {"role": "assistant", "content": current_story},
                {"role": "user", "content": f"Revise the story: {nxt}"},
            ]

            print("Revising the story...")
            story = writer_judge_loop(writer_messages, judge_messages, user_prompt_history)

            if story is None:
                print("Could not generate this revision; the previous story still stands. Try a different revision.")
                continue

            print("Final safety check on the revised story...")
            raw = censor.run([{"role": "user", "content": story}])
            result = json.loads(raw)
            if not result["pass"]:
                print("Could not generate this revision; the previous story still stands. Try a different revision.")
                continue

            print(story)
            current_story = story

if __name__ == "__main__":
    main()
