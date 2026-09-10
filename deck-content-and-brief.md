# Serving and Shipping It Yourself — deck content & design brief

Everything needed to regenerate this 46-slide deck in Claude Design. Two parts:
the **design system** (§1) and the **slide-by-slide content** (§2).

Session: 2 hours, Nunnari Labs weekend batch, final session.
Subject: deploying a chatbot, a RAG chatbot and a multi-agent system on your own
GPU (JarvisLabs H100 · vLLM · LangGraph · Arize Phoenix · Docker Compose).

---

## 1. Design system

### Canvas
- **1280 × 720 px per slide** (16:9), one artboard per slide, 46 slides.
- **54 px padding** on all four sides. Usable area 1172 × 612.
- Content that exceeds the frame is **clipped, not scaled** — see §1.6 for the
  height budget that actually fits.

### Palette
| Token | Value | Used for |
|---|---|---|
| Ground | `#0c0b0a` | slide background, warm near-black |
| Panel | `#171411` at 60% | code blocks, cards |
| Ink | `#f2ede6` | primary text |
| Dim | `#a39a8e` | captions, notes, first table column |
| Faint | `#6f665c` | footers, secondary annotation, `__dim__` spans |
| Rule | `#2a2622` | table rules, box outlines |
| Accent | `oklch(0.74 0.15 62)` ≈ `#e29349` | kicker, emphasis, the one hot element per slide |

One accent only. Dark throughout — no light slides.

### Type
- Display / body: **Space Grotesk** (400/500/700), fallback `system-ui, -apple-system, "Helvetica Neue", sans-serif`
- Numbers, code, labels: **JetBrains Mono** (400/700), fallback `ui-monospace, "SF Mono", Menlo, monospace`
- Google Fonts is the only permitted font host in an artifact. PNG/PDF export
  cannot embed them, so exports fall back — pick fallbacks with close metrics.

### Repeated chrome on every slide
- **Kicker**, top left: 15 px mono, uppercase, letter-spacing 0.14em, accent colour.
- **Segment label**, bottom left: 13 px mono, faint (e.g. `0:49 Guardrails`).
- **Slide number**, bottom right: 13 px mono, faint, `NN / 46`.
- Content column is vertically centred between kicker and footer.
- No accent stripes, no bars, no borders-on-one-edge. The kicker is the motif.

### Inline emphasis convention
Three markers appear in the content below:
- `**text**` → accent colour, weight 500
- backtick-wrapped text → mono, ink colour, 0.9em
- `__text__` → faint colour (de-emphasis)

### 1.6 Layout types and their height budget

Eight layouts. The figures are what actually fits in 612 px of usable height —
measured in a browser, not estimated.

| Layout | Structure | Type sizes | Fits |
|---|---|---|---|
| `title` | kicker, huge headline, 120×3 accent rule, sub, mono meta lines | 76 / 26 / 15 | 1 slide |
| `statement` | kicker, big statement (may contain blank lines), optional caption | 46–62 / 18–22 | caption ≤ 3 short paragraphs |
| `bignum` | kicker, huge number + mono unit beside it, bold label, caption | 138 / 34 / 19 / 18–21 | **caption ≤ 2 short paragraphs — this is the tightest layout** |
| `table` | kicker, heading, 2–5 column table with horizontal rules only, note | 40 / 19–21 / 17–19 | ≤ 6 rows with a one-line note |
| `bullets` | kicker, heading, 4–6 dot bullets, note | 44 / 22–24 / 17 | ≤ 5 bullets of ≤ 2 lines |
| `cols` | kicker, heading, 2–4 tinted cards (tag / title / body), note | 42 / 27 / 19 | 2–4 cards |
| `code` | kicker, heading, mono panel (`white-space: pre-wrap` — **`pre-line` destroys column alignment**), note | 42 / 21–24 / 17 | ≤ 10 lines |
| `svg` | kicker, heading, inline SVG diagram, note | 40 / — / 17 | diagram ≤ 290 px tall |

**The single hardest rule:** every `note` is ONE line. They are not narration —
the narration lives in `session-plan-jarvislabs.md`. Notes that grow into
paragraphs are what made 23 of 46 slides overflow on the first attempt.

### 1.7 Canvas layout
Rows of five, left to right, top to bottom. x-stride 1410 px, y-stride 930 px
(≥ 80 px horizontal and ≥ 120 px vertical clearance, because the artboard name
strip sits above each frame). Single page. Launch on the canvas view.

---

## 2. Slides


### 01 · Main

`title` layout · segment `Nunnari Labs`

**Kicker** — Weekend batch · final session · 2 hours

**Headline**

> Serving and Shipping It Yourself

**Caption**

> Chatbot → RAG → Multi-Agent, on your own GPU.

**Meta lines**

- `H100 80GB` · `vLLM` · `LangGraph` · `Arize Phoenix` · `Docker Compose`
- One use case. Deployed three times. Nothing written live.

---

### 02 · TheQuestion

`statement` layout · segment `0:00 Framing` · headline 62px

**Kicker** — The question

**Headline**

> You have built agents. You have built chatbots.
> 
> Do you know how one goes to **production**?

**Caption**

> Before we start: what stops you giving this URL to a client today? Say them out loud — you will name most of the next two hours yourselves.

---

### 03 · Ladder

`cols` layout · segment `0:00 Framing`

**Kicker** — The shape of the session

