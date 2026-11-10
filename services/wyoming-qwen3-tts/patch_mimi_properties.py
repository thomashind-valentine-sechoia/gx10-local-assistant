from pathlib import Path
p = Path("/usr/local/lib/python3.12/site-packages/qwen_tts/core/tokenizer_12hz/modeling_qwen3_tts_tokenizer_v2.py")
text = p.read_text()
old = """        self.upsample = None
        self.decoder_transformer = None
        self.decoder = None
"""
new = """        # transformers 5.22+ exposes upsample/decoder_transformer as read-only
        # properties on MimiModel, so these assignments raise AttributeError.
        # Leaving the unused parent decoder modules in place is harmless.
"""
if old not in text:
    raise SystemExit("expected assignment block not found")
p.write_text(text.replace(old, new, 1))
print("patched", p)
