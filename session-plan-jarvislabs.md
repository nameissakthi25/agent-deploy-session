# Session Plan

**Serving and Shipping It Yourself: Chatbot → RAG → Multi-Agent on Your Own GPU**

Weekend Batch · Final Session · 2 hours
JarvisLabs (A100 80GB) · vLLM · LangGraph · Arize Phoenix · Docker Compose

---

## What this session is

Learners have already built a working multi-agent system. This session is about the gap between something that works on a laptop and something you can hand to a client — with no managed platform doing the hard parts for you.

We serve the model ourselves on a GPU, then deploy one use case three times against it: a plain chatbot, a RAG chatbot, and a multi-agent system. Along the way we add the things that make a system operable — guardrails, tracing, tests, a build pipeline, and a feedback loop.

Nothing is written live. The code is pre-built, and we walk through it, run it, and deploy it. Learners observe rather than follow along in a terminal. Say this at the start so nobody tries to keep up.

**Why this shape matters:** every layer here is ours. There is no platform providing secrets management, autoscaling, or traffic control. That makes the session harder to build and better to learn from — learners see the decisions a managed platform would have made on their behalf, and they get a real answer to the client who says their data cannot leave the country.

## What learners should leave with

- What it takes to serve an open model yourself, and what it costs per token when you measure it rather than read it
- What putting an application in a container actually forces you to decide
- The ability to read an agent trace and find a specific failure inside it
- Where guardrails belong in a multi-agent system, especially the one place most people miss
- Which parts of an agent system can be tested normally, and which can only be scored
- An honest sense of when multi-agent is worth its cost

## At a glance

| Time | What happens |
|---|---|
| 0:00 | Framing and ground rules |
| 0:04 | The model layer — vLLM on the GPU |
| 0:18 | Stage 1 — the plain chatbot, and the first deploy |
| 0:32 | Turning on tracing, while things are still simple |
| 0:40 | Stage 2 — RAG, and state leaving the container |
| 0:49 | Guardrails on the way in and on the way out |
| 0:58 | Stage 3 — the agents, and the guardrail only they need |
| 1:13 | Testing something that doesn't behave the same way twice |
| 1:22 | The build pipeline, and the third deploy |
| 1:33 | Closing the feedback loop |
| 1:44 | Three versions, one question — and how real teams roll out |
| 1:51 | Questions |

---

## Infrastructure

One JarvisLabs A100 80GB instance running everything under Docker Compose:

| Container | Role | Port |
|---|---|---|
| `vllm` | Serves the model, OpenAI-compatible API | 8000 |
| `chat-v1` | Stage 1 — plain chatbot | 8101 |
| `chat-rag` | Stage 2 — RAG chatbot | 8102 |
| `chat-agents` | Stage 3 — multi-agent | 8103 |
| `phoenix` | Tracing UI and collector | 6006 |
| `caddy` | Reverse proxy, routes `/v1`, `/v2`, `/v3` | 80 |
| `ui` | Streamlit, with the thumbs control | 8501 |

The vector database stays **outside** the box on a managed free tier (Qdrant Cloud or Pinecone). This is deliberate: if everything sits on one machine, the Stage 2 lesson about state leaving the container disappears. Keep it external so that lesson is real.

**Model:** a 30B-class instruct model with native tool-calling support, served through vLLM with its tool-call parser enabled. Sizing driven by one constraint — the Stage 3 supervisor must emit reliable tool calls, and smaller models are noticeably weaker at this. Confirm the specific model and parser flags during rehearsal; this is the single highest-risk technical dependency in the session.

## Budget

$50 purchased. A100 80GB at $1.49/hr with per-minute billing gives roughly 33 hours.

| Activity | Hours | Cost |
|---|---|---|
| Build and first bring-up | 6 | $9 |
| Rehearsal 1 | 3 | $4.50 |
| Rehearsal 2 | 3 | $4.50 |
| Session | 2.5 | $4 |
| Buffer | 6 | $9 |
| **Total** | **~20** | **~$31** |

**The main way this budget disappears is forgetting to pause.** A GPU left running overnight costs about $36 — more than the entire planned spend. Pause the instance after every single session. Note also that retained storage continues billing while the instance is paused, so tear down the filesystem once the session is done.