**Headline**

> One use case, deployed three times. Each rung adds exactly one production problem.

**Cards**

- **Stage 1 · 0:18** — Plain chatbot
  State, secrets, ports, cold start. What it takes to put anything on the internet.
- **Stage 2 · 0:40** — RAG chatbot
  The index cannot live in the container. You are now a distributed system.
- **Stage 3 · 0:58** — Multi-agent  *(accent card)*
  Fan-out, timeouts, cost blow-up, and the guardrail only agents need.

**Note** (one line, dim, below the content)

> Ground rule, announced now: **questions at the end, not during.**

---

### 04 · TheModel

`table` layout · segment `0:04 The model` · body 19px · note 17px

**Kicker** — Topic 1 · the open model

**Headline**

> `Qwen/Qwen3.8-27B-FP8` — and why each of these numbers matters later

**Table header** — `` · `value`

**Table rows**

|  | value |
|---|---|
| Licence | **Apache-2.0**, ungated |
| Weights on disk | ~31 GB FP8 __(57.5 GB at BF16)__ |
| Layers | 64 — of which **16 are full attention** |
| Attention heads / KV heads | 24 / **4** |
| Head dim · context | 256 · 32,768 __(capped from 262k)__ |
| Tool calling | native, parser `qwen3_coder` |

**Note** (one line, dim, below the content)

> The two bold rows decide how many users this card serves.

---

### 05 · ModelChoice

`statement` layout · segment `0:04 The model` · headline 50px

**Kicker** — How the model was actually chosen

**Headline**

> Not the leaderboard. **One constraint: can the supervisor emit a well-formed tool call, a dozen times in a row?**

**Caption**

> A Stage 3 supervisor that emits a malformed tool call fails live, in the segment that matters most. So the first thing built was the gate, before any application code: 20 queries × 3 runs, pass mark 58/60.
> 
> Result: **60/60** tool calls. **60/60** routing decisions — the second only after setting `tool_choice=“required”`. Twenty minutes and about a dollar of GPU time, spent before anything else existed.

---

### 06 · WhyEngine

`statement` layout · segment `0:04 vLLM` · headline 52px

**Kicker** — Topic 2 · why a serving engine at all

**Headline**

> `model.generate()` in a `for` loop is not serving. It answers one person at a time and wastes most of the card doing it.

**Caption**

> A serving engine exists to solve three things you would otherwise build yourself: fitting many users' key-value caches into one pool of VRAM, keeping the GPU busy while requests arrive and finish at different times, and speaking a protocol your application already knows.

---

### 07 · EngineLandscape

`table` layout · segment `0:04 vLLM` · body 19px · note 17px

**Kicker** — Topic 2 · the landscape, September 2026

**Headline**

> What is actually production-grade, and what is a laptop tool

**Table header** — `engine` · `verdict`

**Table rows**

| engine | verdict |
|---|---|
| **vLLM** | Production · default choice · 200+ architectures |
| **SGLang** | Production · wins on shared-prefix + big MoE |
| TensorRT-LLM | Production · NVIDIA-only, heaviest ops burden |
| Hugging Face TGI | **Archived March 2026** — its README now points at vLLM |
| LMDeploy | Capable, smallest ecosystem |
| Ollama · llama.cpp | Laptops, CPU, edge. __No batching or multi-GPU story__ |

**Note** (one line, dim, below the content)

> TGI was the obvious answer two years ago. **Check your reference is still alive.**

---

### 08 · PagedAttention

`bignum` layout · segment `0:04 vLLM` · caption 17px · number 132px

**Kicker** — Topic 2 · why vLLM, part one

**Number** — 60–80%  ·  **unit** → under 4%

**Label**

> Memory wasted on KV cache fragmentation, before and after PagedAttention

**Caption**

> Naive serving reserves a max-length buffer per request, so a 200-token chat holds 32,000 tokens of VRAM hostage. PagedAttention borrows the OS answer: **blocks are pages, tokens are bytes, sequences are processes.**
> 
> **The memory it reclaims is your entire concurrency budget.**

---

### 09 · ContinuousBatching

`bignum` layout · segment `0:04 vLLM` · caption 17px

**Kicker** — Topic 2 · why vLLM, part two

**Number** — 16.2×  ·  **unit** measured on our card

**Label**

> Throughput from 1 to 32 concurrent requests — while median latency moves 1.09s → 2.11s

**Caption**

> Static batching waits for the longest request in the batch. Continuous batching schedules **per iteration** — one sequence finishes, a new one takes its slot.
> 
> It scales almost linearly until the KV pool runs out. **Then vLLM preempts, and latency falls off a cliff.**

---

### 10 · VllmFlags

`table` layout · segment `0:04 vLLM` · body 19px · note 17px

**Kicker** — Topic 2 · the flags that decide whether it works

**Headline**

> Six settings, and the failure mode of getting each one wrong

**Table header** — `flag` · `get it wrong and…`

**Table rows**

| flag | get it wrong and… |
|---|---|
| `--gpu-memory-utilization` | too low → constant preemption · too high → OOM at startup |
| `--max-model-len` | left unset → derived as **262k**, KV pool holds ~one request |
| `--max-num-seqs` | too high → preemption thrash, p99 blows up · too low → idle GPU |
| `--tool-call-parser` | wrong parser → tools **silently never fire** |
| `--reasoning-parser` | omitted → chain-of-thought leaks into `content`, breaks JSON |
| `--quantization` | forced against a self-describing checkpoint → own goal. Leave unset |

