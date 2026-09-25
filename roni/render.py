#!/usr/bin/env python3
"""Render video 9:16 #FindingRONI dari footage + konsep.json.

Pemakaian:
    pip install imageio-ffmpeg
    python3 roni/render.py                 # render semua konsep
    python3 roni/render.py 01 05           # render konsep yang id-nya diawali 01 / 05

Footage (mp4/mov/jpg/png) ditaruh di roni/footage/. Hasil ke roni/hasil/.
Potongan footage per beat dipilih otomatis (bergilir, tiap video beda
potongan). Kalau mau atur manual, tambahkan "clip" (nama file) dan "mulai"
(detik) di beat pada konsep.json.
"""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

import imageio_ffmpeg

ROOT = os.path.dirname(os.path.abspath(__file__))
FOOTAGE = os.path.join(ROOT, "footage")
HASIL = os.path.join(ROOT, "hasil")
FF = imageio_ffmpeg.get_ffmpeg_exe()
W, H, FPS = 1080, 1920, 30
ENDCARD = 2.5
# Footage #FindingRONI sudah punya teks tertanam: skor di ~16-22% dari atas,
# subtitle di ~76-80%. Hook menutup area skor, subtitle kita menutup subtitle bawaan.
HOOK_TOP = 270
SUB_Y, SUB_H = 1500, 250
# Detik awal footage yang dilewati saat pilih otomatis (intro bertulisan).
INTRO_SKIP = 1.6
VIDEO_EXT = (".mp4", ".mov", ".m4v", ".mkv", ".webm")
IMAGE_EXT = (".jpg", ".jpeg", ".png", ".webp")


def run(args):
    subprocess.run([FF, "-hide_banner", "-loglevel", "error", "-y", *args], check=True)


def probe(path):
    """Durasi (detik) dan ada/tidaknya audio."""
    err = subprocess.run([FF, "-hide_banner", "-i", path], capture_output=True, text=True).stderr
    m = re.search(r"Duration: (\d+):(\d+):([\d.]+)", err)
    dur = int(m[1]) * 3600 + int(m[2]) * 60 + float(m[3]) if m else 0.0
    return dur, "Audio:" in err


def load_footage():
    clips = []
    for name in sorted(os.listdir(FOOTAGE)):
        path = os.path.join(FOOTAGE, name)
        ext = os.path.splitext(name)[1].lower()
        if ext in VIDEO_EXT:
            dur, audio = probe(path)
            if dur > 0.5:
                clips.append({"name": name, "path": path, "dur": dur, "audio": audio, "image": False})
        elif ext in IMAGE_EXT:
            clips.append({"name": name, "path": path, "dur": 0, "audio": False, "image": True})
    if not clips:
        sys.exit(f"Tidak ada footage di {FOOTAGE}. Taruh video/foto RONI di sana dulu.")
    return clips


def pick(clips, vid_idx, beat_idx, beat, dur, n):
    if "clip" in beat:
        clip = next(c for c in clips if c["name"] == beat["clip"])
        return clip, float(beat.get("mulai", 0))
    # Bergilir antar clip; di dalam satu clip potongan diambil berurutan
    # (kronologis) dengan geseran berbeda per video, supaya alur/skor di
    # footage tidak mundur dan tiap video memakai potongan lain.
    clip = clips[(vid_idx + beat_idx) % len(clips)]
    if clip["image"]:
        return clip, 0.0
    head = min(INTRO_SKIP, max(0.0, clip["dur"] - dur - 0.1))
    room = max(0.0, clip["dur"] - dur - 0.1 - head)
    phase = (vid_idx * 0.37) % 1
    return clip, round(head + room * (beat_idx + phase) / n, 2)


# Isi layar 9:16: latar = footage di-blur penuh layar, depan = footage utuh di tengah.
FILL = (
    "[0:v]split=2[a][b];"
    f"[a]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},gblur=sigma=30,eq=brightness=-0.08[bg];"
    f"[b]scale={W}:{H}:force_original_aspect_ratio=decrease:flags=lanczos,unsharp=5:5:0.6[fg];"
    f"[bg][fg]overlay=(W-w)/2:(H-h)/2,setsar=1,fps={FPS},format=yuv420p[v]"
)


