# -*- coding: utf-8 -*-
"""Chunked, resumable speech-to-text for long meeting or advising recordings.

Built on faster-whisper. The audio is cut into overlapping chunks that are
transcribed in parallel processes. Each chunk is saved as a JSON checkpoint as
soon as it finishes, so an interrupted run resumes where it stopped.

Design notes (from a thesis-advisor feedback workflow):
  * One single-stream "medium" run was estimated at about 5.3 hours for a
    65-minute recording on a 16-core CPU. Chunked parallel runs with "small"
    were used instead. Change the model with --model or WHISPER_MODEL.
  * The first parallel run was lost when the session ended, so every chunk
    writes its own checkpoint.
  * Chunk WAV files are kept, so a re-run with another model skips re-splitting.
  * A short recording can be one chunk (--chunks 1), which is a single stream.

Usage:
  python transcribe_meeting.py "recording.m4a" --tag fb_0915 --out-dir ./feedback
  python transcribe_meeting.py rec.m4a --terms "term one, term two"
  python transcribe_meeting.py rec.m4a --plan-only        # print chunk plan, no ASR

Requirements: pip install faster-whisper ; ffmpeg on PATH or --ffmpeg <path>.
"""
import argparse
import json
import math
import os
import re
import subprocess
import sys
import wave
from concurrent.futures import ProcessPoolExecutor, as_completed

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

OVERLAP_SEC = 12.0          # overlap between neighbouring chunks; removed by merge_rows()
DEFAULT_CHUNK_SEC = 480.0   # about 8 minutes per chunk
MAX_WORKERS = 8             # parallel processes; CPU threads are split across them
BASE_PROMPT = "논문 지도 회의 녹음입니다."  # initial prompt text is read by the model, not code

_model = None
_model_key = None


def get_model(name, threads):
    """Load the Whisper model once per worker process and reuse it."""
    global _model, _model_key
    key = (name, threads)
    if _model is None or _model_key != key:
        from faster_whisper import WhisperModel
        _model = WhisperModel(name, device="cpu", compute_type="int8", cpu_threads=threads)
        _model_key = key
    return _model


def fmt_ts(sec):
    sec = int(sec)
    h, rem = divmod(sec, 3600)
    m, s = divmod(rem, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"


def run_ffmpeg(ffmpeg, args):
    cmd = [ffmpeg, "-y", "-v", "error"] + args
    try:
        subprocess.run(cmd, check=True)
    except FileNotFoundError:
        sys.exit(f"[error] ffmpeg not found: {ffmpeg} (install it or pass --ffmpeg <path>)")
    except subprocess.CalledProcessError as e:
        sys.exit(f"[error] ffmpeg failed (exit {e.returncode}): {' '.join(cmd)}")


def wav_duration(path):
    with wave.open(path, "rb") as w:
        return w.getnframes() / float(w.getframerate())


def is_fresh(target, source):
    """True when target exists, is not empty, and is not older than its source."""
    return (os.path.exists(target) and os.path.getsize(target) > 10_000
            and os.path.getmtime(target) >= os.path.getmtime(source))


def unique_base(out_dir, base, exts):
    """Return a base name whose files (base + ext) do not exist yet. Never overwrite."""
    cand, n = base, 1
    while any(os.path.exists(os.path.join(out_dir, cand + e)) for e in exts):
        n += 1
        cand = f"{base}_v{n}"
    return cand


def transcribe_chunk(job):
    """Transcribe one chunk and save its checkpoint atomically."""
    wav, offset, ck_path, model_name, threads, language, prompt = job
    if os.path.exists(ck_path):
        return ck_path, None
    model = get_model(model_name, threads)
    segments, _info = model.transcribe(
        wav, language=language, beam_size=5,
        vad_filter=True, vad_parameters=dict(min_silence_duration_ms=700),
        condition_on_previous_text=False, initial_prompt=prompt,
    )
    rows = [{"start": s.start + offset, "end": s.end + offset, "text": s.text.strip()}
            for s in segments if s.text.strip()]
    tmp = ck_path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False)
    os.replace(tmp, ck_path)  # an interrupted write never leaves a half-written checkpoint
    return ck_path, len(rows)


def merge_rows(rows):
    """Sort by start time and drop text repeated in the overlap between chunks."""
    merged = []
    for r in sorted(rows, key=lambda r: r["start"]):
        if merged:
            prev = merged[-1]
            same_head = len(prev["text"]) >= 6 and r["text"][:12] == prev["text"][:12]
            near = abs(r["start"] - prev["start"]) < 2.0 or r["start"] < prev["end"] - 1.0
            if same_head and near:
                continue
        merged.append(r)
    return merged


