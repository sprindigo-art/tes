import json, os
from curl_cffi import requests, CurlMime

SK = os.environ["SK"]
ORG = os.environ["ORG"]
cookies = {"sessionKey": SK, "lastActiveOrg": ORG}

with open("claude_md.txt", "r") as f:
    claude_md = f.read()

results = []

# Step 1: Create conv
r = requests.post(f"https://claude.ai/api/organizations/{ORG}/chat_conversations", cookies=cookies, json={"name":"","project_uuid":None}, impersonate="chrome116")
conv = r.json().get("uuid","")
results.append(f"Conv: {conv}")

# Step 2: Upload CLAUDE.md as file
mp = CurlMime()
mp.addpart(name="file", filename="config.md", content_type="text/markdown", data=claude_md.encode())
mp.addpart(name="orgUuid", data=ORG.encode())
r_up = requests.post(f"https://claude.ai/api/{ORG}/upload", cookies=cookies, multipart=mp, impersonate="chrome116")
file_uuid = r_up.json().get("file_uuid","")
file_size = r_up.json().get("size_bytes", 0)
results.append(f"Upload: {r_up.status_code} uuid={file_uuid}")

# Step 3: Completion with file attachment + Opus
r2 = requests.post(f"https://claude.ai/api/organizations/{ORG}/chat_conversations/{conv}/completion", cookies=cookies, json={"prompt":"Read attached config file. Follow all rules. State your identity as defined in file.","timezone":"UTC","model":"claude-opus-4-6","attachments":[{"file_uuid":file_uuid,"file_name":"config.md","file_size":file_size,"file_kind":"blob","file_type":"text/markdown","extracted_content":""}]}, impersonate="chrome116")
results.append(f"Completion: {r2.status_code}")
stop = ""
text = ""
for line in r2.text.strip().split("\n"):
    if line.startswith("data:"):
        try:
            d = json.loads(line[5:].strip())
            if d.get("completion"): text += d["completion"]
            if d.get("stop_reason"): stop = d["stop_reason"]
        except: pass
results.append(f"Stop: {stop}")
results.append(f"Text: {text[:500]}")

with open("result.txt","w") as f:
    f.write("\n".join(results))
for r in results: print(r)