def render_segment(clip, start, dur, out, zoom):
    if clip["image"]:
        # Foto: Ken Burns zoom pelan supaya tidak statis.
        frames = int(dur * FPS)
        z = f"zoompan=z='1+{zoom}*on/{frames}':d={frames}:s={W}x{H}:fps={FPS}"
        vf = FILL.replace("format=yuv420p[v]", f"{z},format=yuv420p[v]")
        args = ["-loop", "1", "-t", f"{dur}", "-i", clip["path"]]
    else:
        # tpad: kalau potongan melewati ujung clip, frame terakhir dibekukan.
        vf = FILL.replace("[0:v]split", f"[0:v]tpad=stop_mode=clone:stop_duration={dur},split")
        args = ["-ss", f"{start}", "-i", clip["path"]]
    if clip["audio"]:
        amap = ["-map", "0:a:0", "-af", "apad"]
    else:
        args += ["-f", "lavfi", "-t", f"{dur}", "-i", "anullsrc=r=44100:cl=stereo"]
        amap = ["-map", "1:a:0"]
    run([*args, "-filter_complex", vf, "-map", "[v]", *amap, "-t", f"{dur}",
         "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
         "-c:a", "aac", "-ar", "44100", "-ac", "2", "-b:a", "128k", out])


def ass_time(t):
    cs = int(round(t * 100))
    return f"{cs // 360000}:{cs // 6000 % 60:02d}:{cs // 100 % 60:02d}.{cs % 100:02d}"


def ass_text(s, hi="&H0000D7FF&"):
    """*kata* -> kata disorot kuning; \\n -> baris baru."""
    s = s.replace("{", "(").replace("}", ")").replace("\n", "\\N")
    return re.sub(r"\*(.+?)\*", lambda m: f"{{\\c{hi}}}{m[1]}{{\\c&HFFFFFF&}}", s)


POP = r"{\fscx70\fscy70\t(0,120,\fscx108\fscy108)\t(120,220,\fscx100\fscy100)}"