Everything off the box is free: Phoenix runs in a container, the vector database is a free tier, GitHub Actions is within included minutes.

---

## 0:00 — Framing

Stage 1 is already running on screen. Ask the room one question: what stops you giving this URL to a client today?

Take answers and write them up. They will name most of the syllabus themselves — it breaks and we don't know why, anyone could abuse it, we can't tell if it's getting better. Map each answer to a segment. The session becomes answers to their own list rather than a lecture.

Announce the ground rule: questions at the end, not during. Say it out loud. Two hours this dense will otherwise lose fifteen minutes to questions the session was about to answer anyway.

## 0:04 — The model layer

Nothing else can run until the model is up, so start here.

Walk the vLLM service in the compose file: which model, what quantization, how much GPU memory it's told to claim, and the tool-call parser that Stage 3 will depend on. Bring it up and watch the weights load.

Then look at what you can only see when the GPU is yours:

**GPU memory.** Show `nvidia-smi`. Weights, KV cache, and the headroom left over. Explain why the KV cache is what actually limits how many users you can serve at once — not the weights.

**Batching.** Fire one request, then ten at once. Total time barely moves. Continuous batching is why self-hosting is viable at all, and seeing it is more convincing than being told.

**Tokens per second, and money.** Read throughput off the vLLM logs. Then do the arithmetic on screen: at $1.49 an hour, and this many tokens per second, what does a million tokens cost you? Compare that number to a hosted API's published rate.

That comparison is the segment's payoff, and it cuts both ways honestly. Self-hosting is cheaper per token at high utilisation and much more expensive at low utilisation, because you pay for the GPU whether anyone is asking questions or not. The real reasons to self-host are usually data residency and predictable cost, not raw price.

## 0:18 — Stage 1: the plain chatbot

Deliberately boring code. One endpoint, one model call, no memory. The interesting part isn't the chatbot, it's what happens when you try to put it in front of people.

**Where state goes.** Restart the container and watch the conversation vanish. Anything you kept in a variable is gone on restart, and gone again if you ever run two copies. Show where it would have to live instead.

**Where the keys live.** Show the wrong way first — a key hardcoded in the source, then a key in the compose file that's about to be committed. Then fix it: `.env` kept out of version control, injected at runtime. Be honest here that a managed platform would give you a proper secret store with versioning and audit logs, and that a `.env` file on one box is the minimum, not the standard. Naming the gap is the lesson.

**Which port, and who can reach it.** The app listens inside the container; Caddy routes the outside world to it. Show the mapping. Then ask who else can reach port 8000 — the model endpoint has no authentication in front of it, and on a public IP that matters.

Deploy it: `docker compose up -d chat-v1`. Hit the route through the proxy. It's live.

Close by saying: this is how a prototype ships. In an hour we'll see why it isn't how a product ships.

## 0:32 — Turning on tracing

Do this now, while a request is still small enough to read in full.

Phoenix is already in the compose file. Six lines in the app, and every model call becomes visible. Run one request and read the trace together: how long it took, how many tokens, and the actual prompt that got sent. That last one usually surprises people, because once you count the system prompt, the template, and the history, it's much bigger than what the user typed.

The reason to do this early is practical. A three-step trace teaches you to read traces; a forty-step trace does not. By Stage 3 the tree will be large, and this is what makes it readable.

Worth saying once: the instrumentation is standard OpenTelemetry, and because vLLM speaks the OpenAI protocol, it traces a self-hosted model exactly as it would a hosted one. We never touch it again for the rest of the session.

## 0:40 — Stage 2: RAG, and state leaving the container

Move quickly. The room already knows RAG. Only the deployment lesson is new.

The lesson: the vector database cannot live inside the container. Containers get rebuilt and restarted, and an index sitting on a container filesystem is either lost or inconsistent between copies. So it moves out to a managed service, and the application keeps only a connection and a credential.

Name what just happened. Even on a single box, the project stopped being one program and became a distributed system. Everything harder about the rest of the session follows from that.

This is also where the Dockerfile gets interesting — a real base image, real system dependencies, and a layer order chosen so that changing application code doesn't reinstall everything. Show a rebuild taking six seconds because the dependency layer was cached.

