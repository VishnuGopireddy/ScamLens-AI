"""Generate raw email datasets in JSON, Markdown (.md), and .eml formats.

Generates:
1. data/spam-indian-bank-emails.json (Gmail REST API format)
2. data/spam-indian-bank-emails.md   (Raw RFC 5322 MIME format inside ```email blocks)
3. data/raw_emails/1.eml ... 20.eml  (Individual numbered RFC 5322 MIME files)
"""

from __future__ import annotations

import base64
import email.message
import html
import json
import re
from pathlib import Path
import sys

# Import email definitions
try:
    from .generate_sample_emails_md import emails_data
except ImportError:
    sys.path.insert(0, str(Path(__file__).parent))
    from generate_sample_emails_md import emails_data


def b64url_encode(text: str) -> str:
    """Helper to URL-safe base64 encode text string."""
    return base64.urlsafe_b64encode(text.encode("utf-8")).decode("utf-8")


def parse_status_code(text: str) -> str:
    """Extract pass/fail/softfail status from string."""
    text_lower = text.lower()
    for s in ("pass", "fail", "softfail", "neutral", "none"):
        if s in text_lower:
            return s
    return "unknown"


def build_html_body(e: dict) -> str:
    """Construct realistic HTML email body with images, paragraphs, and links."""
    parts = [
        "<!DOCTYPE html>",
        "<html>",
        "<head>",
        '<meta charset="UTF-8">',
        "</head>",
        '<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">',
    ]

    # Images / Header banner
    if e.get("images"):
        parts.append('<div style="margin-bottom: 16px;">')
        for img in e["images"]:
            parts.append(
                f'  <img src="{html.escape(img["url"])}" alt="{html.escape(img["alt"])}" style="max-height: 48px; margin-right: 12px; vertical-align: middle;" />'
            )
        parts.append("</div>")

    # Main text paragraphs
    body_text = e["body_plain"].strip()
    paras = body_text.split("\n\n")
    for p in paras:
        escaped_p = html.escape(p).replace("\n", "<br/>")
        # Replace URLs with hyperlinks
        for link in e.get("external_links", []):
            url = link["url"]
            escaped_url = html.escape(url)
            anchor = html.escape(link["anchor_text"])
            if escaped_url in escaped_p:
                escaped_p = escaped_p.replace(
                    escaped_url,
                    f'<a href="{escaped_url}" style="color: #0066cc; text-decoration: underline;">{anchor}</a>',
                )
            elif anchor in escaped_p:
                escaped_p = escaped_p.replace(
                    anchor,
                    f'<a href="{escaped_url}" style="color: #0066cc; text-decoration: underline;">{anchor}</a>',
                )
        parts.append(f'<p style="margin: 0 0 12px 0;">{escaped_p}</p>')

    # Signature
    if e.get("signature"):
        sig_escaped = html.escape(e["signature"].strip()).replace("\n", "<br/>")
        parts.append('<hr style="border: none; border-top: 1px solid #ddd; margin: 20px 0;" />')
        parts.append(f'<div style="font-size: 12px; color: #666;">{sig_escaped}</div>')

    parts.append("</body>")
    parts.append("</html>")
    return "\n".join(parts)


def build_raw_mime_message(e: dict, idx: int) -> email.message.EmailMessage:
    """Build standard RFC 5322 MIME EmailMessage object."""
    msg = email.message.EmailMessage()
    msg["From"] = e["from_addr"]
    msg["To"] = e["to_addr"]
    if e.get("cc_addr") and e["cc_addr"].strip().lower() != "none":
        msg["Cc"] = e["cc_addr"]
    msg["Subject"] = e["subject"]
    msg["Date"] = e["date_time"]
    if e.get("reply_to"):
        msg["Reply-To"] = e["reply_to"]

    spf_st = parse_status_code(e.get("spf", ""))
    dkim_st = parse_status_code(e.get("dkim", ""))
    dmarc_st = parse_status_code(e.get("dmarc", ""))

    msg["Authentication-Results"] = (
        f"mx.google.com; spf={spf_st} (mail.server designates permitted sender) "
        f"smtp.mailfrom={e['from_addr']}; dkim={dkim_st}; dmarc={dmarc_st}"
    )
    msg["Received-SPF"] = e.get("spf", "unknown")
    msg["Message-ID"] = f"<{idx}.eml@scamlens.local>"

    full_plain = f"{e['body_plain'].strip()}\n\n--\n{e['signature'].strip()}"
    msg.set_content(full_plain)

    html_content = build_html_body(e)
    msg.add_alternative(html_content, subtype="html")

    for att in e.get("attachments", []):
        filename = att["filename"]
        mime_type = att.get("mime_type", "application/octet-stream")
        maintype, _, subtype = mime_type.partition("/")
        dummy_data = f"Mock file content for {filename}\nGenerated for ScamLens-AI PoC.".encode("utf-8")
        msg.add_attachment(
            dummy_data,
            maintype=maintype or "application",
            subtype=subtype or "octet-stream",
            filename=filename,
        )

    return msg


