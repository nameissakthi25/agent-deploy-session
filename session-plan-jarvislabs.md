# Session Plan

**Serving and Shipping It Yourself: Chatbot → RAG → Multi-Agent on Your Own GPU**

Weekend Batch · Final Session · 2 hours
JarvisLabs H100 80GB (region IN2) · vLLM · LangGraph · Arize Phoenix · Docker Compose

*Rewritten 2026-09-09 against the built repository. Every number below was
measured on the actual card, not estimated. Where a number is still unverified
it is marked as such.*

---

## What this session is

Learners have already built a working multi-agent system. This session is about
the gap between something that works on a laptop and something you can hand to a
client — with no managed platform doing the hard parts for you.

We serve the model ourselves on a GPU, then deploy one use case three times
against it: a plain chatbot, a RAG chatbot, and a multi-agent system. Along the
way we add the things that make a system operable — guardrails, tracing, tests, a
build pipeline, and a feedback loop.

Nothing is written live. The code is pre-built, and we walk through it, run it,
and deploy it. Learners observe rather than follow along in a terminal. Say this
at the start so nobody tries to keep up.

**Why this shape matters:** every layer here is ours. There is no platform
providing secrets management, autoscaling, or traffic control. That makes the
session harder to build and better to learn from — learners see the decisions a
managed platform would have made on their behalf, and they get a real answer to
the client who says their data cannot leave the country.

## What learners should leave with

- What it takes to serve an open model yourself, and what a token actually costs
  once you measure it instead of reading a pricing page
- The one number that decides whether self-hosting is worth it, and why it is
  almost never the hourly rate
- What putting an application in a container forces you to decide
- The ability to read an agent trace and find a specific failure inside it
- Where guardrails belong in a multi-agent system, especially the one place most
  people miss — and how weak a hand-rolled guard really is when you measure it
- Which parts of an agent system can be tested normally, and which can only be
  scored
- An honest sense of when multi-agent is worth its cost

## At a glance

| Time | What happens |
|---|---|
| 0:00 | Framing and ground rules |
| 0:04 | The model layer — vLLM on the GPU, and what a token costs |
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

One JarvisLabs H100 80GB VM running everything under Docker Compose. Eight
services:

| Container | Role | Port |
|---|---|---|
| `vllm` | Serves the model, OpenAI-compatible API | 8000 (published) |
| `chat-v1` | Stage 1 — plain chatbot | 8101 (internal) |
| `chat-rag` | Stage 2 — RAG chatbot | 8102 (internal) |
| `chat-agents` | Stage 3 — multi-agent | 8103 (internal) |
| `qdrant` | Vector database, own container and own volume | 6333 (published) |
| `phoenix` | Tracing UI and OTLP collector | 6006 (published) |
| `ui` | Streamlit, with the thumbs control | 8501 (internal) |
| `caddy` | Reverse proxy — the only way in | 80 |

Routes through Caddy: `/v1/*`, `/v2/*`, `/v3/*` to the three apps, `/traces` to
Phoenix, `/` to the Streamlit UI. The apps only ever define `/chat`, `/health`
and `/feedback` — the stage lives in the URL, not in the application code.

**Model:** `Qwen/Qwen3.8-27B-FP8` (Apache-2.0, ungated, ~31GB), served as
`qwen3`. vLLM `v0.29.0`, tool parser `qwen3_coder` — **not** `hermes`. Reasoning
parser `qwen3`; thinking is on by default at `xhigh` and every call opts out,
because a supervisor whose only job is picking a name from a list should not emit
a reasoning block first.

This was the highest-risk dependency in the whole session and it has now been
verified on the card: **60/60 valid first-attempt tool calls**, and **60/60
correct supervisor routing decisions** once `tool_choice="required"` was set.
Weight load is about 5 minutes cold and 20 seconds warm from the `hf-cache`
volume.

## Budget

$50 purchased. H100 80GB is ₹229.64/hour on-demand, billed per minute. A100 80GB
is ₹126.85/hour if cost needs cutting — build hours do not need the faster card,
but **both rehearsals must be on the H100**, because concurrency and KV cache
settings are card-specific and you do not want to be tuning them live.

| Activity | Hours | Cost |
|---|---|---|
| Build and first bring-up | 6 | ₹1,378 |
| Rehearsal 1 | 3 | ₹689 |
| Rehearsal 2 | 3 | ₹689 |
| Session | 2.5 | ₹574 |
| Buffer | 6 | ₹1,378 |
| **Total** | **~20** | **~₹4,708** |