Deploy: `docker compose up -d chat-rag`. Then look at the trace — there's a retrieval step in it now, showing which documents came back. For the first time you can *check* whether the answer came from the documents or whether the model filled in the gaps itself.

## 0:49 — Guardrails, in and out

Written by hand rather than pulled from a library, so people see the mechanism instead of a config file.

**On the way in**, before anything reaches the model: injection heuristics, personal data, absurd input lengths. The cheapest possible place to say no.

**On the way out**, before anything reaches the user: does the response match the shape we promised, and does it violate any policy we care about.

Run two inputs built specifically to get blocked. Show them blocked, then show what the system would have returned otherwise. Find both rejections in the trace — guardrails are part of the recorded history, not something happening off to the side.

**One point that lands harder here than on a managed platform:** a hosted model would have arrived with its own safety filters already applied. Ours has none. Everything protecting this system is code we wrote. That's the trade for controlling the model — full control means full responsibility, and it's worth stating plainly to a room that may be pitching self-hosting to clients.

Flag that there's a third place guardrails belong, and it only exists once you have multiple agents. That's next.

## 0:58 — Stage 3: the agents

Walk the graph: a supervisor and three workers. Each node becomes a step in the trace, so the picture on the slide and the picture in Phoenix are the same picture.

Then the third guardrail, and it's the important one. In a single-agent system the model calls tools you chose and configured. In a multi-agent system, **one agent's output becomes another agent's tool input** — nobody wrote that input and nobody reviewed it. That surface doesn't exist in simpler systems, and it's the one almost nobody guards. Every tool call gets an allowlist and argument validation.

Run it. The trace tree is the whole system laid out visually, and the hand-off between agents — abstract last week — is right there as one step sitting inside another.

Then break it deliberately. A malformed tool argument works well. Debug it from the trace alone, without opening a log file. That's the payoff for everything since 0:32.

Finally, show the waterfall: one user request fanning out into a dozen sequential model calls, all hitting your single GPU. Go back to `nvidia-smi` and show the KV cache under real pressure. This is where the earlier cost arithmetic gets uncomfortable — a multi-agent request is roughly a dozen times the inference cost of a chatbot request, and on your own hardware that shows up as concurrency limits rather than a bill.

## 1:13 — Testing something that doesn't behave the same way twice

The idea that makes this teachable: sort tests by whether the thing is predictable, not by how big it is.

**Predictable, so test it properly.** Guardrails are ordinary functions with ordinary inputs and outputs. Output schemas either match or don't. Routing can be tested by feeding the supervisor a state and asserting which worker it picks. None of these need a model call, and the whole set should finish in seconds.

**Not predictable, so score it instead.** Whether an answer is *good* can't be asserted. You run it across a batch of examples, score the batch, and check the average clears a line you set. That's a release decision, not a per-commit one.

Run the fast suite live. Its speed is the argument — if the predictable tests finish in seconds, nobody needs convincing they should run on every change.

The line to land: people try to assert an exact response from a language model, watch it fail randomly, and conclude agent systems can't be tested. They can. The checks just live in different places, and some are thresholds rather than assertions.

## 1:22 — The build pipeline, and the third deploy

Open with an honest admission. Twice now I deployed by typing a command into a box I was already logged into. That's how a demo ships. It depends on my shell history, nothing checked it before it went out, and if it breaks there's no way back.

So instead, push a commit and let the pipeline run:

1. Run the fast tests
2. Build the image and tag it with the exact commit
3. Push it to a registry
4. Pull and restart the service on the instance
5. Run the scored evaluations against it

**Two honest notes to make out loud, not hide:**

The pipeline authenticates with a long-lived API key stored in the repository's secrets. On a managed cloud you'd use short-lived tokens issued per run, with no permanent credential anywhere. We don't have that here, and it's a real weakness — say so rather than presenting it as good practice.

Step 4 is a restart, which means a few seconds of downtime and no way back except redeploying the previous image. Which brings us to the last segment.

Talk over the pipeline run. When it goes green, Stage 3 is live — deployed by a pipeline rather than a person.

## 1:33 — Closing the feedback loop

The pipeline just scored the new version against a set of examples. Where did those come from?

From users. A thumbs-down in the interface attaches itself to that request's trace. Filter for the unhappy ones. Turn them into a set. Change one thing — a prompt, how many documents get retrieved, a routing rule — and run the set again to see whether the score moved.

