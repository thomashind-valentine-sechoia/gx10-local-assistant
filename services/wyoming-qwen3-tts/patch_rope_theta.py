from pathlib import Path
p = Path("/usr/local/lib/python3.12/site-packages/qwen_tts/_transformers_compat.py")
text = p.read_text()
old = "    base = config.rope_theta\n"
new = """    base = getattr(config, "rope_theta", None)
    if base is None:
        rp = getattr(config, "rope_parameters", None)
        if isinstance(rp, dict):
            base = rp.get("rope_theta")
        elif rp is not None:
            base = getattr(rp, "rope_theta", None)
    if base is None:
        base = 10000.0
"""
if old not in text:
    raise SystemExit("expected rope_theta line not found")
p.write_text(text.replace(old, new, 1))
print("patched", p)
