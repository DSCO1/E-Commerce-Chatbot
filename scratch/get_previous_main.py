import json
import os

log_file = r"C:\Users\Ujjaw\.gemini\antigravity-ide\brain\95796c4d-1896-467a-b456-2585590b183c\.system_generated\logs\transcript_full.jsonl"
if not os.path.exists(log_file):
    log_file = r"C:\Users\Ujjaw\.gemini\antigravity-ide\brain\95796c4d-1896-467a-b456-2585590b183c\.system_generated\logs\transcript.jsonl"

print(f"Reading logs from {log_file}...")
main_py_versions = []

with open(log_file, "r", encoding="utf-8") as f:
    for line in f:
        try:
            data = json.loads(line)
            # Check for replace_file_content or view_file response
            # A PLANNER_RESPONSE contains tool_calls
            # We want to find the state of main.py right before step 2109
            step_idx = data.get("step_index", 0)
            if step_idx < 2109:
                if "tool_calls" in data:
                    for tc in data["tool_calls"]:
                        if tc.get("name") in ["replace_file_content", "write_to_file"]:
                            args = tc.get("args", {})
                            path = args.get("AbsolutePath") or args.get("TargetFile") or ""
                            if "main.py" in path:
                                main_py_versions.append((step_idx, "replace", args))
                # Also check system tool responses for view_file
                if data.get("source") == "MODEL" and data.get("type") == "VIEW_FILE":
                    # Wait, the tool response in transcript has type depending on tool name
                    pass
        except Exception as e:
            pass

print(f"Found {len(main_py_versions)} replacement modifications to main.py before step 2109.")
# Let's inspect the last replacement before 2109.
# Actually, let's write a parser to look at what files we viewed or what replacement content we sent.
# Better yet, let's look at the original main.py in the previous commit, and reconstruct it step by step,
# or scan for any VIEWS that contain chunks.
# Wait, let's check if there is an active view_file in logs containing chunks.
# Let's write a python script to scan the entire logs for the full main.py text or pieces.
