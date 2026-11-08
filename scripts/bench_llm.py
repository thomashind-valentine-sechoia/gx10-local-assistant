import json,time,urllib.request
U="http://localhost:8000/v1/chat/completions"
def stream(msgs,extra={}):
    b=dict(model="qwen3.6-35b-a3b",messages=msgs,stream=True,max_tokens=200,temperature=0.6,stream_options={"include_usage":True},**extra)
    r=urllib.request.urlopen(urllib.request.Request(U,json.dumps(b).encode(),{"Content-Type":"application/json"}))
    t0=time.time();ft=None;txt="";n=0;tc=""
    for l in r:
        l=l.decode().strip()
        if not l.startswith("data:") or l.endswith("[DONE]"):continue
        d=json.loads(l[5:])
        if d.get("usage"):n=d["usage"]["completion_tokens"]
        for c in d.get("choices",[]):
            de=c["delta"]
            if (de.get("content") or de.get("tool_calls")) and ft is None: ft=time.time()-t0
            txt+=de.get("content") or ""
            for t in de.get("tool_calls") or []: tc+=json.dumps(t.get("function",{}))
    T=time.time()-t0
    return ft,n,T,txt,tc
sys=[{"role":"system","content":"You are a concise British home voice assistant. Answer in 1-3 short sentences."}]
qs=["How long should I boil an egg for a runny yolk?","What's the capital of Australia?","How do I bleed a radiator?","Why is the sky blue?","What temperature should I roast a chicken at?"]
stream(sys+[{"role":"user","content":"hi"}])
for q in qs:
    ft,n,T,txt,_=stream(sys+[{"role":"user","content":q}])
    print(f"TTFT {ft*1000:.0f}ms  {n} tok  total {T:.2f}s  decode {n/(T-ft):.1f} tok/s | {txt[:90]!r}")
tools=[{"type":"function","function":{"name":"HassTurnOn","description":"Turn on a device","parameters":{"type":"object","properties":{"name":{"type":"string"},"area":{"type":"string"}},"required":["name"]}}},
{"type":"function","function":{"name":"HassLightSet","description":"Set brightness","parameters":{"type":"object","properties":{"name":{"type":"string"},"brightness":{"type":"integer"}},"required":["name","brightness"]}}}]
for q in ["Turn on the office lamp","Dim the office lamp to 30 percent"]:
    ft,n,T,txt,tc=stream(sys+[{"role":"user","content":q}],{"tools":tools,"tool_choice":"auto"})
    print(f"TOOL TTFT {ft*1000:.0f}ms total {T:.2f}s -> {tc} {txt!r}")