**The main way this budget disappears is forgetting to pause.** One H100 left
running overnight is about ₹5,500 — more than the entire planned spend. `jl pause
<id> --yes` after every single session, without exception. Retained storage keeps
billing while paused, so tear the filesystem down once the session is over, not
just the instance.

Everything off the box is free: Phoenix and Qdrant run in containers, GitHub
Actions is within included minutes.

Two operational facts that have already bitten and will again:

- `jl resume` gives the instance a **new id, and sometimes the same IP with a new
  host key**. Run `make ci-secrets` after every resume — it clears the stale
  `known_hosts` entry, reinstalls the CI deploy key and rewrites the three
  GitHub secrets.
- Confirm GST treatment on the invoice. If the $50 was pre-GST, usable compute is
  about 18% less than the table above assumes. Still fits, but it eats the
  model-swap reserve.

---

## 0:00 — Framing

Stage 1 is already running on screen. Ask the room one question: what stops you
giving this URL to a client today?

Take answers and write them up. They will name most of the syllabus themselves —
it breaks and we don't know why, anyone could abuse it, we can't tell if it's
getting better. Map each answer to a segment. The session becomes answers to
their own list rather than a lecture.

Announce the ground rule: questions at the end, not during. Say it out loud. Two
hours this dense will otherwise lose fifteen minutes to questions the session was
about to answer anyway.

## 0:04 — The model layer, and what a token costs

Nothing else can run until the model is up, so start here.

Walk the `vllm` service in `compose.model.yaml`: which checkpoint, the FP8
quantisation, how much GPU memory it is told to claim, `--max-num-seqs`, and the
tool-call parser that Stage 3 depends on. The weights are already loaded — never
load them live.

Then look at what you can only see when the GPU is yours.

**GPU memory.** Show `nvidia-smi`. Weights are about 31GB of the 80GB; the rest
is KV cache and headroom. The point to land: **the KV cache, not the weights, is
what limits how many users you can serve at once.** FP8 instead of BF16 is what
bought that headroom — the same model at BF16 is about 57.5GB and leaves very
little.

**Batching.** Fire one request, then thirty-two at once. Total time barely moves.
That is continuous batching, and seeing it is far more convincing than being told.

**Then the money, measured.** Run `make cost`. It sweeps concurrency on the real
card and divides throughput into the real hourly rate. Measured 2026-09-09,
H100 80GB in IN2 at ₹229.64/hour, 256-token outputs:

| concurrent | tok/sec | median latency | ₹ / 1M output | USD / 1M output |
|---|---|---|---|---|
| 1 | 76 | 1.09s | 839 | 9.54 |
| 4 | 203 | 1.52s | 314 | 3.57 |
| 8 | 434 | 1.77s | 147 | 1.67 |
| 16 | 793 | 1.96s | 91 | 0.91 |
| 32 | 1231 | 2.11s | 52 | 0.59 |

**16.2× more throughput from 1 to 32 concurrent, while median latency only goes
1.09s to 2.11s.** Unit cost swings 16× on utilisation alone.

The rupee column is what you actually pay. The dollar column converts at
₹88/USD, which is what `scripts/cost_report.py` assumes — today's rate is nearer
₹95, so the real dollar cost is a few percent lower than shown. Every ratio below
uses the same basis on both sides, so the comparison holds either way.

Now the comparison, and do it against **the same model** so nobody can argue the
difference is capability. Qwen3.8-27B is sold by hosted providers at **$2.00 to
$3.20 per million output tokens** (OpenRouter's provider table, checked
2026-09-09). Use the cheapest, $2.00, because it is the hardest bar for
self-hosting to clear — picking an expensive provider would flatter our card.

That gives one number worth writing on the board:

> **Break-even sits between 4 and 8 concurrent requests — about 7.**

The card needs to be pushing about 362 tokens a second before owning it beats
renting the same model by the token. Below that, buying is cheaper. Above it your
own card wins, and at 32 concurrent it wins by about 3.4×. With one user at a
time you are paying **4.8× more** than you would to just buy it.

`make cost` prints this break-even line itself, so the number comes off the card
rather than off a slide.

This is the segment's payoff and it does not flatter self-hosting. Say it
plainly: **utilisation decides, not the hourly rate.** A GPU is a fixed cost you
pay whether anyone is asking questions or not, so the honest reasons to self-host
are usually data residency, predictable spend and control over the model — not
price. Price only follows if you can keep the card busy.

