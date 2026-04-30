import json

from agents import validator, censor, writer, judge

"""
Before submitting the assignment, describe here in a few sentences what you would have built next if you spent 2 more
hours on this project:

"""

example_requests = "A story about a girl named Alice and her best friend Bob, who happens to be a cat."

def main():
    user_input = input("What kind of story do you want to hear? ")

    print("Validating your request...")
    raw = validator.run([{"role": "user", "content": user_input}])
    result = json.loads(raw)
    if not result["pass"]:
        print(f"Hmm, I couldn't help with that — {result['feedback']}")
        return

    print("Checking content is age-appropriate...")
    raw = censor.run([{"role": "user", "content": f"REQUEST: {user_input}"}])
    result = json.loads(raw)
    if not result["pass"]:
        print(f"Hmm, I couldn't help with that — {result['feedback']} How about: \"{result['alternate']}\"?")
        return

    print("Writing the story...")
    writer_messages = [{"role": "user", "content": user_input}]
    judge_messages = []
    story = None
    for i in range(3):
        draft = writer.run(writer_messages)
        writer_messages.append({"role": "assistant", "content": draft})

        print(f"Judging draft {i + 1}...")
        judge_messages.append({
            "role": "user",
            "content": f"User request: {user_input}\n\nDraft to evaluate:\n\n{draft}",
        })
        raw = judge.run(judge_messages)
        judge_messages.append({"role": "assistant", "content": raw})
        result = json.loads(raw)
        if result["pass"]:
            story = draft
            break

        print(f"Judge requested revisions: {result['feedback']}")
        writer_messages.append({
            "role": "user",
            "content": f"Judge feedback: {result['feedback']}\n\nPlease revise the story.",
        })

    if story is None:
        print("Could not generate a story for that prompt; please try a different one.")
        return

    print("Final safety check on the story...")
    raw = censor.run([{"role": "user", "content": f"STORY: {story}"}])
    result = json.loads(raw)
    if not result["pass"]:
        print("Could not generate a story for that prompt; please try a different one.")
        return

    print(story)

if __name__ == "__main__":
    main()