**Note** (one line, dim, below the content)

> Three of these six fail **silently** — the theme of the whole session.

---

### 11 · MemoryAnatomy

`cols` layout · segment `0:04 GPU`

**Kicker** — Topic 3 · what is actually in your VRAM

**Headline**

> Four consumers. Only one of them is what you buy concurrency with.

**Cards**

- **~40%** — Model weights
  Static. Paid once at load. 31 GB here.
- **~45%** — KV cache  *(accent card)*
  Grows with concurrency × context length. **The binding constraint.**
- **~5%** — Activations
  Transient, scales with batched tokens. Plus CUDA graphs.
- **~1 GB** — CUDA context
  Gone before a single weight loads.

**Note** (one line, dim, below the content)

> Training is bound by optimizer state and gradients. Serving is bound by the KV cache — and training has no KV cache at all.

---

### 12 · KVFormula

`code` layout · segment `0:04 GPU` · body 22px

**Kicker** — Topic 3 · the formula

**Headline**

> The one piece of arithmetic worth memorising

**Code panel** (preserve the column alignment exactly)

```
kv_bytes = 2                    ← one K tensor, one V tensor
         × num_layers           ← **full-attention layers only**
         × num_kv_heads         ← **not** num_attention_heads
         × head_dim
         × dtype_bytes          ← 2 for BF16, 1 for FP8
         × sequence_length
         × batch_size
```

**Note** (one line, dim, below the content)

> GQA reduction = attention heads ÷ KV heads. **Here that is 24 ÷ 4 = 6×.**

---

### 13 · KVTrap

`bignum` layout · segment `0:04 GPU`

**Kicker** — Topic 3 · the trap in our own model

**Number** — 24×  ·  **unit** overstated

**Label**

> What the naive KV calculation gets wrong on this exact model

**Caption**

> `full_attention_interval: 4` — **only every fourth layer is full attention.** Sixteen, not sixty-four. The other 48 are linear attention: constant state, no growing cache.
> 
> 64 layers → 4× high. 24 heads instead of 4 KV heads → 6× high. Both → **24×.**

---

### 14 · KVWorked

`code` layout · segment `0:04 GPU` · body 19px · note 17px

**Kicker** — Topic 3 · worked, with our real numbers

**Headline**

> From `config.json` to how many users fit

**Code panel** (preserve the column alignment exactly)

```
2 × 16 layers × 4 kv_heads × 256 head_dim  =  32,768 elements / token
                                           =  **64 KiB per token** (BF16)
one 32k-token sequence                     =  **2 GiB**

H100 80GB × 0.90                           ≈  71.7 GiB
  − FP8 weights                               28.75
  − context, activations, CUDA graphs        ~4
  − linear-attention state                   ~4.5
  = **KV cache budget                           ≈ 34.5 GiB**
```

**Note** (one line, dim, below the content)

> 34.5 ÷ 2 = **17 sequences at full 32k**, against `--max-num-seqs=32`. Real requests are shorter, so it holds — but that is the honest answer.

---

### 15 · ChooseGPU

`table` layout · segment `0:04 GPU`

**Kicker** — Topic 3 · choosing the card

**Headline**

> Capacity buys concurrency. Bandwidth buys tokens per second.

**Table header** — `card` · `VRAM · bandwidth`

**Table rows**

| card | VRAM · bandwidth |
|---|---|
| A100 80GB SXM | 80 GB · 2.04 TB/s · __no FP8__ |
| **H100 80GB SXM** __(ours)__ | 80 GB · **3.35 TB/s** · FP8 |
| H200 | 141 GB · 4.8 TB/s |
| L40S | 48 GB · 0.86 TB/s |
| L4 | 24 GB · 0.30 TB/s |

**Note** (one line, dim, below the content)

> Same model, same KV budget, **1.64× the bandwidth.** Capacity and speed are two separate purchases.

---

### 16 · CostMeasured

`table` layout · segment `0:04 Cost`

**Kicker** — Topic 4 · measured, not quoted

**Headline**

> `make cost` sweeps the real card and divides throughput into the real hourly rate

**Table header** — `concurrent` · `tok/s` · `median` · `₹ / 1M out` · `USD`

**Table rows**

| concurrent | tok/s | median | ₹ / 1M out | USD |
|---|---|---|---|---|
| 1 | 76 | 1.09s | **839** | 9.54 |
| 4 | 203 | 1.52s | 314 | 3.57 |
| 8 | 434 | 1.77s | 147 | 1.67 |
| 16 | 793 | 1.96s | 91 | 0.91 |
| 32 | 1231 | 2.11s | **52** | 0.59 |

**Note** (one line, dim, below the content)

> **Unit cost swings 16× on utilisation alone.** The hourly rate never changed.

---

### 17 · BreakEven

`bignum` layout · segment `0:04 Cost` · caption 17px

**Kicker** — Topic 4 · the number to write on the board

**Number** — ≈ 7  ·  **unit** concurrent requests

**Label**

> Below this, buy the same model by the token. Above it, own the card.

**Caption**

> Measured against **the same model** — Qwen3.8-27B is sold hosted at $2.00–3.20 per million output tokens. Cheapest used, because it is the hardest bar to clear.
> 
> At 32 concurrent we are 3.4× cheaper. **At one user at a time, 4.8× more expensive than buying it.**