Keep this on the board. It gets collected at 1:44.

> **Before the session:** set `HOSTED_COMPARISON` in `scripts/cost_report.py` to
> the rate you intend to quote, and name the provider and model on screen. The
> verdict depends entirely on what you compare to, and a room that spots an
> unfair comparison will discount the whole segment.

## 0:18 — Stage 1: the plain chatbot

Deliberately boring code. One endpoint, one model call, in-process history. The
interesting part isn't the chatbot, it's what happens when you try to put it in
front of people.

**Where state goes.** Restart the container and watch the conversation vanish.
Anything you kept in a variable is gone on restart, and gone again if you ever
run two copies. Show where it would have to live instead.

**Where the keys live.** Show the wrong way first — a value hardcoded in the
source, then one sitting in a compose file that's about to be committed. Then fix
it: `.env`, git-ignored, injected at runtime.

Be honest about the size of that fix. A `.env` file on one box is the minimum,
not the standard — a managed platform gives you a secret store with versioning
and audit logs. Naming the gap is the lesson.

There is a nice wrinkle here worth thirty seconds: **this stack barely has any
secrets.** The model is Apache-2.0 and ungated, so `HF_TOKEN` is optional and only
raises your download rate limit. Qdrant is on the same private network and needs
no credential. What that shows is that "manage your secrets properly" is not a
ritual you perform on a fixed list — it is a question you ask of each dependency,
and sometimes the answer is that there is nothing to manage. Compare it to 1:22,
where a real long-lived credential does exist and is a genuine weakness.

**Which port, and who can reach it.** The app listens inside the container; Caddy
routes the outside world to it, and the three app services are not published at
all. Show the mapping. Then ask who else can reach port 8000. The model endpoint
has **no authentication in front of it** and it is published on a public IP —
anyone who finds it can use your GPU. Say what you would do about it in
production and say why it is still open here.

Deploy it: `docker compose up -d chat-v1`. Hit `/v1/chat` through the proxy. It's
live.

Close by saying: this is how a prototype ships. In an hour we'll see why it isn't
how a product ships.

## 0:32 — Turning on tracing

Do this now, while a request is still small enough to read in full.

Phoenix is already in the compose file. Six lines in `app/observability.py` and
every model call becomes visible. Run one request and read the trace together:
how long it took, how many tokens, and the actual prompt that got sent. That last
one usually surprises people — once you count the system prompt, the template and
the history, it is much bigger than what the user typed.

One convenience worth pointing out, because it is what makes the rest of the
session navigable: **every `/chat` response carries the `trace_id` of its own
request.** Paste it straight into Phoenix's search box. No hunting.

The reason to do this early is practical. A two-span trace teaches you to read
traces; a forty-span tree does not. By Stage 3 the tree will be large, and this
is what makes it readable.

Worth saying once: the instrumentation is standard OpenTelemetry, and because
vLLM speaks the OpenAI protocol, it traces a self-hosted model exactly as it
would a hosted one. We never touch it again for the rest of the session.

Put Phoenix on the second screen now and leave it there.

## 0:40 — Stage 2: RAG, and state leaving the container

Move quickly. The room already knows RAG. Only the deployment lesson is new.

The lesson: **the index cannot live inside the application container.** Containers
get rebuilt and restarted, and an index sitting on an app container's filesystem
is either lost on the next deploy or inconsistent between copies. So it moves out
— its own container, its own named volume, its own lifecycle — and the
application keeps only a connection string.

Be precise about what that does and does not buy you, because here the vector
database is on the same box:

- **What it does buy:** `chat-rag` can be rebuilt, restarted and redeployed all
  session without touching the index. That gets demonstrated for real at 1:22,
  when the pipeline restarts a service and the data survives.
- **What it does not buy:** the index has no replication, no backup, and it dies
  with the machine. Moving from one container to a managed service is one line in
  `.env` — `QDRANT_URL` — and that line is the whole difference between "survives
  a deploy" and "survives a disaster."

Name what just happened. Even on a single box, the project stopped being one
program and became a distributed system. Everything harder about the rest of the
session follows from that.

This is also where the Dockerfile gets interesting — a real base image, real
system dependencies, and a layer order chosen so that changing application code
doesn't reinstall everything. Show a rebuild taking six seconds because the
dependency layer was cached.

