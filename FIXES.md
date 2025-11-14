# Bug Fixes Log

## v0.1.1 - Session Management Fixes

### Issue 1: Content Extraction
**Problem**: Claude CLI JSON response uses `"result"` field, but code was looking for `"content"` or `"text"`.

**Symptoms**: First chat worked but content was not properly extracted.

**Fix**: Added `"result"` field extraction in `_extract_content_from_json()`.

```python
# claude_code_server/client.py line 251
if "result" in data:  # Claude CLI uses "result" field
    return data["result"]
```

### Issue 2: Error Message Clarity
**Problem**: When Claude CLI fails, error message didn't show stderr/stdout details.

**Symptoms**: Error "Claude CLI failed with return code 1" without details.

**Fix**: Enhanced error message to include stderr and stdout.

```python
# claude_code_server/client.py line 116-120
error_msg = f"Claude CLI failed with return code {result.returncode}"
if result.stderr:
    error_msg += f"\nStderr: {result.stderr}"
if result.stdout:
    error_msg += f"\nStdout: {result.stdout}"
```

## Testing After Fixes

Run in a **standalone terminal** (not inside Claude Code):

```bash
cd /Users/eric/Project/viralt/claude-code-server
python3 test_debug.py
```

Expected output:
```
[1] First call - No session yet
✓ Success!
  Content: 42
  Claude session ID: 894eaf27-...
  Saved claude_session_id: 894eaf27-...

[2] Second call - Should resume with session
✓ Success!
  Content: I said 42

✅ All tests passed!
```

If still fails, the error message will now show detailed stderr/stdout.
