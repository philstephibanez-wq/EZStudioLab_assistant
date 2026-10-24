"""XPS read-only OCR + translation preflight: no network document download or LAB.
Does not start jobs. Prints sanitized JSON and does not claim a successful OCR
unless the real Tesseract executable and traineddata are available.
"""
from __future__ import annotations
import json
import subprocess
import tempfile
import sys
import time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"app"))
from profile_tesseract_runtime import resolve_tesseract, booklet_ocr_enabled
from profile_document_consultation import consult

# 5x7 bitmap, scaled without image packages; recognizable synthetic OCR input.
FONT={
"T":("11111","00100","00100","00100","00100","00100","00100"),
"E":("11111","10000","10000","11110","10000","10000","11111"),
"S":("01111","10000","10000","01110","00001","00001","11110"),
}
def _image_fixture():
    glyphs="TEST"
    scale=12
    width=(len(glyphs)*6+2)*scale
    height=11*scale
    bitmap=bytearray([255])*(width*height)
    for n,char in enumerate(glyphs):
        for y,line in enumerate(FONT[char]):
            for x,val in enumerate(line):
                if val=="1":
                    for dy in range(scale):
                        start=((y+2)*scale+dy)*width+(n*6+x+2)*scale
                        bitmap[start:start+scale]=bytes([0])*scale
    return ("P5\\n%d %d\\n255\\n"%(width,height)).encode("ascii")+bitmap

def check_ocr():
    state=resolve_tesseract()
    if state.get("status")!="ready":
        return {"status":"unavailable","reason":state.get("status"),"executed":False}
    try:
        with tempfile.TemporaryDirectory(prefix="ezs_ocr_smoke_") as folder:
            image=Path(folder)/"synthetic.pgm"
            image.write_bytes(_image_fixture())
            done=subprocess.run([state["executable"],str(image),"stdout","-l","eng",
                    "--tessdata-dir",state["tessdata_dir"],"--psm","7"],
                    capture_output=True,timeout=20,check=False)
        recognized=done.stdout.decode("utf-8","replace").strip()
        return {"status":"recognized" if "TEST" in recognized.upper() else "recognition_mismatch",
                "executed":True,"exit_code":done.returncode,
                "expected":"TEST","recognized":recognized[:80],
                "model":"eng","fixture":"synthetic_bitmap"}
    except (OSError,subprocess.TimeoutExpired) as exc:
        return {"status":"execution_error","reason":type(exc).__name__,"executed":False}

def check_translation():
    # Deliberately synthetic; passing only proves a real inference, not accuracy.
    sample={"duration":{"verdict":"non_trouve","reference_value":"English metadata: five minutes",
                        "references":[{"url":"https://example.org/fixture",
                        "reference_value":"English metadata: five minutes",
                        "attribution":"synthetic_unverified"}]}}
    advice=consult({"title":"Synthetic song","artist":"Synthetic artist"},sample)
    return {"status":advice.get("status"),"executed":advice.get("status") in ("completed","abstain"),
            "translation_notes_count":len(advice.get("translation_notes") or []),
            "translation_proven":False,"reason":advice.get("reason"),
            "advisory_only":advice.get("advisory_only"),"promotes_verdict":advice.get("promotes_verdict")}

def main():
    started=time.monotonic()
    ocr=check_ocr()
    translation=check_translation()
    report={"schema":"ezstudio.assistant.ocr-translation-preflight.v1",
            "assistant_version":(ROOT/"VERSION").read_text(encoding="utf-8-sig").strip(),
            "ocr":ocr,"ocr_setting_enabled":booklet_ocr_enabled(),
            "qwen_translation":translation,
            "lab_jobs_created":0,"lab_writes":0,
            "scientific_validation":False,
            "duration_ms":round((time.monotonic()-started)*1000)}
    print(json.dumps(report,ensure_ascii=True,allow_nan=False))
    return 0 if translation["executed"] and translation["advisory_only"] and not translation["promotes_verdict"] else 1

if __name__=="__main__":
    raise SystemExit(main())