Do this with real thumbs-downs collected from the room earlier in the session.

The chain is the lesson: no tracing means no examples, no examples means no measurement, and without measurement "we improved it" is just a feeling. And because the pipeline scores against that same set, real user complaints become the thing that blocks a bad release.

## 1:44 — Three versions, one question — and how real teams roll out

All three are live. Ask each the same question and put them side by side: how long each took, how many tokens each burned, and how good each answer was.

Then ask it plainly: **did the agents earn their complexity here?** Sometimes the honest answer is no, and saying so is more valuable than anything else in the session. Multi-agent is a cost you pay when you need the capability — it isn't a default and it isn't a sign of sophistication.

Close with the thing we didn't build, on the whiteboard, in about three minutes:

**Canary releases.** Version 1 is live serving everyone; you've built version 2. Rather than switching everyone at once, you send a small slice of real traffic — say ten percent — to the new version, watch the traces and the thumbs-downs, then either ramp to a hundred percent or pull it back. The name comes from canaries in coal mines: a small early warning before the whole thing goes bad.

This matters more for agents than for ordinary software, because you can never fully know whether an agent's answers are good before real users hit it. Evals give you an average on a fixed set; real questions are messier. So you expose a few users and decide from real evidence.

On a managed platform this is a single command and the rollback is a config change, not a redeploy. On our setup you'd have to build it yourself with weighted routing in the proxy. We didn't — and that's the honest trade for owning the whole stack. Worth knowing it exists and what it costs to not have it.

## 1:51 — Questions

---

## What we deliberately left out

- **Writing code live.** Not possible alongside model serving, three deploys, and a pipeline in two hours.
- **Depth on RAG.** The room already has it. Nine minutes, deployment lesson only.
- **Questions during the session.** The biggest risk to the schedule.
- **Canary routing, built.** Explained on the whiteboard, not implemented. Building weighted routing live on self-managed infrastructure is fragile, and the concept lands fine without it.
- **Autoscaling and multi-instance.** One box, one GPU. Say what would change with more.
- **Managed alternatives.** One sentence: Cloud Run or a similar platform gives you secrets, traffic control, and keyless CI for free, at the cost of sending your data there.

## Before the session

- **Model and tool-call parser confirmed working.** The Stage 3 supervisor must emit reliable tool calls. This is the highest technical risk of the whole session — verify it first, and be willing to change model if it's shaky.
- Full compose stack brought up from scratch at least twice, timed
- Repository tagged at each of the three stages; all dependencies pinned
- Pipeline run green at least twice; the commit for the 1:22 demo written and ready to push
- `.env` populated; vector database provisioned, indexed, and reachable from the box
- Phoenix container confirmed receiving traces from all three app services
- Blocked inputs tested end to end against the deployed Stage 3
- Reverse proxy routes verified from outside the instance, on a phone if possible
- Recordings made of the model bring-up, all three deploys, and one green pipeline run
- **Instance paused** after every rehearsal, without exception
- Second screen arranged, with Phoenix visible from 0:32 onward

## If something goes wrong

| Problem | What to do |
|---|---|
| Model fails to load or is slow to start | Bring the stack up before the room arrives; never load weights live |
| Tool calls come back malformed at Stage 3 | Fall back to the recorded run; this is why it's rehearsed twice |
| GPU out of memory under the Stage 3 fan-out | Lower the concurrency cap and the KV cache allocation; have working values noted in advance |
| A deploy fails | Play the recording and keep going |
| Pipeline hangs or queues | Give it ninety seconds, then cut to the recorded run |
| Instance unreachable | Local Docker Compose on a laptop with a much smaller model, rehearsed as a cold fallback |
| Running behind at 1:22 | Shorten testing by showing the tests rather than running them. Never cut the pipeline or the feedback loop. |

## After the session

Instance paused immediately, then torn down along with its storage — retained storage keeps billing after a pause. Learners do not need infrastructure of their own.

What they take home:

- The repository, tagged at all three stages — the differences between the tags are the syllabus
- The compose file, which is a complete self-hosted stack they can run on any GPU box
- An export of the session's traces, so the trace-reading segments can be revisited
- The cost-per-token arithmetic from 0:04, with the numbers we actually measured
