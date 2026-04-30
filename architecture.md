# Bedtime Story Chatbot — Architecture (v1 plan)

Source: planning prompt by user, 2026-04-29.

## High-level shape

A user enters a prompt. The system processes it and returns a story. During the process, the system might ask the user clarifying questions, or the user might request changes to the story.

This is a multi-agent system. Each agent has a designated role.

## Considerations

1. **System prompts** — define each agent's role, personality, and behavior.
2. **The agent loop** — how communication flows once a session starts. Needs guardrails to avoid infinite loops.
3. **Context management** — context window per agent, what info passes between agents, how to manage growing context, what to keep vs drop.
4. **External datasources** — optional, none planned.

## Agents

- **Writer**: a children's story writer. Takes a user prompt, returns a story.
- **Judge / Editor**: reviews the Writer's draft, gives feedback. Writer incorporates feedback. Back-and-forth — the most important loop in the system.
- **Censor**: before the Writer sends the story to the user, verifies content is suitable for ages 5–10. Also checks user input for inappropriate requests.
- **Validator**: lightweight; ensures input makes sense and is on-topic. Rejects coding questions, gibberish, etc. First check after user input. Does not communicate with other agents.

## Flow

```
User
  │
  ▼
Validator ── fail ──► User
  │ pass
  ▼
Censor (input) ── fail ──► User
  │ pass
  ▼
Writer ◄────┐
  │         │
  ▼         │
Judge ──────┘  (until Judge approves)
  │ approved
  ▼
Censor (output) ── fail ──► (back to Writer ↔ Judge)
  │ pass
  ▼
User
```

If iteration limit hit: emit a "could not generate a story for that prompt" message and ask the user to try a different one.

## Shared state

- **Current Story State** — global string, initialized empty. All agents read it; the Writer writes to it.
- **User prompt history** — list of user prompts: the initial story request plus any later revision prompts. Passed to the Judge each round so it can evaluate the draft against everything the user has asked for.

## Per-agent context strategy

- **Validator**: Current Story State + recent user/validator turns. Assumed small for now; revisit if it grows.
- **Censor**: stateless. Verifies only the chunk passed in.
- **Judge**: each round receives `(user prompt history, current draft, prior feedback turns)`. The user prompt history (initial + any revisions) lets the Judge evaluate whether the draft addresses what the user actually asked for. Context will grow → eventually compact older turns. **Compaction deferred to a later iteration.**
- **Writer**: most stateful. Converses with Judge, Censor, and User. Compress the conversation block when the Judge approves. Censor flagging an approved story re-triggers a Writer ↔ Judge round (known limitation, deferred).

When the Writer ↔ Judge loop runs, the Writer sends the **full current draft** to the Judge each round (story is small; diff optimisation deferred).

## Prompting strategy

Start simple. Understand simple prompting before judging whether complexity actually improves quality.

- **Validator & Censor**: few-shot + role + structured JSON output (`{"pass": bool, "feedback": str}`).
- **Judge**: role + bedtime-tuned three-act rubric + structured JSON output (`{"approved": bool, "feedback": str}`).
- **Writer**: role + length (~500–600 words), sentence simplicity, age-appropriate vocabulary, **bedtime-tuned three-act**: gentle setup → mild conflict (no high-stakes drama or fear) → soothing resolution with cozy wind-down language ("safe", "cozy", "snuggled", "dream").

## Temperatures (v1)

- Writer: 0.7
- Judge: 0.3
- Censor: 0.0
- Validator: 0.0

Tune during prompt iteration if needed.

## Deferred / known limitations

- Compaction strategy for Judge & Writer histories.
- Censor re-trigger of Writer ↔ Judge loop after final-story rejection.
- What to retain when compressing a Judge-approved block.
- Final system prompts — iterated based on observed story quality.

## Decisions (v1)

- **Iteration cap** for Writer ↔ Judge: **3** per session. One iteration = one Writer-Judge back-and-forth. Cap can be raised later.
- **Session reset**: a fresh Writer ↔ Judge session (counter back to 0) begins when the Censor rejects an approved draft, or when the user requests a revision after delivery.
- **Structured outputs** via OpenAI JSON mode for Validator / Censor / Judge.
- **Story structure**: bedtime-tuned three-act (see Prompting strategy).
- **Writer → Judge payload**: full current draft each round (no diffs in v1).
