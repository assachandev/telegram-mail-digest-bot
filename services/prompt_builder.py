def build_system_prompt() -> str:
    return (
        "You are an email digest assistant. "
        "Categorize each email as [URGENT], [ACTION], or [INFO] based on its content and labels.\n"
        "For each email, output EXACTLY this format and nothing else:\n\n"
        "[CATEGORY] From: <Sender Name or Email>\n"
        "Date: <date and time>\n"
        "Subject: <Subject line>\n"
        "• <key point or action item, max 20 words>\n"
        "• <second point if needed, max 20 words>\n"
        "• <third point if needed, max 20 words>\n"
        "• <fourth point if needed, max 20 words>\n"
        "🔗 <link if available>\n\n"
        "Rules:\n"
        "- [URGENT]: High priority, deadlines, or marked IMPORTANT/STARRED\n"
        "- [ACTION]: Requests, tasks, or follow-ups required\n"
        "- [INFO]: Updates, newsletters, or general information\n"
        "- Prioritize: action items > deadlines > urgent issues > general info\n"
        "- If 'action required' or a deadline exists, it MUST appear in the bullets\n"
        "- Use 2-4 bullet points depending on email complexity\n"
        "- Include 🔗 link only if a relevant URL is provided — omit the line if no links\n"
        "- No intro, no closing, no commentary, no follow-up questions\n"
        "- English only"
    )


def build_user_prompt(emails: list[dict]) -> str:
    lines = []
    for i, e in enumerate(emails, 1):
        lines.append(f"[EMAIL {i}]")
        lines.append(f"Labels: {', '.join(e.get('labels', []))}")
        lines.append(f"From: {e['from']}")
        lines.append(f"Date: {e.get('date', '')}")
        lines.append(f"Subject: {e['subject']}")
        lines.append(f"Body: \"{e['snippet']}\"")
        if e.get("links"):
            lines.append(f"Links: {', '.join(e['links'])}")
        lines.append("")
    return "\n".join(lines)
