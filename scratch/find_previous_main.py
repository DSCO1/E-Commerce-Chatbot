import json
import os

log_file = r"C:\Users\Ujjaw\.gemini\antigravity-ide\brain\95796c4d-1896-467a-b456-2585590b183c\.system_generated\logs\transcript_full.jsonl"
if not os.path.exists(log_file):
    log_file = r"C:\Users\Ujjaw\.gemini\antigravity-ide\brain\95796c4d-1896-467a-b456-2585590b183c\.system_generated\logs\transcript.jsonl"

print(f"Reading logs from {log_file}...")
with open(log_file, "r", encoding="utf-8") as f:
    for line in f:
        try:
            data = json.loads(line)
            # Find a step that views or replaces app/main.py
            if "tool_calls" in data:
                for tc in data["tool_calls"]:
                    if tc.get("name") in ["view_file", "replace_file_content", "write_to_file"]:
                        args = tc.get("args", {})
                        path = args.get("AbsolutePath") or args.get("TargetFile") or ""
                        if "main.py" in path:
                            print(f"Step {data.get('step_index')}: {tc['name']}")
                            # print just a snippet of args to verify
                            print(str(args)[:200])
        except Exception as e:
            pass