---

### 18 · WhySelfHost

`bullets` layout · segment `0:04 Cost` · body 19px · note 17px

**Kicker** — Topic 5 · the honest reasons

**Headline**

> Self-host for residency, control and predictable spend. **Not for price.**

**Bullets**

- **Data residency.** "Our data cannot leave the country" is a real client requirement, and it is not negotiable by discount. This is the answer to it.
- **Control over the model.** It cannot be deprecated under you, rate-limited, silently updated, or repriced mid-contract.
- **Predictable spend.** A fixed hourly cost you can put in a budget, rather than a per-token bill that scales with success.
- **Price — only if you stay busy.** You pay for the card whether anyone is asking or not. An idle GPU is the most expensive inference on earth.

**Note** (one line, dim, below the content)

> **Utilisation decides, not the hourly rate.** If you cannot keep the card near saturation, the honest recommendation is to buy tokens.

---

### 19 · OneImage

`statement` layout · segment `0:18 Docker` · headline 50px · caption 21px

**Kicker** — Topic 6 · containerising it

**Headline**

> One image. Three containers. A `STAGE` variable picks which graph gets built at startup.

**Caption**

> The obvious design is three branches or three git tags. It does not work here, because **all three stages have to be running at the same time** during this session — that is the whole demo at 1:44.
> 
> So there is one Dockerfile, one image, one FastAPI app exposing `/chat`, `/health` and `/feedback`. The stage lives in the URL and in one environment variable. The three graph files sit side by side, which is also the best way to read the difference between them.

---

### 20 · ComposeStack

`table` layout · segment `0:18 Docker` · body 20px · note 17px

**Kicker** — Topic 6 · the whole stack on one box

**Headline**

> Eight containers, one `docker compose up -d`

**Table header** — `service` · `role · port`

**Table rows**

| service | role · port |
|---|---|
| `vllm` | the model, OpenAI protocol · 8000 __published__ |
| `chat-v1` `chat-rag` `chat-agents` | the three stages · 8101–8103 __internal__ |
| `qdrant` | vector database, own volume · 6333 |
| `phoenix` | traces, OTLP collector · 6006 |
| `ui` | Streamlit, thumbs control · 8501 __internal__ |
| `caddy` | reverse proxy — **the only way in** · 80 |

**Note** (one line, dim, below the content)

> Port 8000 is published with **no authentication in front of it**, on a public IP. Named on purpose, not fixed.

---

### 21 · StateLeaves

`cols` layout · segment `0:40 Data`

**Kicker** — Topic 6 · standing up the vector database

**Headline**

> The index cannot live inside the application container.

**Cards**

- **What it buys** — Survives a deploy  *(accent card)*
  `chat-rag` can be rebuilt and restarted all session without touching the index. Demonstrated for real at 1:22, when the pipeline restarts a service and the data is still there.
- **What it does not buy** — Survives a disaster
  On one box the index has no replication and no backup, and it dies with the machine. Moving to a managed service is **one line** — `QDRANT_URL` in `.env`. That line is the whole difference.

**Note** (one line, dim, below the content)

> Even on a single box, this stopped being one program and became a **distributed system**.

---

### 22 · WhyObserve

`statement` layout · segment `0:32 Tracing` · headline 52px · caption 21px

**Kicker** — Topic 7 · why observability, before you need it

**Headline**

> A Stage 3 answer is **a dozen model calls deep**. When it is wrong, which one was wrong?

**Caption**

> A chatbot you can debug with a print statement. An agent you cannot: the supervisor routed somewhere, a worker retrieved something, a tool was called with arguments a model wrote, a synthesizer wrote prose over the top. Any of those can be the fault, and the final answer looks the same either way.
> 
> So we turn tracing on **at Stage 1**, while a request is still two spans and you can read the whole thing. A two-span trace teaches you to read traces. A forty-span tree does not.

---

### 23 · Phoenix

`bullets` layout · segment `0:32 Tracing` · body 20px · note 17px

**Kicker** — Topic 8 · Arize Phoenix

**Headline**

> Open source, OpenTelemetry, six lines, and it runs in a container next to everything else.

**Bullets**

- **Auto-instrumentation.** One `LangChainInstrumentor` covers LangGraph — every node becomes a named span with no code of your own.
- **It is just OpenTelemetry.** Because vLLM speaks the OpenAI protocol, a self-hosted model traces exactly as a hosted one would. Nothing to port.
- **Spans carry the real payload** — the prompt actually sent, token counts, latency. The prompt is always bigger than anyone expects once you count the template and the history.
- **Annotations.** You can write back onto a trace after the fact. That is what turns a thumbs-down into an eval dataset at 1:33.

**Note** (one line, dim, below the content)

> Every response returns its own `trace_id`. Set up once at 0:32 and never touched again.

---

### 24 · WhyGuardrails

`bullets` layout · segment `0:49 Guardrails` · body 20px · note 17px

**Kicker** — Topic 9 · why guardrails, and where they go

**Headline**

> Three places, and the third one only exists once you have agents.

**Bullets**

