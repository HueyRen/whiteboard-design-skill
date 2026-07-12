# whiteboard design skill

A Claude Code skill for **whiteboard-style product design interviews** — practice mode for drilling the format, and a live executor mode for real interviews.

Turns a live design conversation into a structured 8-step whiteboard (`template.html`) plus generated wireframes, or coaches you through the same 8 steps as a solo practice partner.

## Recommended: live transcription via Notion

The live executor mode reads its context from `Meeting.md`. The easiest way to keep that file updated in real time during an actual interview is Notion's built-in AI meeting transcription, piped in with the included `notion_sync.py`.

1. **Start a live transcript in Notion.** Open (or create) a Notion page for the call, click the audio/record icon in the page toolbar, and start Notion's AI meeting transcription. It transcribes the conversation onto that page as you talk.
2. **Create a Notion integration** at [notion.so/my-integrations](https://www.notion.so/my-integrations) → "New integration" → copy the "Internal Integration Secret" (this is your `NOTION_TOKEN`). Then open the transcript page → "..." menu → "Connections" → add your integration, so it's allowed to read the page.
3. **Get the page ID** from the page URL — the 32-character string right before any `?`, e.g. `notion.so/My-Meeting-1a2b3c4d5e6f7890abcd1234ef567890` → page ID is `1a2b3c4d5e6f7890abcd1234ef567890`.
4. **Set the token and run the sync:**
   ```bash
   pip install requests
   export NOTION_TOKEN=<your integration secret>
   python3 notion_sync.py <page_id>
   ```
   This polls the page every 3 seconds and writes the transcript to `Meeting.md` at the repo root. `/wb` reads that file on every invocation, so the whiteboard stays in sync with the live conversation. Ctrl+C to stop.

On macOS you can skip the `export` and instead store the token once in Keychain — see the top of `notion_sync.py` for the command. `--interval N` changes the poll frequency (default 3s).

Don't have Notion, or prefer another transcription tool? Just keep `Meeting.md` updated however you like (paste transcript chunks in manually, pipe in another tool's output) — `/wb` doesn't care how the file gets written, only that it's there.

**Privacy:** `notion_sync.py` never hardcodes your token or page ID — it reads `$NOTION_TOKEN` (or macOS Keychain) and takes the page ID as a CLI argument. `Meeting.md` is gitignored at the repo root, so a live transcript never ends up committed even if you forget and run `git add .`.

## Recommended: a GitHub repo per session, before you start

Before starting the interview (or a practice run) — not just before wireframing — it's worth creating a dedicated GitHub repo for that session:

1. Before diving into Step 1, create a new (private is fine) GitHub repo for **this session only**, separate from the skill repo itself.
2. Push everything the session has produced so far into it: `sessions/<slug>/template.html`, `Meeting.md`, `company-notes.md` if you have one.

This is optional — `/wb lofi` and `/wb prototype` work fine against the local `sessions/` folder without it — but it pays off once you're iterating across multiple screens or directions and want a record of what changed.

**Recommended: use Claude Design for the wireframing/prototyping step.** Connect the session repo in Claude Design and do Step 7 there instead of working against loose local files. Real-time prototyping goes noticeably better against a live repo — you can review the commit history as screens evolve, branch to compare lo-fi vs. hi-fi or Direction A vs. B without overwriting each other, and Claude has a clean, versioned source of truth to read from and write back to.

## What it does

- **Practice mode** — give it a prompt (or let it pick one from the practice bank), and it walks you through Why → Who → Context → Assumptions → Ideation → Flow → Solution → Summary, one step at a time, catching blind spots and modeling what to say out loud.
- **Live executor mode** — during an actual interview, feed it your meeting transcript and it fills in a shareable HTML whiteboard in real time, plus auto-generates lo-fi/hi-fi wireframes.
- **Reference library** — `SKILL.md` pulls in a `references/` folder on demand (8-step framework, problem-type taxonomy, scoring rubric, red-flag checklist, ASCII wireframe component guide). That folder isn't included in this repo — see below.

## Install

Copy this repo into your Claude Code skills directory:

```bash
git clone https://github.com/HueyRen/whiteboard-design-skill.git ~/.claude/skills/wb
```

Then invoke it in Claude Code as `/wb`.

**Note:** `SKILL.md` reads from a local `references/` folder (framework guide, problem types, scoring rubric, interviewer strategies, practice bank, wireframe components) that isn't published in this repo. Quick-reference commands (`types`, `redflags`, `signals`, `components`, `interviewer`, `coach`) and practice mode won't have content to pull from until you add your own `references/*.md` files matching the names `SKILL.md` expects.

## How sessions work

The root `template.html` is a **pristine, blank template** — it is never edited in place. Every practice run or real interview creates its own folder:

```
sessions/
  2026-07-12-pet-adoption/
    template.html      # copy of the root template, filled in as you go
    Meeting.md          # live transcript for this session
    company-notes.md    # optional — interviewer/company context you add yourself
    pet-adoption-lofi/  # generated wireframes
```

`sessions/` is gitignored — your real interview transcripts, company notes, and generated wireframes stay local and never get committed.

## Commands

| Command | What it does |
|---|---|
| `/wb [prompt]` | Start a new practice/interview session |
| `/wb s1` … `/wb s8` | Fill or coach one step of the framework |
| `/wb lofi` / `/wb prototype` | Generate wireframes from the current session |
| `/wb review` | Self-review against the scoring rubric |
| `/wb coach [step]` | Deep-dive coaching on one step |
| `/wb types` / `redflags` / `signals` / `time` / `components` / `interviewer` | Quick-reference cards |

See [SKILL.md](SKILL.md) for the full behavior spec.

## Structure

```
SKILL.md          # the skill definition Claude Code reads
template.html     # blank whiteboard template — copied per session, never edited directly
notion_sync.py    # optional — polls a Notion page and writes Meeting.md in real time
references/       # NOT published here (gitignored) — supply your own, see Install
sessions/          # gitignored — your local practice/interview runs live here
```