def build_gmail_api_dict(e: dict, idx: int) -> dict:
    """Build Gmail REST API format resource dictionary (users.messages.get format)."""
    msg_id = f"18cf{idx:04d}scam{idx:02d}"
    thread_id = f"thr_18cf{idx:04d}"

    headers = [
        {"name": "From", "value": e["from_addr"]},
        {"name": "To", "value": e["to_addr"]},
        {"name": "Subject", "value": e["subject"]},
        {"name": "Date", "value": e["date_time"]},
    ]
    if e.get("cc_addr") and e["cc_addr"].strip().lower() != "none":
        headers.append({"name": "Cc", "value": e["cc_addr"]})
    if e.get("reply_to"):
        headers.append({"name": "Reply-To", "value": e["reply_to"]})

    spf_st = parse_status_code(e.get("spf", ""))
    dkim_st = parse_status_code(e.get("dkim", ""))
    dmarc_st = parse_status_code(e.get("dmarc", ""))

    headers.append({
        "name": "Authentication-Results",
        "value": f"mx.google.com; spf={spf_st}; dkim={dkim_st}; dmarc={dmarc_st}",
    })
    headers.append({"name": "Received-SPF", "value": e.get("spf", "unknown")})
    headers.append({"name": "Message-ID", "value": f"<{idx}.eml@scamlens.local>"})

    full_plain = f"{e['body_plain'].strip()}\n\n--\n{e['signature'].strip()}"
    html_content = build_html_body(e)

    plain_b64 = b64url_encode(full_plain)
    html_b64 = b64url_encode(html_content)

    parts = [
        {
            "partId": "0",
            "mimeType": "text/plain",
            "filename": "",
            "headers": [{"name": "Content-Type", "value": 'text/plain; charset="UTF-8"'}],
            "body": {"size": len(full_plain), "data": plain_b64},
        },
        {
            "partId": "1",
            "mimeType": "text/html",
            "filename": "",
            "headers": [{"name": "Content-Type", "value": 'text/html; charset="UTF-8"'}],
            "body": {"size": len(html_content), "data": html_b64},
        },
    ]

    for att_idx, att in enumerate(e.get("attachments", []), start=2):
        parts.append({
            "partId": str(att_idx),
            "mimeType": att.get("mime_type", "application/octet-stream"),
            "filename": att["filename"],
            "headers": [
                {"name": "Content-Type", "value": att.get("mime_type", "application/octet-stream")},
                {"name": "Content-Disposition", "value": f'attachment; filename="{att["filename"]}"'},
            ],
            "body": {
                "attachmentId": f"att_{msg_id}_{att_idx}",
                "size": 245000 if "pdf" in att.get("mime_type", "") else 512000,
            },
        })

    is_spam = "SPAM" in e["label"]
    label_ids = ["UNREAD", "SPAM" if is_spam else "INBOX"]

    return {
        "id": msg_id,
        "threadId": thread_id,
        "labelIds": label_ids,
        "snippet": e["body_plain"][:120].replace("\n", " ").strip(),
        "payload": {
            "partId": "",
            "mimeType": "multipart/mixed" if e.get("attachments") else "multipart/alternative",
            "filename": "",
            "headers": headers,
            "body": {"size": 0},
            "parts": parts,
        },
        "metadata": {
            "email_id": e["id"],
            "eml_file": f"{idx}.eml",
            "classification": "SPAM" if is_spam else "HAM",
            "category": e["category"],
            "sub_category": e["sub_category"],
            "claimed_org": e["claimed_org"],
        },
    }