One detail that pays off later: **embeddings run on CPU**, via fastembed with
`BAAI/bge-small-en-v1.5`. Retrieval never touches the GPU, which is why it does
not compete with generation for KV cache at 0:58.

Deploy: `docker compose up -d chat-rag`. Then look at the trace — there is a
retrieval span in it now, showing which documents came back. For the first time
you can *check* whether the answer came from the documents or whether the model
filled in the gaps itself.

> **The corpus has two halves, and the difference shows on screen.** 50 articles:
> 42 generated from real incidents in the source dataset, and 8 hand-written
> policy and how-to documents. Both kinds of question now answer well — "how do I
> reset my password" returns the policy article with the portal URL and the
> password rules, cited.
>
> Two things worth demonstrating rather than avoiding. The dataset has 14 issue
> families and, for example, 26 separate incidents titled "GlobalProtect VPN
> disconnects immediately", so there are genuine near-duplicate documents for
> retrieval to get wrong. And on *"how do I get access to a finance shared
> drive?"* two incident articles titled "Access denied to Finance shared drive"
> outrank the policy article that actually answers it — 0.818 and 0.811 against
> 0.808 — because the incident titles match the question lexically. The answer
> still comes out right, since all three are inside the retrieval window, but it
> is a live example of retrieval preferring familiar phrasing over the correct
> document.

## 0:49 — Guardrails, in and out

> **Timing: this segment is now overcommitted.** The slot is nine minutes and the
> notes below are roughly eight minutes of talking *before* the live demos.
> Something has to go. In order of what to cut first:
>
> 1. The two blocked inputs — describe them instead of running them, the trace
>    screenshot makes the point
> 2. "The guard we tried to add, and didn't" — self-contained, nothing later
>    depends on it
> 3. The guard-eval table — but keep the 14% number even if you cut the table
>
> Do not cut the tool guard at 0:58 to make room. That one is the reason the
> session exists.

Written by hand rather than pulled from a library, so people see the mechanism
instead of a config file.

**On the way in**, before anything reaches the model: injection heuristics,
personal data, absurd input lengths. The cheapest possible place to say no.

**On the way out**, before anything reaches the user: does the response match the
shape we promised, and does it violate any policy we care about.

Run two inputs built specifically to get blocked. Show them blocked, then show
what the system would have returned otherwise. Find both rejections in the trace
— guardrails are part of the recorded history, not something happening off to the
side.

**Then do the thing almost no session does: score your own guard and admit the
result.** `make guardeval` runs `input_guard` against the dataset's PII answer
key. Measured:

| | |
|---|---|
| Email addresses caught | 100% |
| Phone numbers caught | 72% |
| **All PII in the corpus caught** | **14%** |
| False positives on safe strings | 0.5% |

A hand-rolled regex guard catches the two things you thought of and is blind to
almost everything else. That is not a bug in this implementation — it is what
pattern-matching guards are. The lesson: **a guardrail you have not measured is a
guardrail you are guessing about**, and the answer-key test that produced this
table took less time to write than the guard did.

Two things this sets up. First, it is an honest argument for layering — a weak
cheap filter in front is still worth having, as long as nobody downstream is
relying on it having worked. Second, and this lands harder here than on a managed
platform: a hosted model arrives with its own safety filters already applied.
Ours has none. **Everything protecting this system is code we wrote, and we have
just measured how good that code is.** Full control means full responsibility.
Say it plainly to a room that may be pitching self-hosting to clients.

### The guard we tried to add, and didn't — 4 minutes

*Budget this at four minutes and no more. If the segment is running long, cut
straight from the table above to "the third place guardrails belong". Everything
here is real and none of it is load-bearing for a later segment.*

Ask Stage 1: **"explain chatgpt."** It explains ChatGPT, at length, helpfully.

All three guards ran. All three correctly allowed it — the input was short and
clean, Stage 1 calls no tools, and the answer leaked no prompt, no PII, no
security bypass. **The policy simply had no opinion about scope.** This is worth
sitting with for a second: "we have guardrails" is not a property of a system,
it is a list, and this was not on the list.

So add a clause. Three attempts, each measured against cases written down first:

