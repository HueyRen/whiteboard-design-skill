#!/usr/bin/env python3
"""Notion Meeting Transcript → Meeting.md live sync.

Usage:
    python3 notion_sync.py <page_id> [--interval 3]
    python3 notion_sync.py 1a2b3c4d5e6f7890abcd1234ef567890

<page_id> is the 32-char ID from the Notion page URL (dashes optional).

Polls Notion API every N seconds, writes transcript to Meeting.md.
Ctrl+C to stop.
"""

import argparse
import os
import signal
import subprocess
import sys
import time
from datetime import datetime

import requests

# Token resolution, in order: $NOTION_TOKEN env var, then macOS Keychain
# (service: notion-integration-token). Never hardcode the token in this file —
# it's meant to live in a synced/shared repo.
def get_notion_token() -> str:
    env_token = os.environ.get("NOTION_TOKEN")
    if env_token:
        return env_token

    result = subprocess.run(
        ["security", "find-generic-password", "-s", "notion-integration-token", "-w"],
        capture_output=True, text=True,
    )
    if result.returncode == 0:
        return result.stdout.strip()

    sys.exit(
        "Notion token not found. Either:\n"
        "  export NOTION_TOKEN=<token>\n"
        "or, on macOS, store it in Keychain:\n"
        '  security add-generic-password -a "$USER" -s notion-integration-token -w <TOKEN>'
    )

NOTION_TOKEN = get_notion_token()
NOTION_VERSION = "2022-06-28"
BASE_URL = "https://api.notion.com/v1"
OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "Meeting.md")

HEADERS = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Notion-Version": NOTION_VERSION,
}


def get_blocks(block_id: str) -> list:
    """Fetch all child blocks (handles pagination)."""
    blocks = []
    cursor = None
    while True:
        params = {"page_size": 100}
        if cursor:
            params["start_cursor"] = cursor
        resp = requests.get(f"{BASE_URL}/blocks/{block_id}/children", headers=HEADERS, params=params)
        resp.raise_for_status()
        data = resp.json()
        blocks.extend(data.get("results", []))
        if not data.get("has_more"):
            break
        cursor = data.get("next_cursor")
    return blocks


def extract_text(rich_text_list: list) -> str:
    return "".join(rt.get("plain_text", "") for rt in rich_text_list)


def extract_transcript(blocks: list, depth: int = 0) -> str:
    """Recursively extract all text from blocks."""
    lines = []
    for block in blocks:
        btype = block.get("type", "")
        bdata = block.get(btype, {})

        # Extract rich_text from any block type that has it
        if isinstance(bdata, dict) and "rich_text" in bdata:
            text = extract_text(bdata["rich_text"]).strip()
            if text:
                lines.append(text)

        # Recurse into children
        if block.get("has_children") and depth < 5:
            child_blocks = get_blocks(block["id"])
            child_text = extract_transcript(child_blocks, depth + 1)
            if child_text:
                lines.append(child_text)

    return "\n\n".join(lines)


def get_page_title(page_id: str) -> str:
    try:
        resp = requests.get(f"{BASE_URL}/pages/{page_id}", headers=HEADERS)
        resp.raise_for_status()
        props = resp.json().get("properties", {})
        title_prop = props.get("title", {})
        if title_prop.get("type") == "title":
            return extract_text(title_prop.get("title", []))
    except Exception:
        pass
    return "Meeting"


def write_meeting_md(title: str, transcript: str):
    now = datetime.now().strftime("%H:%M:%S")
    today = datetime.now().strftime("%Y-%m-%d")
    with open(OUTPUT_FILE, "w") as f:
        f.write(f"# Meeting Transcript\n")
        f.write(f"**Page**: {title} | **Date**: {today} | **Last sync**: {now}\n\n")
        f.write(f"---\n\n")
        f.write(transcript)
        f.write("\n")


def main():
    parser = argparse.ArgumentParser(description="Sync Notion meeting transcript to Meeting.md")
    parser.add_argument("page_id", help="Notion page ID (from the page URL, dashes optional)")
    parser.add_argument("--interval", "-i", type=int, default=3, help="Poll interval in seconds (default: 3)")
    args = parser.parse_args()

    page_id = args.page_id.replace("-", "")
    interval = args.interval

    running = True
    def handle_signal(sig, frame):
        nonlocal running
        running = False
        print("\n⏹️  Stopping sync...")
    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    title = get_page_title(page_id)
    print(f"══ notion_sync ━━ Live Sync ON ━━━━━━━━━━━")
    print(f"📋 Page: {title}")
    print(f"📁 File: {OUTPUT_FILE}")
    print(f"🔄 Polling: every {interval}s")
    print(f"Ctrl+C to stop.")
    print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    last_transcript = None
    sync_count = 0

    while running:
        try:
            blocks = get_blocks(page_id)
            transcript = extract_transcript(blocks)

            if transcript != last_transcript:
                write_meeting_md(title, transcript)
                wc = len(transcript.split())
                if last_transcript is not None:
                    delta = wc - len(last_transcript.split())
                    print(f"🔄 [{datetime.now().strftime('%H:%M:%S')}] Meeting.md updated (+{delta} words, total {wc})")
                else:
                    print(f"📝 [{datetime.now().strftime('%H:%M:%S')}] Meeting.md created ({wc} words)")
                last_transcript = transcript
                sync_count += 1

        except requests.exceptions.HTTPError as e:
            if e.response and e.response.status_code == 429:
                print("⚠️  Rate limited, backing off 5s...")
                time.sleep(5)
                continue
            print(f"⚠️  HTTP error: {e}")
        except requests.exceptions.ConnectionError:
            print("⚠️  Connection error, retrying...")
        except Exception as e:
            print(f"⚠️  {e}")

        time.sleep(interval)

    # Final sync
    try:
        blocks = get_blocks(page_id)
        transcript = extract_transcript(blocks)
        write_meeting_md(title, transcript)
        wc = len(transcript.split())
        print(f"\n══ notion_sync ━━ Live Sync OFF ━━━━━━━━━━")
        print(f"📁 Meeting.md final: {wc} words | Syncs: {sync_count}")
        print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    except Exception:
        print("⏹️  Stopped.")


if __name__ == "__main__":
    main()
