from agent import Agent

"""
Before submitting the assignment, describe here in a few sentences what you would have built next if you spent 2 more
hours on this project:

"""

agent = Agent(
    system_prompt="You are a helpful assistant.",
    temperature=0.1,
    max_tokens=3000,
)

example_requests = "A story about a girl named Alice and her best friend Bob, who happens to be a cat."

def main():
    user_input = input("What kind of story do you want to hear? ")
    response = agent.run([{"role": "user", "content": user_input}])
    print(response)

if __name__ == "__main__":
    main()