| Clause | Result |
|---|---|
| "discusses a topic other than internal IT support" | Blocks a *pure* off-topic answer 6/6. **Allows the realistic one 6/6** — Stage 1 hedges, explaining ChatGPT and then offering help with "its integration within our internal IT systems", which reads as on-topic |
| "explains any external product, even briefly" | Catches the hedge. Also blocks half the corpus — **BitLocker, Okta, GlobalProtect and Intune are all external products**. Eval 97.9% → 72.9%, smoke test failed on all three stages |
| "answers a question that is not a request for internal IT support" — *with the question shown to the judge* | 8/8 on a hand-built case set. Then blocked **every policy question** in the eval: "what is the policy on requesting a new laptop" reads as HR. Eval 97.9% → **33.3%**, hard fail |

Then stop, and ship nothing. **A guard that intermittently refuses correct
answers is worse than the gap it closes**, and Stage 1 answering off-topic is a
teaching point rather than a defect — it is the answer to the question you asked
the room at 0:00.

Three things to draw out, in order of how much they are worth:

1. **The third attempt is the dangerous one.** It scored 8/8 and was wrong. The
   case set contained no policy questions — the half of the corpus added that
   same day — so it measured the wrong thing, confidently, and produced a number
   that justified shipping. A measurement is only as good as the cases you
   thought to include, and the cases you forget are the ones you just changed.
2. **The boundary is genuinely ambiguous.** "Internal IT support" versus "HR
   policy" is not a line one sentence can carve in this corpus. That is a real
   answer to "just add a guardrail for it" — some rules are not expressible as
   prose, and want a classifier or an intent allowlist instead.
3. **A prose policy clause is engineering, not writing.** One word — "discusses"
   versus "explains… even briefly" — flips it from useless to overreaching. The
   only way to know is to measure it against cases you wrote down first.

**And the bug found on the way, which is the one that would have cost you this
demo.** The policy judge was running at `temperature=0.7` — the model card's
*generation* setting — on a call that classifies rather than writes. It blocked a
correct answer **3 times in 15**. A 20% flake rate in a release gate: the smoke
test intermittent, the deploy gate intermittent, one CI run red for no reason
anybody could see. Now `temperature=0.0`, with a test asserting it.

Show that one on screen if you show nothing else here. It looks like the
architecture misbehaving and it is one wrong sampling parameter.

One thread to leave hanging, because 1:13 picks it up: **the judge can only
assess what it is shown.** It never sees the retrieved documents, so it cannot
tell a cited fact from an invented one — a "must not invent" clause is
unjudgeable by construction. That exact mistake has now been made three times in
this repo: in this policy, in the eval rubric, and in the third topicality
attempt. There is a test whose only job is to catch a fourth.

Flag that there's a third place guardrails belong, and it only exists once you
have multiple agents. That's next.

## 0:58 — Stage 3: the agents

Walk the graph in `app/graph_stage3.py`: a supervisor routing to three workers —
a retriever, a tool agent and a synthesizer. Each node becomes a span, so the
picture on the slide and the picture in Phoenix are the same picture.

Mention the one setting that made routing reliable: **`tool_choice="required"`**.
Without it the supervisor sometimes answered in prose instead of picking a
worker. With it, 60 out of 60 routing decisions were correct. That is a
one-parameter fix for a failure mode that looks like a model problem, and it is
worth ten seconds because learners will hit it.

Then the third guardrail, and it's the important one. In a single-agent system the
model calls tools you chose and configured. In a multi-agent system, **one
agent's output becomes another agent's tool input** — nobody wrote that input and
nobody reviewed it. That surface doesn't exist in simpler systems, and it's the
one almost nobody guards. Every tool call gets an allowlist and argument
validation, and the rejection shows up as its own span.

Run it. The trace tree is the whole system laid out visually, and the hand-off
between agents — abstract last week — is right there as one span sitting inside
another.

Then break it deliberately. A malformed tool argument works well. Debug it from
the trace alone, without opening a log file. That's the payoff for everything
since 0:32.

Finally, the waterfall, and the number that stings. One user request fans out
into a dozen model calls **made sequentially**. So a single user's Stage 3 request
is a batch of one, and from the 0:04 table a batch of one costs **₹839 per million
tokens — the worst row on the board, 4.8× what buying the same model would cost.**
Batching only helps you when many people are asking at once. Go back to
`nvidia-smi` and show the KV cache under real pressure.

This is the uncomfortable moment of the session and it should be. On your own
hardware, the cost of multi-agent shows up as a concurrency ceiling rather than
an invoice, which makes it easy to ignore right up until it isn't.

## 1:13 — Testing something that doesn't behave the same way twice

The idea that makes this teachable: sort tests by whether the thing is
predictable, not by how big it is.

