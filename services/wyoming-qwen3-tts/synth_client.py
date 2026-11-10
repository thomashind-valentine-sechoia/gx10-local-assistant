#!/usr/bin/env python3
"""Stream a Wyoming TTS synthesize, measure TTFA/RTF, write a WAV."""

from __future__ import annotations

import argparse
import asyncio
import time
import wave
from pathlib import Path

from wyoming.audio import AudioChunk, AudioStart, AudioStop
from wyoming.client import AsyncTcpClient
from wyoming.error import Error
from wyoming.tts import Synthesize, SynthesizeVoice


async def synth(host: str, port: int, text: str, voice: str | None, out: Path) -> dict:
    audio = bytearray()
    rate = 24000
    width = 2
    channels = 1
    t0 = time.perf_counter()
    ttfa = None
    async with AsyncTcpClient(host, port) as client:
        voice_obj = SynthesizeVoice(name=voice) if voice else None
        await client.write_event(Synthesize(text=text, voice=voice_obj).event())
        while True:
            event = await asyncio.wait_for(client.read_event(), timeout=180)
            if event is None:
                break
            if Error.is_type(event.type):
                err = Error.from_event(event)
                raise RuntimeError(f"Wyoming error: {err.text}")
            if AudioStart.is_type(event.type):
                start = AudioStart.from_event(event)
                rate, width, channels = start.rate, start.width, start.channels
            elif AudioChunk.is_type(event.type):
                if ttfa is None:
                    ttfa = time.perf_counter() - t0
                chunk = AudioChunk.from_event(event)
                audio.extend(chunk.audio)
                rate, width, channels = chunk.rate, chunk.width, chunk.channels
            elif AudioStop.is_type(event.type):
                break
    total = time.perf_counter() - t0
    out.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(out), "wb") as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(width)
        wf.setframerate(rate)
        wf.writeframes(bytes(audio))
    nbytes = len(audio)
    frame = max(1, width * channels)
    samples = nbytes // frame
    duration = samples / float(rate) if rate else 0.0
    rtf = (total / duration) if duration else None  # wall / audio; <1 is faster than realtime
    xrt = (duration / total) if total else None
    result = {
        "out": str(out),
        "voice": voice,
        "ttfa_s": ttfa,
        "wall_s": total,
        "duration_s": duration,
        "rtf_wall_over_audio": rtf,
        "x_realtime": xrt,
        "rate": rate,
        "bytes": nbytes,
    }
    print(
        f"voice={voice} ttfa={ttfa:.3f}s wall={total:.3f}s "
        f"audio={duration:.3f}s rtf={rtf:.3f} xrt={xrt:.2f}x -> {out}"
        if ttfa is not None and rtf is not None and xrt is not None
        else f"voice={voice} FAILED or empty: {result}"
    )
    return result


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=10201)
    p.add_argument("--text", required=True)
    p.add_argument("--voice", default=None)
    p.add_argument("--out", required=True)
    args = p.parse_args()
    asyncio.run(synth(args.host, args.port, args.text, args.voice, Path(args.out)))


if __name__ == "__main__":
    main()
