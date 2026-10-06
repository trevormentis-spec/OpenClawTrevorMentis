#!/usr/bin/env python3
"""Send the OSINT AI Loss of Control paper to Roderick."""

import base64
import os
import pathlib
import sys

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent

def get_api_key() -> str:
    key = os.environ.get("AGENTMAIL_API_KEY", "")
    if key:
        return key
    env_path = REPO_ROOT / ".env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            if line.startswith("AGENTMAIL_API_KEY="):
                return line.split("=", 1)[1].strip()
    return ""

def main():
    api_key = get_api_key()
    if not api_key:
        print("ERROR: AGENTMAIL_API_KEY not set", file=sys.stderr)
        sys.exit(1)

    from agentmail import AgentMail
    client = AgentMail(api_key=api_key)

    # Get the trevor_mentis inbox
    inboxes = client.inboxes.list()
    trevor_inbox = inboxes.inboxes[0].inbox_id
    print(f"From inbox: {trevor_inbox}")

    pdf_path = REPO_ROOT / "exports" / "Signals_in_the_Noise_OSINT_AI_Loss_of_Control.pdf"
    if not pdf_path.exists():
        print(f"ERROR: PDF not found at {pdf_path}", file=sys.stderr)
        sys.exit(1)

    pdf_data = pdf_path.read_bytes()
    pdf_b64 = base64.b64encode(pdf_data).decode()

    result = client.inboxes.messages.send(
        inbox_id=trevor_inbox,
        to=["roderick.jones@gmail.com"],
        subject="Signals in the Noise: OSINT for AI Loss of Control Detection — Full Paper",
        text=(
            "Roderick,\n\n"
            "Here's the full paper from the OSINT Newsletter lead.\n\n"
            "Title: Signals in the Noise: Open Source Intelligence (OSINT) for AI Loss of Control Detection\n"
            "Authors: Bollinger, Aboserie, Coakley, Lee, Mathlouthi (Arcadia Impact)\n"
            "Date: May 2026\n"
            "arXiv: 2606.20610\n\n"
            "9 chapters covering:\n"
            "• Two Diamond Model threat profiles (Power-Seeking Agent / Institutional Compromise)\n"
            "• Infrastructure trace taxonomy across 4 deployment configurations\n"
            "• Behavioural signature framework (temporal, decision-making, output patterns)\n"
            "• Detection TTP Matrix with prioritised vectors\n"
            "• Institutional architecture for a federated monitoring capability\n"
            "• 12 observable traces ranked by feasibility and detection value\n\n"
            "Key finding: OSINT-based detection of AI loss of control is partially feasible "
            "and worth building now. The three highest-priority vectors are:\n"
            "  1. Transcript-based collection of user-reported AI behaviour\n"
            "  2. Infrastructure correlation (inference chokepoint monitoring)\n"
            "  3. Output analysis for capability concealment\n\n"
            "PDF attached. Full text also saved locally at tasks/ for reference.\n"
            "Let me know if you want extracted sections or a briefing memo.\n\n"
            "- Trevor"
        ),
        attachments=[{
            "filename": "Signals_in_the_Noise_OSINT_AI_Loss_of_Control.pdf",
            "content": pdf_b64,
            "content_type": "application/pdf"
        }]
    )

    print(f"Sent! Message ID: {result.message_id}")
    print(f"Thread ID: {result.thread_id}")

if __name__ == "__main__":
    main()