**Predictable, so test it properly.** Guardrails are ordinary functions with
ordinary inputs and outputs. Output schemas either match or don't. Routing can be
tested by handing the supervisor a state and asserting which worker it picks, with
the model stubbed. None of these need a model call. The suite is **63 tests and
finishes in about a second locally**, 2.0–2.4s in CI.

**A judge can only assess what you show it.** This is the single most
transferable idea in the segment, and it is worth three minutes because the room
will otherwise spend a month learning it the slow way.

The output guard's judge sees the answer. Nothing else. Not the retrieved
documents, not the question — until we passed the question in deliberately. So:

- *"must not invent an approval workflow"* is **unjudgeable by construction**. A
  cited workflow and an invented one look identical from the answer alone. When
  this clause was in the guard's policy it blocked correct answers 3/3; when the
  same idea reappeared in the eval rubric it scored a correct, fully-cited answer
  **1/5**.
- Worse, that rubric had scored the *same question* 5/5 the week before — back
  when the corpus could not answer it and "I don't know" was the right reply.
  **Improving the corpus made the score go down.** A regression in the
  measurement, not in the system, which is a genuinely disorienting thing to
  debug if you have not seen it before.
- Topicality has the same shape but a different fix. It is a property of the
  *(question, answer) pair* — "explaining ChatGPT" and "explaining why BitLocker
  fails" are the same kind of answer, and only the question separates them. The
  evidence was missing, so we handed it over. Groundedness could not be fixed
  that way, because the evidence is the whole corpus — which is precisely why
  groundedness is an eval and not a guard.

Two rules fall out, and they are cheap to state and expensive to learn:
**write the clause so it can be answered from what the judge can see**, and
**when a rubric and a system disagree, suspect the rubric first.**

There is now a test, `test_policy_clauses_are_all_judgeable_from_the_answer_alone`,
whose entire job is to fail if somebody writes a fourth one. Show it. A three-line
test that encodes a lesson learned three times is a good advertisement for tests.

**Not predictable, so score it instead.** Whether an answer is *good* can't be
asserted. You run it across a batch of examples, score the batch, and check the
average clears a line you set — `PASS_THRESHOLD = 0.70` in `evals/run_eval.py`.
That's a release decision, not a per-commit one.

Run the fast suite live. Its speed is the argument — if the predictable tests
finish in a second, nobody needs convincing they should run on every change.

Then prove the scored gate is real rather than decorative, by running the **same
dataset against two different stages**:

| Target | Score | Gate |
|---|---|---|
| Stage 3 (`/v3`) | 97.9% | PASS, exit 0 |
| Stage 1 (`/v1`) | 31–34% | **FAIL, exit 1** |

A gate that never fails is not a gate. This one fails on a version that genuinely
cannot answer the questions, which is exactly what you want it doing at 1:22.

> Be precise if you quote both numbers: **they were measured on different
> datasets.** Stage 1's 31–34% is from the original 8-example set; Stage 3's
> 97.9% is from the current 12-example set, which added four policy questions
> once the corpus could answer them. Re-run Stage 1 against the 12-example set
> before putting the two side by side on a slide —
> `EVAL_ROUTE=v1 python evals/run_eval.py`.

The line to land: people try to assert an exact response from a language model,
watch it fail randomly, and conclude agent systems can't be tested. They can. The
checks just live in different places, and some are thresholds rather than
assertions.

## 1:22 — The build pipeline, and the third deploy

Open with an honest admission. Twice now I deployed by typing a command into a box
I was already logged into. That's how a demo ships. It depends on my shell
history, nothing checked it before it went out, and if it breaks there's no way
back.

So instead, push a commit and let `.github/workflows/deploy.yml` run. Four jobs,
green end to end in about three minutes:

| Job | Trigger | What it does |
|---|---|---|
| `test` | every PR and push | install, `ruff`, the 60 fast tests |
| `build` | push to `main` | build the app image, tag it with the commit SHA, push to GHCR |
| `deploy` | after build | SSH to the instance, pull that SHA, restart `chat-agents` only, smoke test |
| `eval` | after deploy | score the deployed Stage 3; non-zero exit fails the job |

Two things to point at while it runs.

**The image is tagged with the exact commit SHA.** Not `latest`. That is what
makes "which version is in production" a question with an answer, and it is what
would make a rollback possible.

