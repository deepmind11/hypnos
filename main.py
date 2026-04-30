import json

from agents import validator, censor, writer

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
    raw = censor.run([{"role": "user", "content": user_input}])
    result = json.loads(raw)
    if not result["pass"]:
        print(f"Hmm, I couldn't help with that — {result['feedback']} How about: \"{result['alternate']}\"?")
        return

    print("Writing the story...")
    story = writer.run([{"role": "user", "content": user_input}])
    print(story)

if __name__ == "__main__":
    main()
