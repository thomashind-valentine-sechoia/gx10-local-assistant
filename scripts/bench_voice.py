import socket,json,time,wave,sys
def send(s,t,data=None,payload=b""):
    h={"type":t,"version":"1.5.0"};d=json.dumps(data or {}).encode()
    h["data_length"]=len(d)
    if payload:h["payload_length"]=len(payload)
    s.sendall(json.dumps(h).encode()+b"\n"+d+payload)
def recv(f):
    h=json.loads(f.readline());d=h.get("data") or {}
    if h.get("data_length"):d.update(json.loads(f.read(h["data_length"])))
    p=f.read(h["payload_length"]) if h.get("payload_length") else b""
    return h["type"],d,p
def tts(text,voice="bf_emma"):
    s=socket.create_connection(("127.0.0.1",10200));f=s.makefile("rb")
    t0=time.time();send(s,"synthesize",{"text":text,"voice":{"name":voice}})
    first=None;audio=b"";rate=24000
    while True:
        t,d,p=recv(f)
        if t=="audio-start":rate=d["rate"]
        if t=="audio-chunk":
            first=first or time.time()-t0;audio+=p
        if t=="audio-stop":break
    return first,time.time()-t0,audio,rate
def stt(wavf):
    w=wave.open(wavf);fr=w.readframes(w.getnframes())
    s=socket.create_connection(("127.0.0.1",10300));f=s.makefile("rb")
    fmt={"rate":w.getframerate(),"width":w.getsampwidth(),"channels":w.getnchannels()}
    send(s,"transcribe",{"language":"en"});send(s,"audio-start",fmt)
    for i in range(0,len(fr),4096):send(s,"audio-chunk",fmt,fr[i:i+4096])
    t0=time.time();send(s,"audio-stop")
    while True:
        t,d,p=recv(f)
        if t=="transcript":return time.time()-t0,d["text"]
for i,txt in enumerate(["Turn on the office lamp.","How long should I boil an egg for a runny yolk? Boil it for about six minutes, then cool it in cold water so it stops cooking."]*3):
    a,b,au,r=tts(txt)
    print(f"TTS first audio {a*1000:.0f}ms total {b*1000:.0f}ms audio {len(au)/2/r:.1f}s")
    w=wave.open(f"/tmp/s{i}.wav","wb");w.setnchannels(1);w.setsampwidth(2);w.setframerate(r);w.writeframes(au);w.close()
for i in range(4):
    dt,t=stt(f"/tmp/s{i%2}.wav");print(f"STT {dt*1000:.0f}ms after audio-stop: {t!r}")