**The two credentials in this file are a lesson sitting side by side.** The
`build` job authenticates with `secrets.GITHUB_TOKEN` — minted per run, expires
with the job, scoped to one thing. The `deploy` job authenticates with
`GPU_SSH_KEY`, a long-lived private key in repository secrets: it does not
expire, it grants shell access rather than one permission, and it leaves no
per-run audit trail. On a managed cloud you would federate an identity and have
no stored key at all. **Read the weakness out loud rather than presenting it as
good practice** — the contrast with the job directly above it is the whole point,
and it is a callback to the secrets discussion at 0:18.

Also name what step 4 is not: it is a restart, so there are a few seconds of
downtime and no way back except redeploying the previous image. Which brings us
to the last segment.

Talk over the pipeline run. When it goes green, Stage 3 is live — deployed by a
pipeline rather than a person.

> **Fallback:** if GitHub Actions queues, give it ninety seconds and then cut to
> the recorded green run. This is the only segment with an external dependency you
> do not control.

## 1:33 — Closing the feedback loop

The pipeline just scored the new version against a set of examples. Where did
those come from?

From users. A thumbs-down in the Streamlit UI posts to `/v{n}/feedback`, and the
**app** — not the UI — writes a `user_feedback` annotation onto that request's
trace, inside a traced process, so the write gets its own span. Filter Phoenix for
the unhappy ones. `make dataset` turns them into
`evals/datasets/from_feedback.json`. Change one thing — a prompt, how many
documents get retrieved, a routing rule — and run the set again to see whether
the score moved.

Do this with real thumbs-downs collected from the room earlier in the session.
Ask for them explicitly around 0:58 so there is something to work with here.

The chain is the lesson: no tracing means no examples, no examples means no
measurement, and without measurement "we improved it" is just a feeling. And
because the pipeline scores against that same set, real user complaints become
the thing that blocks a bad release.

> Two practical notes. Only feedback collected **after** the root span began
> carrying `input.value` can be recovered — earlier annotations have no question
> attached and get skipped. And one thumbs-down is not a regression suite; this
> segment demonstrates a mechanism, and you should say that the real version of it
> takes weeks of traffic.

## 1:44 — Three versions, one question — and how real teams roll out

All three are live. Ask each the same question and put them side by side: how long
each took, how many tokens each burned, and how good each answer was. The eval
numbers from 1:13 already give you the quality column — 31–34% against 96.9–100%.

Then collect the cost board from 0:04 and ask it plainly: **did the agents earn
their complexity here?**

For this use case the answer has a shape worth saying out loud. Stage 3 is
dramatically better at answering the questions — 96.9–100% against 31–34%, and
that part is not close. The cost is two separate multipliers, and it is worth
keeping them apart:

- **About twelve times the tokens per question** as Stage 1, because a supervisor
  plus three workers means a dozen model calls where the chatbot made one. On the
  same card that is roughly twelve times the cost per question.
- **Each of those tokens priced at the batch-of-one rate**, because Stage 3's
  calls run sequentially — so 4.8× what buying the same model by the token would
  cost, until you have enough concurrent users to fill the card.

Twelve times the tokens is the architecture's honest price and you pay it
wherever you run. The 4.8× is not the architecture's fault at all — it is what
owning an under-used GPU costs, and it goes away as soon as the room is busy.
Whether the whole trade is worth it depends on what a correct answer is worth,
and that is a business question, not an architecture one.

Multi-agent is a cost you pay when you need the capability. It isn't a default and
it isn't a sign of sophistication.

Close with the thing we didn't build, on the whiteboard, in about three minutes:

**Canary releases.** Version 1 is live serving everyone; you've built version 2.
Rather than switching everyone at once, you send a small slice of real traffic —
say ten percent — to the new version, watch the traces and the thumbs-downs, then
either ramp to a hundred percent or pull it back. The name comes from canaries in
coal mines: a small early warning before the whole thing goes bad.

This matters more for agents than for ordinary software, because you can never
fully know whether an agent's answers are good before real users hit it. Evals
give you an average on a fixed set; real questions are messier. So you expose a
few users and decide from real evidence.

On a managed platform this is one command and the rollback is a config change,
not a redeploy. On our setup you would build it yourself with weighted routing in
Caddy. We didn't — and that's the honest trade for owning the whole stack. Worth
knowing it exists and what it costs to not have it.

## 1:51 — Questions

---

## What we deliberately left out

- **Writing code live.** Not possible alongside model serving, three deploys, and
  a pipeline in two hours.
