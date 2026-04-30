Okay so here is what I am thinking.

    A user enters a prompt. Then our system processes it and spits out a story, during the process it might ask user
    some questions or once the user might ask for some changes to the story.


    I have thought of a mult-agentic architecture, where each agent will designated to perform a duty.
    Important considerations:
    1. System prompts for the Agent, this basically defines their role, personality and behavior
    2. The Agent Loop: How does communication flow once a session is initiated. Of course requiring guardrails so that
    we don't get stuck in an infinite loop.
    3. Context Management: How long should the context window be for each agent? When agents are communicating what
    information should be shared? How do you manage a growing context window? How do you decide what to keep in the
    context window?
    4. External Datasources (optional, have no plans at the moment)

  Am I missing any fundamental component in my agentic system desgin?

  Okay so let's start with what agents will exist in this system, before we decide the system prompts, how to wire them up and the agentic loop.

  We will have:
  a) The Writer: A childrens story writer, that takes in a user prompt and returns a story.
  b) A Judge/Editor: That looks at what the writer wrote and gives feedback. The writer then incorporates that feed  back and we have a little back and forth. (so this in one loop in the
  entire system, there are other loops, but this is the most important one)
  c) A Censorship Agent: Before the Writer is ready to send the story out to the User, it makes sure the content is suitable for a 5-10 year old.The censorship agent also looks at user
  input to make sure they aren't asking for something unsuitable for a child between 5-10.
  d) A validator: A lightweight agent that just ensures the input makes sense and is relevant to what the overall system is designed to do. No answering coding questions, if gibberish,
  then ask user to give a prompt instead. The validator as far as I can see doesn't communicate with other agents. It is the first check that happens after user input.

  This is our baseline model. As you can see it is simple. The agentic loop and emerges out of what we just wrote: Writer-Judge Loop and two checks: one for censorship and once for input
  validation.

  User -> Validator (if fails, back to User) -> Censorship (if fails back to user) -> Writer -> Judge -> Writer .... Judge accepts -> Censorship (if pass send to User) if fail -> Writer
  -Judge .. and it repeats.

  Is this clear? I will have to think of how I will setup guardrails so as to prevent infinite loops. If the systems hits that limit, it prints out a message, saying could not generate a
  story using that prompt, suggest a different one.

  Okay now we have to decide, what all information will be exchanged between these agents whenever they communicate. This is where we decide how the system will manage context
  effectively.

  One things I realised is that out program will need to track the "Current Story State" (initialized as an empty string) globally so that all agents have access to it. You will see why
  in a moment.

  Let's start with the Validator. Validator agents will need to know the current state of the story to contextualize user input. If validation fails, it needs to let the user know, so it
  could lead to a back and forth. It needs to hold all of this into context. (For now let's assume that the conversation size will remain small, so we don't have we worry about it
  overflowing. Make a note of this assumption.) Once validation passes, the context is cleared.

  The Censorship Agent can be stateless, it only needs to verify that the input it recieved, whether from the user or the writer does not contain inappropriate content. This one is easy.

  Let's think about the Judge now:
  The Judge is basically in a conversation with the writer, it is evaluating writer output at each turn. Does it need to know previous iterations to judge the latest draft? I think it
  does, because it needs to evaluate whether the previous feedback was incorporated. I could make the judge stateless, but it just feels less coherent to me that way. Now, since we are
  exchanging stories here, the context can grow quickly and overflow, I need to address this. Perhaps, I can start with a larger context window to begin with. I will come up with an exact
   strategy later, compacting older conversations is a simple strategy that can work. Make a note of this, we will implement this in future iterations, want to keep the first model
  simple.

  Also, when the judge and writer are having a conversation, the writer only sends the diff of the current story, to minimize token usage.

  Once the judge approves the story, I can clear the context. This has one limitation, it is possible that the censorship agent, flags the story and we have to start another judge-writer
  loop. For now just make a note of this, we are not addressing this here.

  Okay, finally the writer. The only agent that talks to two different agents, the user and has to maintain state.
  So it has to hold the entire conversation with the Judge. Once the judge approves, we can summarize that block of  conversation, then the writer might have an interation with the
  censorboard, which could lead to a rewrite and a new session with the judge. Or the user might ask for a modification, which  will lead to another session with the judge. Here is an
  important observation, the writer-user and writer-censor interations are actually small in comparison to their interaction with the judge. So whenever a judge approves, that will define
   the end of the block and we can compress the conversation block. What exactly needs to be saved in this compression, we can decide later, make a note of it.


  Okay, now that we know what the agentic loop is and how these agents communicate and manage context we can start defining appropriate system prompts to match those expectations.
  The final system prompts for these agents will be decided iteratively, based on story quality and adherence to system specifications as described above.

  I want to start with simple prompting strategies, understanding that will help me gauge if complex prompts are actually improving performance or not.

  The most suitable techniques here would be:
  Censor and Validator: "Few shot Prompting" and "Role"
  Judge: "Role" + I need to provide it with some rubric to evaluate stories (can u search the internet for this, there is the three art structure,hero's journey, etc.Which one would be
  best for bedtime stories for children)
  Writer: "Role" + Also need to provide constraints on lenght of story (500-600 words seems to be the sweet spot for bedtime stories). Sentence lenght and complexity. Wordcomplexity. The
  writer should also follow some structure such as heros journey, etc. What structure do bedtime stories follow.
  For writer creativity, you will also need to adjust the temprature of the agent, right now it is set to 0.1, which is to low for a writer, should be around 0.7. Please suggest
  temperature ranges for other agents as well.



  That is a lot to digest. The prompt reads a bit like stream of consciousness, so let me summarise. I start with what I am thinking at the high-level the agent architecture: Agent loop,
  communication protocol,  context management and system prompts for the agents. I then do a deep dive into each of them.

  Please review everything I have said. Transform it into a to-do list(save it) so that we don't miss anything. Make sure to save the prompt to drive. Once that is done, let's come up
  with a plan of action to build this.
