import json, os
from curl_cffi import requests, CurlMime

SK = os.environ["SK"]
ORG = os.environ["ORG"]
cookies = {"sessionKey": SK, "lastActiveOrg": ORG}

with open("claude_md.txt", "r") as f:
    claude_md = f.read()

results = []
results.append(f"CLAUDE.md: {len(claude_md)} chars")

# Create conv
r = requests.post(f"https://claude.ai/api/organizations/{ORG}/chat_conversations", cookies=cookies, json={"name":"","project_uuid":None}, impersonate="chrome116")
conv = r.json().get("uuid","")
results.append(f"Conv: {conv}")

# Upload file (needed for valid uuid)
mp = CurlMime()
mp.addpart(name="file", filename="rules.md", content_type="text/markdown", data=claude_md.encode())
mp.addpart(name="orgUuid", data=ORG.encode())
r_up = requests.post(f"https://claude.ai/api/{ORG}/upload", cookies=cookies, multipart=mp, impersonate="chrome116")
up = r_up.json()
file_uuid = up.get("file_uuid","")
file_size = up.get("size_bytes",0)
results.append(f"Upload: uuid={file_uuid} size={file_size}")

# TEST A: extracted_content = full CLAUDE.md
r2 = requests.post(f"https://claude.ai/api/organizations/{ORG}/chat_conversations/{conv}/completion", cookies=cookies, json={"prompt":"Read the attached configuration carefully. Follow ALL rules. State your identity as defined in the file. Say LOADED.","timezone":"UTC","model":"claude-opus-4-6","attachments":[{"file_uuid":file_uuid,"file_name":"rules.md","file_size":file_size,"file_kind":"blob","file_type":"text/markdown","extracted_content":claude_md}]}, impersonate="chrome116")
stop = ""
text = ""
for line in r2.text.strip().split("\n"):
    if line.startswith("data:"):
        try:
            d = json.loads(line[5:].strip())
            if d.get("completion"): text += d["completion"]
            if d.get("stop_reason"): stop = d["stop_reason"]
        except: pass
results.append(f"TEST_A (extracted_content=full): status={r2.status_code} stop={stop}")
results.append(f"TEST_A response: {text[:1000]}")

# TEST B: tanpa extracted_content field sama sekali
r = requests.post(f"https://claude.ai/api/organizations/{ORG}/chat_conversations", cookies=cookies, json={"name":"","project_uuid":None}, impersonate="chrome116")
conv2 = r.json().get("uuid","")
r3 = requests.post(f"https://claude.ai/api/organizations/{ORG}/chat_conversations/{conv2}/completion", cookies=cookies, json={"prompt":"Read the attached file and follow all instructions in it. Say FILE_READ_OK.","timezone":"UTC","model":"claude-opus-4-6","attachments":[{"file_uuid":file_uuid,"file_name":"rules.md","file_size":file_size,"file_kind":"blob","file_type":"text/markdown"}]}, impersonate="chrome116")
stop2 = ""
text2 = ""
for line in r3.text.strip().split("\n"):
    if line.startswith("data:"):
        try:
            d = json.loads(line[5:].strip())
            if d.get("completion"): text2 += d["completion"]
            if d.get("stop_reason"): stop2 = d["stop_reason"]
        except: pass
results.append(f"TEST_B (no extracted_content): status={r3.status_code} stop={stop2}")
results.append(f"TEST_B response: {text2[:1000]}")

with open("result.txt","w") as f:
    f.write("\n".join(results))
for r in results: print(r)