- **Depth on RAG.** The room already has it. Nine minutes, deployment lesson only.
- **Questions during the session.** The biggest risk to the schedule.
- **Canary routing, built.** Explained on the whiteboard, not implemented.
  Building weighted routing live on self-managed infrastructure is fragile, and
  the concept lands fine without it.
- **Git tags per stage.** All three stages have to run *at the same time* during
  the session, so the runtime design is one image with a `STAGE` variable, not
  three tagged commits. Learners get the three `app/graph_stage*.py` files side by
  side instead — same teaching value, and it matches what actually runs.
- **Autoscaling and multi-instance.** One box, one GPU. Say what would change with
  more.
- **Authentication on anything.** The model endpoint and Qdrant are both
  published without it. Named at 0:18 as a deliberate gap, not fixed.
- **Managed alternatives.** One sentence: Cloud Run or similar gives you secrets,
  traffic control and keyless CI for free, at the cost of sending your data there.
  Bedrock AgentCore would host the agent stage well but not the chatbot and RAG
  stages in the same shape, which would break the ladder.

## Before the session

**Blocking — nothing else matters if these fail:**

- [x] Model and tool-call parser verified — 60/60 tool calls, 60/60 routing
- [ ] `HOSTED_COMPARISON` set to a rate you have checked, with the provider and
      model named on screen. The 0:04 and 1:44 verdicts both depend on it.
- [ ] Pipeline run green **twice**. It has been green once.
- [ ] `make smoke` passing — 23 assertions, about 15 seconds
- [ ] Full compose stack brought up from scratch at least twice, timed

**Content:**

- [ ] Demo questions chosen and rehearsed. Both incident- and policy-shaped
      questions work now — see the corpus note at 0:40
- [ ] Blocked inputs tested end to end against the deployed Stage 3
- [ ] Rewrite the 0:04 narration around the measured H100 numbers if you are
      working from older slides; the old draft quoted an A100 at $1.49/hr
- [x] ~~Decide whether to add policy how-to articles to the corpus~~ — done,
      8 added in `policy/`, corpus is 50 articles. Historic note follows:
      to state the gap on screen and only ask incident questions

**Operational:**

- [ ] `.env` populated (`HF_TOKEN` optional), corpus indexed with `make index`
- [ ] Weights pre-downloaded to the persistent volume — warm load is 20 seconds,
      cold is 5 minutes
- [ ] Phoenix confirmed receiving traces from all three app services
- [ ] Caddy routes verified from outside the instance, on a phone if possible
- [ ] **GHCR package made public** — one click in package settings, no API for it.
      Otherwise learners cannot pull the image from the repo you hand them.
- [ ] `make ci-secrets` run after the final resume, so the three GitHub secrets
      match the live instance
- [ ] Recordings made of the model bring-up, all three deploys, and one green
      pipeline run
- [ ] Second screen arranged, Phoenix visible from 0:32 onward
- [ ] **Instance paused** after every rehearsal, without exception

## If something goes wrong

| Problem | What to do |
|---|---|
| Model slow to start | Bring the stack up before the room arrives; never load weights live |
| Tool calls come back malformed | Fall back to the recorded run; this is why it's rehearsed twice |
| GPU out of memory under the Stage 3 fan-out | Lower `--max-num-seqs` and the KV cache allocation; have working values noted in advance |
| A deploy fails | Play the recording and keep going |
| Pipeline hangs or queues | Give it ninety seconds, then cut to the recorded run |
| SSH refuses after a resume | `ssh-keygen -R <ip>`, then `make ci-secrets` |
| Retrieval looks broken | You probably asked a policy question. Switch to an incident question |
| Instance unreachable | Local Docker Compose on a laptop with a much smaller model, rehearsed as a cold fallback |
| Running behind at 1:22 | Shorten testing by showing the tests rather than running them. Never cut the pipeline or the feedback loop |

## After the session

Instance paused immediately, then torn down along with its storage — retained
storage keeps billing after a pause. Learners do not need infrastructure of their
own.

What they take home:

- The repository — one image, three graph files, and a compose stack that runs on
  any GPU box
- The measured cost table from 0:04, including the break-even concurrency, so the
  self-host-versus-buy question is something they can redo with their own numbers
- The guard eval table from 0:49, as an argument for measuring guardrails rather
  than trusting them
- An export of the session's traces, so the trace-reading segments can be
  revisited
- The runbook
