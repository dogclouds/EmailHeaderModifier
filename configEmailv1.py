# change from domain to [P_RPATH]
# add sender
# add [eid] before @ in param header
#

from pathlib import Path
import re

p = Path("fullEmail.txt")
if p.exists():
    content = p.read_text(encoding="utf-8")
    content = re.sub(
        r'^(From:.*?<[^@<>]+)@[^<>]+(>)',
        r'\1@[P_RPATH]\2',
        content,
        flags=re.MULTILINE
    )
    # If Sender already exists, replace its domain; otherwise add new Sender after From
    if re.search(r'^Sender:', content, flags=re.MULTILINE | re.IGNORECASE):
        content = re.sub(
            r'^(Sender:.*?)@[^\s>]+',
            r'\1@[RDNS]',
            content,
            flags=re.MULTILINE | re.IGNORECASE
        )
    else:
        content = re.sub(
            r'^(From:.*)$',
            r'\1\nSender: support@[RDNS]',
            content,
            flags=re.MULTILINE
        )
    content = re.sub(
        r'^(Message-ID:\s*<?[^@\s<>]+)@',
        r'\1[EID]@',
        content,
        flags=re.MULTILINE | re.IGNORECASE
    )
    Path("updatedEmail.txt").write_text(content, encoding="utf-8")
    print("✅ File saved as updatedEmail.txt")
else:
    print("❌ File not found")