def main(argv=None):
    ap = argparse.ArgumentParser(description="Chunked, resumable transcription of a recording.")
    ap.add_argument("audio", help="input audio file (m4a, mp3, wav, ...)")
    ap.add_argument("--tag", help="job name for output and work folders (default: file stem)")
    ap.add_argument("--out-dir", default=".", help="folder for the final transcript")
    ap.add_argument("--work-dir", help="chunks and checkpoints (default: <out-dir>/_work/<tag>)")
    ap.add_argument("--model", default=os.environ.get("WHISPER_MODEL", "small"),
                    help="faster-whisper model: tiny, base, small, medium, large-v3 ...")
    ap.add_argument("--language", default="ko")
    ap.add_argument("--chunk-sec", type=float, default=DEFAULT_CHUNK_SEC,
                    help="target chunk length in seconds")
    ap.add_argument("--chunks", type=int, help="fixed chunk count (overrides --chunk-sec)")
    ap.add_argument("--workers", type=int,
                    help=f"parallel processes (default: min(chunks, {MAX_WORKERS}))")
    ap.add_argument("--terms", default="",
                    help="comma-separated domain terms, passed as the initial prompt")
    ap.add_argument("--ffmpeg", default="ffmpeg", help="path to the ffmpeg executable")
    ap.add_argument("--plan-only", action="store_true", help="print the chunk plan and exit")
    args = ap.parse_args(argv)

    src = os.path.abspath(args.audio)
    if not os.path.isfile(src):
        sys.exit(f"[error] file not found: {src}")
    tag = re.sub(r"\s+", "_", args.tag or os.path.splitext(os.path.basename(src))[0])
    out_dir = os.path.abspath(args.out_dir)
    base_work = os.path.abspath(args.work_dir or os.path.join(out_dir, "_work", tag))
    os.makedirs(base_work, exist_ok=True)

    # 1. Convert to 16 kHz mono WAV (reused while fresh)
    full_wav = os.path.join(base_work, "full_16k.wav")
    if is_fresh(full_wav, src):
        print("[1] reuse existing WAV", flush=True)
    else:
        print(f"[1] ffmpeg: {os.path.basename(src)} -> 16 kHz mono WAV", flush=True)
        run_ffmpeg(args.ffmpeg, ["-i", src, "-ar", "16000", "-ac", "1",
                                 "-c:a", "pcm_s16le", full_wav])

    dur = wav_duration(full_wav)
    n = args.chunks or max(1, math.ceil(dur / args.chunk_sec))
    span = dur / n
    print(f"    duration {dur / 60:.1f} min -> {n} chunk(s), about {span / 60:.1f} min each",
          flush=True)
    if args.plan_only:
        return

    try:  # fail early with a clear message instead of a worker traceback
        import faster_whisper  # noqa: F401
    except ImportError:
        sys.exit("[error] faster-whisper is not installed. Run: pip install faster-whisper")

    work = os.path.join(base_work, f"n{n}")
    ck_dir = os.path.join(work, args.model)
    os.makedirs(ck_dir, exist_ok=True)

    # 2. Cut overlapping chunk WAVs
    jobs = []
    for i in range(n):
        start = max(0.0, i * span - (OVERLAP_SEC if i else 0.0))
        length = span + OVERLAP_SEC * (2 if i else 1)
        chunk_wav = os.path.join(work, f"c{i:02d}.wav")
        if not is_fresh(chunk_wav, full_wav):
            run_ffmpeg(args.ffmpeg, ["-i", full_wav, "-ss", f"{start:.2f}",
                                     "-t", f"{length:.2f}", "-ar", "16000", "-ac", "1",
                                     "-c:a", "pcm_s16le", chunk_wav])
        jobs.append((chunk_wav, start, os.path.join(ck_dir, f"c{i:02d}.json")))

    # 3. Transcribe the chunks that have no checkpoint yet
    todo = [j for j in jobs if not os.path.exists(j[2])]
    print(f"[2] checkpoints {n - len(todo)}/{n} present, {len(todo)} to run "
          f"(model={args.model})", flush=True)
    if todo:
        workers = args.workers or min(len(todo), MAX_WORKERS)
        threads = max(1, (os.cpu_count() or 4) // workers)
        prompt = BASE_PROMPT + (f" 다음 용어가 나옵니다: {args.terms}." if args.terms else "")
        payloads = [(w, off, ck, args.model, threads, args.language, prompt)
                    for (w, off, ck) in todo]
        try:
            with ProcessPoolExecutor(max_workers=workers) as ex:
                futures = {ex.submit(transcribe_chunk, p): p[2] for p in payloads}
                for fut in as_completed(futures):
                    ck_path, count = fut.result()
                    print(f"    checkpoint saved: {os.path.basename(ck_path)} "
                          f"({count} segments)", flush=True)
        except Exception as e:
            sys.exit(f"[error] {type(e).__name__}: {e}\n"
                     "Saved checkpoints are kept. Run the same command again to resume.")
    else:
        print("[2] all checkpoints exist, skipping ASR", flush=True)

    # 4. Merge checkpoints
    rows, missing = [], []
    for (_, _, ck) in jobs:
        if os.path.exists(ck):
            with open(ck, encoding="utf-8") as f:
                rows += json.load(f)
        else:
            missing.append(os.path.basename(ck))
    if missing:
        sys.exit(f"[error] missing checkpoints: {missing}. Run the same command again.")
    merged = merge_rows(rows)

    # 5. Write outputs under a new name (never overwrite)
    os.makedirs(out_dir, exist_ok=True)
    base = unique_base(out_dir, f"{tag}_{args.model}", (".txt", "_segments.json"))
    txt_path = os.path.join(out_dir, base + ".txt")
    json_path = os.path.join(out_dir, base + "_segments.json")
    with open(txt_path, "w", encoding="utf-8") as f:
        for r in merged:
            f.write(f"[{fmt_ts(r['start'])}] {r['text']}\n")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(merged, f, ensure_ascii=False, indent=1)
    print(f"[done] {len(merged)} segments", flush=True)
    print(f"       {txt_path}", flush=True)
    print(f"       {json_path}", flush=True)


if __name__ == "__main__":
    main()
