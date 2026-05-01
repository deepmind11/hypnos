# Hypnos — Multi-Agent Bedtime Story Generator

An interactive CLI that generates bedtime stories for children aged 5–10 using a multi-agent pipeline: validator, censor, writer, and judge. Built on OpenAI's `gpt-3.5-turbo`.

Named for [Hypnos](https://en.wikipedia.org/wiki/Hypnos), the Greek god of sleep.

## Setup

```bash
git clone <repo-url>
cd hypnos

# Set up your environment file with your OpenAI API key
cp .env.example .env
# then edit .env and paste in your OPENAI_API_KEY

# Install dependencies
pip install -r requirements.txt

# Run
python main.py
```

## How it works

```mermaid
flowchart TD
    User([User]) -->|story request| Validator
    Validator -.->|reject| User
    Validator -->|approve| Censor1[Censor: intake check]
    Censor1 -.->|reject| User
    Censor1 -->|approve| Writer

    Writer -->|draft| Judge
    Judge -.->|reject + feedback| Writer
    Judge -->|approve| Censor2[Censor: final safety check]

    Censor2 -.->|reject + safety hint| Writer
    Censor2 -->|approve: deliver story| User
```

Solid arrows = pass-through; dotted arrows = rejection paths.

The four agents:

1. **Validator** — confirms the user is engaging with the story chatbot (rejects off-topic, gibberish, or prompt-injection attempts). Permissive on themes — content safety is the censor's job.
2. **Censor (intake)** — gates user input for child-appropriateness. Shares an intake log with the validator so it can interpret follow-ups after a rejection (e.g. "with a parachute, on his birthday" after "thrown out of a plane" reframes the request as safe).
3. **Writer** — drafts the story. For revisions, it sees the previous story plus the new request.
4. **Judge** — evaluates the draft against a rubric (structure, vocabulary, sentence length, calming ending, length). Loops with the writer up to 3 times for revisions.

The censor also runs a **final safety check** on the approved draft. If it flags the story, the writer restarts with a safety hint (up to 2 attempts).

### Context management

Each agent only sees what it needs for the job in front of it. This was the most thought-out part of the design.

**Validator + Censor (intake).** Both share an `intake_log` — the user's turns from the current intake session plus their own prior verdicts. Sharing lets them read a follow-up like "with a parachute, on his birthday" as a clarification of an earlier rejected "thrown out of a plane" instead of judging each turn in isolation. Each turn also carries the current story so they can disambiguate revision requests like "make him a robot". As soon as both approve, the log is wiped.

**Writer.** Sees only what it needs to write the next draft. For a fresh story, one user message — either the prompt itself or, if it took multiple intake turns to get past the gates, a bullet-list combining them. For a revision, three messages: the original prompt, the current approved story, and the new revision request. During the writer-judge back-and-forth, each draft and each piece of judge feedback are appended in order, so the writer iterates against its own prior attempts and the judge's running critique.

**Judge.** Keeps a running conversation across iterations within a single writer-judge attempt so it remembers what it asked for and can check whether the writer addressed it. Each new attempt — whether a fresh story or a user revision — starts with empty judge memory, but always receives the rolling list of all user requests so far (initial + every revision) so it can evaluate the draft against the user's full intent. The verbose `evaluation` field the judge produces is stripped before being fed back — kept in logs for debugging, not in its own context.

**Censor (final safety check).** Stateless, single-shot. Receives just the story plus a `Source: writer story` label telling it which safety criteria to apply (it treats user input differently from writer output). Judging the story in isolation prevents earlier intake chatter from biasing the final check.

**Iteration loops.** The **writer-judge loop** runs up to 3 times, with the judge's feedback feeding into the writer's next draft. An **outer safety loop** wraps that and runs up to 2 times, restarting the writer-judge cycle with a safety hint each time the final censor flags the resulting story.

**A note on growing context.** The iteration caps above keep a single attempt bounded, but the rolling user-prompt list still grows across a long revision session. There's no compaction yet — for longer sessions we'd summarize older entries into a brief recap.

## Commands

Inside the REPL:

- Type any change you'd like to make to the current story.
- `/new` — start a fresh story (prompts for input).
- `/new <prompt>` — start a fresh story using `<prompt>` directly.
- `Ctrl+C` — exit.

## Project structure

```
main.py        — REPL + orchestrator (process_user_request)
pipeline.py    — pipeline helpers (validate_and_censor_input, combine_user_turns, write_story, writer_judge_loop)
agent.py       — Agent class wrapping the OpenAI API
agents.py      — Agent instances and system prompts
ASSIGNMENT.md  — original assignment brief
logs/          — per-session JSONL logs of every agent call (gitignored)
```

## Notes

- **Model** is locked to `gpt-3.5-turbo` per the original assignment.
- Every agent call is logged (full messages, response, token usage, latency) to `logs/<timestamp>.jsonl` for debugging.
- API key lives in `.env` — never commit it. (`.env` is gitignored.)

## Future plans

Things I'd build next:

1. **Cleaner context handoff between agents** — auditing what each agent receives and pruning anything that isn't actually used for its job. Right now I'm not confident that's tight.

2. **Decomposing the writing step.** The writer currently does outlining, character work, and prose in one shot. I'd split it into smaller agents (outliner → character developer → prose writer) so each layer is deliberate.

3. **More validation.** I have content gates (validator/censor) but no structural checks on agent outputs — I'd add schema enforcement, length limits, and graceful handling when the model returns malformed JSON, so bad responses fail clearly instead of bubbling through.

Two more speculative directions:

- **Judge-panel quality bar** — keep five strong reference bedtime stories, have a small panel of judges score each draft, and only ship if the writer's draft lands above the bottom half.
- **Fine-tuning the model** on a corpus of children's bedtime stories so it sounds more like one out of the box, before any judging or revision.