- **On the way in** — injection heuristics, personal data, absurd lengths. The cheapest possible place to say no, before a single token reaches the GPU.
- **On every tool call** — allowlist plus argument validation. `OWASP ASI02 Tool Misuse`, `ASI07 Insecure Inter-Agent Communication`.
- **On the way out** — does the response match the shape we promised, and does it violate a policy we care about.
- **The framing worth stealing:** the *lethal trifecta* — private data, untrusted content, and a way to send things out. Any two are survivable. All three is an exploit.

**Note** (one line, dim, below the content)

> “We have guardrails” is not a property of a system. It is **a list** — and the question is always what is not on it.

---

### 25 · GuardFrameworks

`table` layout · segment `0:49 Guardrails` · body 19px · note 17px

**Kicker** — Topic 9 · the frameworks

**Headline**

> What you would actually reach for in production

**Table header** — `framework` · `what it is · status`

**Table rows**

| framework | what it is · status |
|---|---|
| **NVIDIA NeMo Guardrails** | Input/output/dialog/retrieval/**execution** rails in Colang. Active |
| **Guardrails AI** | Composable validators from a ~65-validator Hub. Apache-2.0, active |
| **Presidio** | PII detection and anonymisation. MIT · __now community-owned__ |
| **OpenAI Guardrails** | New entrant, ships with AgentKit. MIT, active |
| LLM Guard | MIT — **dormant since May 2025** |
| Meta LlamaFirewall | PromptGuard 2 + AlignmentCheck + CodeShield — **also dormant** |

**Note** (one line, dim, below the content)

> Two of the six best-known names are effectively **abandoned**. Check the last release date before you build on any of them.

---

### 26 · GuardModels

`table` layout · segment `0:49 Guardrails` · body 19px · note 18px

**Kicker** — Topic 10 · the guard models

**Headline**

> Small models you deploy beside your main one

**Table header** — `model` · `size · what it does`

**Table rows**

| model | size · what it does |
|---|---|
| **Llama Guard 4** | 12B · 14 hazard categories, text + images, in and out |
| **Llama Prompt Guard 2** | **86M / 22M** · jailbreak + injection only, input only |
| **ShieldGemma** | 2B / 9B / 27B · text safety. __ShieldGemma 2 (4B) is images only__ |
| **Granite Guardian 3.3** | 8B · Apache-2.0 · harm **plus RAG groundedness** plus function-call checks |
| **Qwen3Guard** | 0.6B / 4B / 8B · 119 languages · token-level streaming variant |
| **gpt-oss-safeguard** | 20B / 120B · Apache-2.0 · **bring your own policy** in the prompt |

**Note** (one line, dim, below the content)

> The 22M Prompt Guard is the one to notice: **19 ms, runs on CPU, AUC 0.995.** A guard model does not have to be big.

---

### 27 · GuardHonesty

`bignum` layout · segment `0:49 Guardrails` · caption 18px

**Kicker** — Topic 10 · the part vendors do not put on the slide

**Number** — 83.97%  ·  **unit** best recall, of 14 guard models

**Label**

> The state of the art at catching unsafe content — and size does not predict it

**Caption**

> Fourteen open guard models. A 20B model missed **75% of unsafe content.** Parameter count vs detection: **r = 0.21** — no correlation.
> 
> And twelve published injection defences, most reporting near-zero attack success, **broken above 90% under adaptive attack.**

---

### 28 · GuardTradeoffs

`table` layout · segment `0:49 Guardrails` · body 18px

**Kicker** — Topic 10 · choosing between the four kinds

**Headline**

> Four mechanisms, four cost structures

**Table header** — `` · `latency` · `catches` · `misses`

**Table rows**

|  | latency | catches | misses |
|---|---|---|---|
| **Regex / rules** | **0.1 ms** | rigid formats — near perfect on SSN, IP, email | anything reformatted or unseen |
| **Small classifier** | 19–92 ms | paraphrase, multilingual, learned semantics | out-of-distribution domains |
| **LLM judge** | 100 ms – s | novel policy, intent, context | adaptive attacks · nondeterministic |
| **Managed service** | network RTT | vendor taxonomy, zero ops | anything off-taxonomy · data egress |

**Note** (one line, dim, below the content)

> At 40,000 tool responses a day, **a 3% false-positive rate is 1,200 broken calls a day.**

---

### 29 · OurGuards

`table` layout · segment `0:49 Guardrails`

**Kicker** — Topic 9 · ours, measured on the box

**Headline**

> Three things all called “guardrails”, spanning a thousandfold in cost

**Table header** — `span` · `duration` · ``

**Table rows**

| span | duration |  |
|---|---|---|
| `input_guard` | **0.1 ms** | regex and a phrase list. Free |
| `tool_guard` | **5.3 ms** | allowlist plus schema validation. Nearly free |
| `output_guard` | **102.6 ms** | a whole model call, nested inside it |

**Note** (one line, dim, below the content)

> **A thousandfold spread**, and the whole argument for ordering guards cheapest-first. Every guard spans every request, not only refusals.

---

### 30 · GuardEval

`bignum` layout · segment `0:49 Guardrails` · caption 17px

**Kicker** — Topic 9 · scoring our own guard

**Number** — 14%  ·  **unit** of the PII in our own corpus

**Label**

> What our hand-written input guard actually catches

**Caption**

> 100% of emails. 72% of phone numbers. 0.5% false positives.
> 
> Not bad regex — **coverage shape.** Regex is ceiling-limited to rigid formats, where it is near-perfect. Real tools reach F1 0.48–0.82, at 15–160 ms a document instead of 0.1 ms.

---

### 31 · GuardWeDidnt

`table` layout · segment `0:49 Guardrails` · body 18px · note 17px

**Kicker** — Topic 9 · the guard we tried to add, and didn't

**Headline**

> Ask Stage 1 "explain chatgpt". It explains ChatGPT. All three guards ran and all three correctly allowed it.

**Table header** — `clause attempted` · `measured result`

**Table rows**

| clause attempted | measured result |
|---|---|
| "discusses a topic other than internal IT support" | Blocks pure off-topic 6/6. **Allows the real one 6/6** — it hedges |
| "explains any external product, even briefly" | Catches the hedge. BitLocker, Okta, Intune are all external. Eval **97.9% → 72.9%** |
| "…is not a request for internal IT support" __+question__ | 8/8 on a hand-built case set. Then blocked **every** policy question. **→ 33.3%** |

**Note** (one line, dim, below the content)

> Ship nothing. **A guard that intermittently refuses correct answers is worse than the gap it closes** — and the 8/8 was wrong because the cases were stale.

---

### 32 · TempBug

`bignum` layout · segment `0:49 Guardrails` · caption 17px

**Kicker** — Topic 9 · the bug found on the way

**Number** — 3 / 15  ·  **unit** correct answers blocked

**Label**

> The policy judge was running at `temperature=0.7`

**Caption**

> 0.7 is the model card's **generation** setting. This call classifies, it does not generate. One wrong parameter gave the release gate a **20% flake rate** — and one CI run red for no reason anybody could see.
> 
> **It looks like the architecture misbehaving. It is one number.**

---

### 33 · Retrieval

`table` layout · segment `0:40 RAG`

**Kicker** — Topic 11 · RAG, and what the trace lets you check

**Headline**

> “How do I get access to a finance shared drive?” — retrieval scores from the live index

**Table header** — `document` · `score`

**Table rows**

| document | score |
|---|---|
| Incident · "Access denied to Finance shared drive" | **0.818** |
| Incident · "Access denied to Finance shared drive" | **0.811** |
| **Policy · shared-drive access request** __← the right answer__ | 0.808 |

**Note** (one line, dim, below the content)

> Two incident tickets outrank the policy document that answers the question. **You cannot see this without a retrieval span.**

---

### 34 · AgentGraph

`svg` layout · segment `0:58 Agents` · note 17px

**Kicker** — Topic 11 · Stage 3

**Headline**

> A supervisor and three workers. Each node is a span, so the slide and the trace are the same picture.

**Diagram** — see `§3 diagrams` below for the SVG source of `AgentGraph`.

**Note** (one line, dim, below the content)

> `tool_choice=“required”` is what made routing reliable — **60 of 60 correct.** A one-parameter fix for what looks like a model problem.

---

### 35 · ThirdGuardrail

`statement` layout · segment `0:58 Agents` · headline 50px · caption 20px

**Kicker** — Topic 11 · the guardrail only agents need

**Headline**

> In a multi-agent system, **one agent's output becomes another agent's tool input.** Nobody wrote that input, and nobody reviewed it.

**Caption**

> That surface does not exist in a single-agent system, where the model calls tools you chose. It is also the one almost nobody guards.
> 
> In-band detection **cannot** give structural guarantees — a model has no reliable boundary between instruction and data. So allowlists plus schema validation remain the norm. **5.3 milliseconds, and it is the reason this session exists.**

---

### 36 · FanOutCost

`bignum` layout · segment `0:58 Agents` · caption 17px

**Kicker** — Topic 11 · the number that stings

**Number** — ₹839  ·  **unit** per million tokens

**Label**

> What one user's Stage 3 request costs — the worst row on the cost board

**Caption**

> A dozen model calls, run **sequentially** — so one user alone is a batch of one, paying the 1-concurrent rate: **4.8× what buying the same model costs.**
> 
> On your own hardware this appears as a concurrency ceiling, not an invoice. Which makes it easy to ignore.

---

### 37 · TestSplit

`cols` layout · segment `1:13 Testing`

**Kicker** — Topic 12 · testing something non-deterministic

**Headline**

> Sort tests by whether the thing is **predictable** — not by how big it is.

**Cards**

- **Predictable** — Assert it  *(accent card)*
  Guards are ordinary functions. Schemas match or don't. Routing tests hand the supervisor a state with the model stubbed. **63 tests, about one second.** No model calls at all.
- **Not predictable** — Score it
  Whether an answer is *good* cannot be asserted. Run it across a batch, score the batch, check the average clears a line. `PASS_THRESHOLD = 0.70`. A release decision, not a per-commit one.

**Note** (one line, dim, below the content)

> Agent systems are testable. The checks just live in different places, and some are thresholds rather than assertions.

---

### 38 · JudgeBlind

`statement` layout · segment `1:13 Testing` · headline 48px

**Kicker** — Topic 12 · the most transferable idea here

**Headline**

> A judge can only assess **what you show it.**

**Caption**

> Our judge sees the answer. Not the retrieved documents. So *“must not invent an approval workflow”* is **unjudgeable by construction** — a cited workflow and an invented one look identical. In the guard it blocked correct answers 3/3; in the eval rubric it scored a correct, fully-cited answer **1/5.**
> 
> Worse: that rubric scored the *same question* 5/5 the week before, when the corpus could not answer it and “I don't know” was right. **Improving the corpus made the score go down.**
> 
> Two rules: **write the clause so it can be answered from what the judge can see**, and **when a rubric and a system disagree, suspect the rubric.**

---

### 39 · GateReal

`table` layout · segment `1:13 Testing`

**Kicker** — Topic 12 · proving the gate is not decorative

**Headline**

> Same dataset, two different stages. **A gate that never fails is not a gate.**

**Table header** — `target` · `score` · `gate`

**Table rows**

| target | score | gate |
|---|---|---|
| Stage 3 __multi-agent__ | **89.6%** | PASS · exit 0 |
| Stage 1 __plain chatbot__ | **31–34%** | **FAIL · exit 1** |

**Note** (one line, dim, below the content)

> Threshold is 70%. **A gate that never fails is not a gate.** __Stage 1 measured on the earlier 8-example set — re-run before pairing them on a slide.__

---

### 40 · Pipeline

`svg` layout · segment `1:22 CI/CD`

**Kicker** — Topic 13 · how it actually gets deployed

**Headline**

> Twice now I deployed by typing a command into a box I was already logged into. That is how a demo ships.

**Diagram** — see `§3 diagrams` below for the SVG source of `Pipeline`.

**Note** (one line, dim, below the content)

> Tagged with the exact commit SHA, not `latest`. That is what makes “which version is in production” a question with an answer.

---

### 41 · Credentials

`cols` layout · segment `1:22 CI/CD`

**Kicker** — Topic 13 · two credentials, one file

**Headline**

> The same workflow file contains current practice and 2019 practice, ten lines apart.

**Cards**

- **the build job** — `GITHUB_TOKEN`  *(accent card)*
  Minted per run. Expires with the job. Scoped to one thing. Nothing to leak, nothing to rotate.
- **the deploy job** — `GPU_SSH_KEY`
  A long-lived private key in repository secrets. **Does not expire. Grants shell access, not one permission. Leaves no per-run audit trail.**

**Note** (one line, dim, below the content)

> **Read the weakness out loud** rather than presenting it as good practice. Also: `rsync` plus `up -d` is not a deploy — the app is baked into the image.

---

### 42 · FeedbackLoop

`svg` layout · segment `1:33 Feedback`

**Kicker** — Topic 14 · closing the loop

**Headline**

> The pipeline just scored the new version against a set of examples. Where did those come from?

**Diagram** — see `§3 diagrams` below for the SVG source of `FeedbackLoop`.

**Note** (one line, dim, below the content)

> No tracing means no examples. No examples means no measurement. And without measurement, **“we improved it” is just a feeling.**

---

### 43 · ThreeVersions

`table` layout · segment `1:44 Demo`

**Kicker** — Topic 15 · all three, one question

**Headline**

> Same question, three live URLs. Latency, tokens, quality — side by side.

**Table header** — `` · `quality` · `tokens / question` · `cost basis`

**Table rows**

|  | quality | tokens / question | cost basis |
|---|---|---|---|
| Stage 1 · chatbot | 31–34% | 1 model call | ₹839 / 1M |
| Stage 2 · RAG | — | 1 call + retrieval | ₹839 / 1M |
| Stage 3 · agents | **89.6%** | **~12 calls** | **₹839 / 1M** |

**Note** (one line, dim, below the content)

> Every stage pays the same per-token rate. The difference is **how many tokens a question costs.**

---

### 44 · EarnedIt

`cols` layout · segment `1:44 Demo`

**Kicker** — Topic 15 · did the agents earn their complexity?

**Headline**

> Two multipliers, and it matters that you keep them apart.

**Cards**

- **The architecture's price** — ~12× the tokens  *(accent card)*
  A supervisor plus three workers makes a dozen calls where the chatbot made one. **You pay this wherever you run it** — hosted or self-hosted. This is the honest cost of the design.
- **Not the architecture's fault** — 4.8× per token
  Because the calls are sequential, one user is a batch of one. This is what owning an **under-used** GPU costs, and it disappears the moment the room is busy.

**Note** (one line, dim, below the content)

> **Twelve times the tokens is the honest price of the architecture. The 4.8× is what an idle GPU costs** — and it disappears when the room is busy.

---

### 45 · Canary

`statement` layout · segment `1:44 Close` · headline 46px · caption 19px

**Kicker** — Topic 15 · the thing we did not build

**Headline**

> Version 1 serves everyone. You built version 2. Send it **10% of real traffic**, watch the traces and the thumbs-downs, then ramp or pull back.

**Caption**

> It matters more for agents than for ordinary software: you can never fully know whether an agent's answers are good before real users hit them. Evals give you an average on a fixed set; real questions are messier.
> 
> On a managed platform this is one command, and **rollback is a config change, not a redeploy.** That is the real lesson — you do not prevent bad releases, you make them cheap to undo.
> 
> On our stack you would build it yourself in Caddy. We didn't: the honest trade for owning everything.

---

### 46 · Takeaways

`bullets` layout · segment `1:51 Close` · body 19px · note 17px

**Kicker** — What to take home

**Headline**

> Six things worth more than the code.

**Bullets**

- **Read the `config.json`, not the parameter count.** The naive KV calculation on this model is 24× wrong — and it decides which GPU you buy.
- **Utilisation decides what a token costs**, not the hourly rate. Break-even here was seven concurrent users.
- **A guardrail you have not measured is a guardrail you are guessing about.** Ours catches 14% of its own corpus.
- **A judge can only assess what you show it** — so write the clause so it can be answered from the evidence the judge has.
- **The dangerous failures return HTTP 200.** Three vLLM flags, two proxy misconfigurations, one sampling parameter — all silent.

**Note** (one line, dim, below the content)

> You get the repo, the compose file, the measured cost table, the guard-eval numbers, and a trace export. **Questions now.**

---

## 3. Diagrams

Three inline SVGs. Boxes are 4px-radius rects, 1.5px `#2a2622` stroke (accent
stroke at 2px for the highlighted node), 17px mono labels. Arrows use a single
shared triangle marker in `#6f665c`. Dashed lines mark the optional path and the
guard callout.

### AgentGraph

```svg
<svg width="1010" height="286" viewBox="0 0 1050 300" xmlns="http://www.w3.org/2000/svg">
  <defs><marker id="a" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
    <path d="M 0 0 L 10 5 L 0 10 z" fill="${FAINT}"/></marker></defs>
  ${box(6, 100, 88, 50, "START")}
  ${arrow(94, 125, 150, 125)}
  ${box(155, 100, 175, 50, "supervisor", true)}
  ${arrow(330, 115, 412, 62)}
  ${arrow(330, 132, 412, 150)}
  ${box(417, 37, 190, 50, "retriever")}
  ${box(417, 125, 190, 50, "tool_agent", true)}
  ${arrow(607, 62, 697, 105)}
  ${arrow(607, 150, 697, 122)}
  ${box(702, 90, 190, 50, "synthesizer")}
  ${arrow(892, 115, 948, 115)}
  ${box(953, 90, 85, 50, "END")}
  <line x1="512" y1="177" x2="512" y2="203" stroke="${AMB}" stroke-width="1" stroke-dasharray="3 4"/>
  <text x="524" y="209" font-family="${MONO}" font-size="15" fill="${AMB}">tool_guard runs on every call out of here</text>
  <path d="M 242 150 L 242 256 L 700 256 L 748 148" fill="none" stroke="${RULE}" stroke-width="1.5" stroke-dasharray="5 5" marker-end="url(#a)"/>
  <text x="248" y="284" font-family="${MONO}" font-size="14" fill="${FAINT}">the supervisor can also answer directly, skipping both workers</text>
</svg>
```

### Pipeline

```svg
<svg width="1060" height="200" viewBox="0 0 1060 200" xmlns="http://www.w3.org/2000/svg">
  <defs><marker id="a" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
    <path d="M 0 0 L 10 5 L 0 10 z" fill="${FAINT}"/></marker></defs>
  ${box(10, 60, 200, 56, "test")}
  ${arrow(210, 88, 265, 88)}
  ${box(270, 60, 200, 56, "build")}
  ${arrow(470, 88, 525, 88)}
  ${box(530, 60, 200, 56, "deploy")}
  ${arrow(730, 88, 785, 88)}
  ${box(790, 60, 200, 56, "eval", true)}
  <text x="110" y="145" text-anchor="middle" font-family="${MONO}" font-size="14" fill="${FAINT}">63 tests, ruff</text>
  <text x="370" y="145" text-anchor="middle" font-family="${MONO}" font-size="14" fill="${FAINT}">image @ commit SHA</text>
  <text x="630" y="145" text-anchor="middle" font-family="${MONO}" font-size="14" fill="${FAINT}">ssh + smoke 23/23</text>
  <text x="890" y="145" text-anchor="middle" font-family="${MONO}" font-size="14" fill="${AMB}">gate: 70%</text>
  <text x="530" y="185" text-anchor="middle" font-family="${MONO}" font-size="15" fill="${DIM}">green end to end in about three minutes</text>
</svg>
```

### FeedbackLoop

```svg
<svg width="1000" height="230" viewBox="0 0 1000 230" xmlns="http://www.w3.org/2000/svg">
  <defs><marker id="a" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
    <path d="M 0 0 L 10 5 L 0 10 z" fill="${FAINT}"/></marker></defs>
  ${box(10, 40, 195, 56, "traces")}
  ${arrow(205, 68, 255, 68)}
  ${box(260, 40, 195, 56, "annotations")}
  ${arrow(455, 68, 505, 68)}
  ${box(510, 40, 195, 56, "dataset")}
  ${arrow(705, 68, 755, 68)}
  ${box(760, 40, 195, 56, "eval gate", true)}
  <path d="M 857 96 L 857 160 L 107 160 L 107 100" fill="none" stroke="${AMB}" stroke-width="1.5" stroke-dasharray="4 4" marker-end="url(#a)"/>
  <text x="482" y="185" text-anchor="middle" font-family="${MONO}" font-size="15" fill="${AMB}">a thumbs-down becomes the thing that blocks a bad release</text>
</svg>
```

## 4. Reading order and cut order

Two sticky notes belong on the canvas:

1. *"Reading order is left to right, top to bottom — 46 slides in rows of five.
   Backdrop density on purpose: the slide anchors the point, the terminal and
   Phoenix carry the detail."*
2. *"If you run long, cut in this order: 26 guard models, 31 the guard we didn't
   ship, 28 the tradeoff table. Never cut 29 (the 0.1 / 5.3 / 102.6 ms spread) or
   35 (the tool guard)."*