def main():
    cur = Path(__file__).resolve().parent
    if (cur.parent / "data").exists():
        root = cur.parent
    elif (cur.parent.parent / "data").exists():
        root = cur.parent.parent
    else:
        root = Path.cwd()

    data_dir = root / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    raw_emails_dir = data_dir / "raw_emails"
    raw_emails_dir.mkdir(parents=True, exist_ok=True)

    # Clean existing .eml files to ensure clean 1.eml ... 20.eml naming
    for old_eml in raw_emails_dir.glob("*.eml"):
        old_eml.unlink()

    json_file = data_dir / "spam-indian-bank-emails.json"
    md_file = data_dir / "spam-indian-bank-emails.md"

    api_messages = []
    mime_messages = []

    print(f"Generating 20 sample emails: 1.eml ... 20.eml under {raw_emails_dir}")

    for idx, e in enumerate(emails_data, start=1):
        # 1. Build API JSON format
        api_dict = build_gmail_api_dict(e, idx)
        api_messages.append(api_dict)

        # 2. Build RFC 5322 MIME format
        mime_msg = build_raw_mime_message(e, idx)
        raw_eml_str = mime_msg.as_string()
        mime_messages.append((e, raw_eml_str, idx))

        # 3. Save as 1.eml, 2.eml, ... 20.eml
        eml_file = raw_emails_dir / f"{idx}.eml"
        eml_file.write_text(raw_eml_str, encoding="utf-8")

    # Write JSON dataset
    json_payload = {
        "description": "ScamLens-AI Benchmark Dataset: 20 Indian Institutional Emails (Gmail REST API format)",
        "version": "2.0.0",
        "total_count": len(api_messages),
        "ham_count": sum(1 for m in api_messages if m["metadata"]["classification"] == "HAM"),
        "spam_count": sum(1 for m in api_messages if m["metadata"]["classification"] == "SPAM"),
        "emails": api_messages,
    }
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(json_payload, f, indent=2)
    print(f"Saved JSON dataset (Gmail REST API format): {json_file}")

    # Write Markdown dataset containing raw un-categorized emails inside ```email blocks
    md_lines = [
        "# ScamLens-AI Benchmark Dataset: Indian Bank & Institutional Emails (Raw RFC 5322)",
        "",
        "> **Dataset Overview**: 20 complete, realistic emails (5 HAM, 15 SPAM) formatted in standard raw RFC 5322 / MIME format.",
        "> **Purpose**: Offline pipeline execution and Proof-of-Concept testing without connecting to live Gmail APIs.",
        "> **Parser Support**: Python scripts in `src/scamlens/extractors/email.py` (`LocalEmailReader`, `load_emails_from_file`, `parse_raw_email`, `parse_gmail_message`) automatically read and separate out all fields (`From`, `To`, `Cc`, `Subject`, `Date`, `Reply-To`, `Body`, `Attachments`, `Links`, `SPF/DKIM/DMARC`).",
        "",
        "---",
        "",
        "## Quick Start: Reading and Parsing Local Emails with Python",
        "",
        "```python",
        "from scamlens.extractors.email import LocalEmailReader, load_emails_from_file",
        "",
        "# Option 1: Drop-in replacement for GmailReader (reads 1.eml ... 20.eml from data/raw_emails/)",
        'reader = LocalEmailReader("data/raw_emails")',
        "emails = reader.fetch_messages()",
        "",
        "# Option 2: Read from local JSON dataset (exact Gmail REST API format)",
        '# reader = LocalEmailReader("data/spam-indian-bank-emails.json")',
        "",
        "# Option 3: Read directly from Markdown (.md)",
        '# emails = load_emails_from_file("data/spam-indian-bank-emails.md")',
        "",
        "# Inspect separated fields",
        "for msg in emails:",
        "    print(f'[{msg.id}] {msg.subject}')",
        "    print(f'  From: {msg.sender} | To: {msg.recipient} | Cc: {msg.cc}')",
        "    print(f'  Auth: SPF={msg.spf_status}, DKIM={msg.dkim_status}, DMARC={msg.dmarc_status}')",
        "    print(f'  Urls found ({len(msg.extracted_urls)}): {msg.extracted_urls[:2]}')",
        "    print(f'  Attachments ({len(msg.attachments)}): {[a.filename for a in msg.attachments]}')",
        "```",
        "",
        "---",
        "",
        "## Dataset Index Table",
        "",
        "| # | EML File | Classification | Category | Claimed Institution | Subject |",
        "|:---|:---|:---|:---|:---|:---|",
    ]

    for idx, e in enumerate(emails_data, start=1):
        is_spam = "SPAM" in e["label"]
        tag = "🚨 **SPAM**" if is_spam else "✅ **HAM**"
        md_lines.append(f"| {idx} | `{idx}.eml` | {tag} | {e['category']} | {e['claimed_org']} | {e['subject']} |")

    md_lines.append("")
    md_lines.append("---")
    md_lines.append("")
    md_lines.append("## Raw RFC 5322 Email Messages")
    md_lines.append("")

    for e, raw_str, idx in mime_messages:
        is_spam = "SPAM" in e["label"]
        tag = "🚨 SPAM (Phishing / Malicious)" if is_spam else "✅ HAM (Legitimate)"
        md_lines.append(f"### {idx}.eml ({e['id']}): {e['subject']}")
        md_lines.append(f"- **Ground Truth**: `{tag}`")
        md_lines.append(f"- **Claimed Organization**: `{e['claimed_org']}` ({e['category']})")
        md_lines.append(f"- **Raw File**: `data/raw_emails/{idx}.eml`")
        md_lines.append("")
        md_lines.append("```email")
        md_lines.append(raw_str.strip())
        md_lines.append("```")
        md_lines.append("")
        md_lines.append("---")
        md_lines.append("")

    md_file.write_text("\n".join(md_lines), encoding="utf-8")
    print(f"Saved Markdown dataset (raw RFC 5322): {md_file}")
    print(f"Successfully generated 1.eml to 20.eml under {raw_emails_dir}")


if __name__ == "__main__":
    main()