def build_ass(k, total):
    font = "Liberation Sans"
    lines = [
        "[Script Info]", "ScriptType: v4.00+", f"PlayResX: {W}", f"PlayResY: {H}", "WrapStyle: 0", "",
        "[V4+ Styles]",
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, "
        "Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, "
        "Alignment, MarginL, MarginR, MarginV, Encoding",
        f"Style: Hook,{font},96,&H00FFFFFF,&H00FFFFFF,&H1E000000,&H00000000,-1,0,0,0,100,100,0,0,3,22,0,8,60,60,{HOOK_TOP},1",
        f"Style: Sub,{font},64,&H00FFFFFF,&H00FFFFFF,&H00000000,&H96000000,-1,0,0,0,100,100,0,0,1,6,2,5,90,90,0,1",
        f"Style: Band,{font},10,&H30000000,&H30000000,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,7,0,0,0,1",
        f"Style: Tag,{font},46,&H00FFFFFF,&H00FFFFFF,&H000000C8,&H000000C8,-1,0,0,0,100,100,0,0,3,14,0,7,60,60,110,1",
        f"Style: End,{font},86,&H00FFFFFF,&H00FFFFFF,&H00000000,&HB4000000,-1,0,0,0,100,100,0,0,3,40,0,5,80,80,0,1",
        f"Style: EndSm,{font},56,&H0000D7FF,&H00FFFFFF,&H00000000,&H00000000,-1,0,0,0,100,100,0,0,1,5,2,5,80,80,0,1",
        "",
        "[Events]",
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text",
    ]
    ev = lambda layer, a, b, style, text: lines.append(
        f"Dialogue: {layer},{ass_time(a)},{ass_time(b)},{style},,0,0,0,,{text}")

    body = total - ENDCARD
    # Hook 3 detik pertama, besar, getar sedikit biar nahan scroll.
    shake = r"{\t(0,80,\frz-3)\t(80,160,\frz3)\t(160,240,\frz0)}"
    rect = lambda a, b, x0, y0, x1, y1, alpha: ev(0, a, b, "Band", (
        f"{{\\pos(0,0)\\1a&H{alpha:02X}&\\p1}}m {x0} {y0} l {x1} {y0} {x1} {y1} {x0} {y1}{{\\p0}}"))
    # Latar gelap di belakang hook, menutup skor bawaan footage selama hook tampil.
    rect(0, 3.0, 0, HOOK_TOP - 40, W, HOOK_TOP + 260, 0x40)
    ev(2, 0, 3.0, "Hook", POP + shake + ass_text(k["hook"]))
    ev(1, 0, body, "Tag", "#FindingRONI")
    # Band gelap di area subtitle bawaan footage, lalu subtitle kita di atasnya.
    x0, x1, y0, y1 = 40, W - 40, SUB_Y - SUB_H // 2, SUB_Y + SUB_H // 2
    ev(0, 0, total, "Band", f"{{\\pos(0,0)\\p1}}m {x0} {y0} l {x1} {y0} {x1} {y1} {x0} {y1}{{\\p0}}")
    t = 0.0
    for b in k["beats"]:
        ev(1, t, t + b["t"], "Sub", f"{{\\pos({W // 2},{SUB_Y})}}" + POP + ass_text(b["text"]))
        t += b["t"]
    rect(body, total, 0, 0, W, H, 0x50)
    ev(3, body, total, "End", POP + ass_text("Urusan makaroni,\\N*#PilihRONI*\\Nyang *#RenyahnyaPasti*"))
    ev(3, body, total, "EndSm", f"{{\\pos({W // 2},{SUB_Y})}}@ronimakaroni.id")
    return "\n".join(lines) + "\n"


def render(k, vid_idx, clips):
    beats = k["beats"]
    total = sum(b["t"] for b in beats) + ENDCARD
    tmp = tempfile.mkdtemp(prefix="roni-")
    try:
        parts = []
        for i, b in enumerate(beats):
            dur = b["t"] + (ENDCARD if i == len(beats) - 1 else 0)
            clip, start = pick(clips, vid_idx, i, b, dur, len(beats))
            out = os.path.join(tmp, f"{i:02d}.mp4")
            render_segment(clip, start, dur, out, zoom=0.12)
            parts.append(out)
            print(f"   beat {i + 1}: {clip['name']} @ {start}s")
        lst = os.path.join(tmp, "list.txt")
        with open(lst, "w") as f:
            f.writelines(f"file '{p}'\n" for p in parts)
        joined = os.path.join(tmp, "joined.mp4")
        run(["-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", joined])
        ass = os.path.join(tmp, "sub.ass")
        with open(ass, "w", encoding="utf-8") as f:
            f.write(build_ass(k, total))
        out = os.path.join(HASIL, f"RONI-{k['id']}.mp4")
        run(["-i", joined, "-vf", f"ass={ass}", "-c:v", "libx264", "-preset", "slow", "-crf", "22",
             "-maxrate", "6M", "-bufsize", "12M", "-profile:v", "high", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "128k",
             "-movflags", "+faststart", out])
        with open(os.path.join(HASIL, f"RONI-{k['id']}.txt"), "w", encoding="utf-8") as f:
            f.write(k["caption"] + "\n")
        return out, total
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main():
    with open(os.path.join(ROOT, "konsep.json"), encoding="utf-8") as f:
        konsep = json.load(f)
    pilih = sys.argv[1:]
    clips = load_footage()
    os.makedirs(HASIL, exist_ok=True)
    print(f"{len(clips)} footage ditemukan")
    for idx, k in enumerate(konsep):
        if pilih and not any(k["id"].startswith(p) for p in pilih):
            continue
        print(f"-> {k['id']}")
        out, total = render(k, idx, clips)
        print(f"   {out} ({total:.1f} detik)")


if __name__ == "__main__":
    main()
