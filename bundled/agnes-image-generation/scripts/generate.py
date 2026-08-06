#!/usr/bin/env python3
"""Agnes AI 免費生圖 — txt2img + img2img

Usage:
  python3 generate.py "prompt" [--image URL ...] [--image-file PATH ...] [--size WxH] [--model NAME] [--outdir DIR]

Notes:
  - --image accepts public URL(s) or data:image/...;base64,... URI(s)
  - --image-file converts local files to Data URI Base64 before calling Agnes
  - API key is read from AGNES_API_KEY or Hermes profile .env files; never print it
"""

import argparse
import base64
import json
import mimetypes
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

BASE_URL = "https://apihub.agnes-ai.com"
ENDPOINT = f"{BASE_URL}/v1/images/generations"
DEFAULT_MODEL = "agnes-image-2.1-flash"
DEFAULT_SIZE = "1024x768"
DEFAULT_OUTDIR = "/tmp/agnes-output"


def get_api_key():
    key = os.environ.get("AGNES_API_KEY")
    if key and key.startswith("sk-"):
        return key

    env_paths = []
    # Active Hermes home (docker data dir, profile, or default)
    hh = os.environ.get("HERMES_HOME", "").strip()
    if hh:
        env_paths.append(Path(hh) / ".env")
        env_paths.append(Path(hh) / "profiles" / "side" / ".env")
    env_paths.extend([
        Path.home() / ".hermes-demo" / ".env",
        Path.home() / ".hermes/profiles/audit/.env",
        Path.home() / ".hermes/profiles/coo/.env",
        Path.home() / ".hermes/profiles/bd/.env",
        Path.home() / ".hermes/profiles/default/.env",
        Path.home() / ".hermes/.env",
    ])
    for p in env_paths:
        if not p.exists():
            continue
        for line in p.read_text(errors="ignore").splitlines():
            if line.startswith("AGNES_API_KEY="):
                val = line.split("=", 1)[1].strip().strip('"').strip("'")
                if val.startswith("sk-"):
                    return val
    raise RuntimeError("AGNES_API_KEY not found. Add it to the active Hermes profile .env")


def file_to_data_uri(path):
    p = Path(path).expanduser()
    if not p.exists():
        raise FileNotFoundError(f"image file not found: {p}")
    mime, _ = mimetypes.guess_type(str(p))
    if not mime or not mime.startswith("image/"):
        # Agnes accepts common image data URIs; default to PNG for unknown image-like files.
        mime = "image/png"
    b64 = base64.b64encode(p.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{b64}"


def call_api(prompt, model, size, image_inputs=None, output_format="url", timeout=180):
    payload = {"model": model, "prompt": prompt, "size": size}

    if image_inputs:
        payload["extra_body"] = {
            "image": image_inputs,
            "response_format": output_format,
        }
    elif output_format == "b64_json":
        payload["return_base64"] = True
    else:
        payload["extra_body"] = {"response_format": "url"}

    headers = {
        "Authorization": f"Bearer {get_api_key()}",
        "Content-Type": "application/json",
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(ENDPOINT, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"API error {e.code}: {body[:800]}")


def save_result(result, outdir):
    if "data" not in result or not result["data"]:
        raise RuntimeError(f"No image data in response: {json.dumps(result)[:500]}")

    item = result["data"][0]
    out = Path(outdir)
    out.mkdir(parents=True, exist_ok=True)
    fpath = out / f"agnes_{int(time.time())}.png"

    if item.get("url"):
        urllib.request.urlretrieve(item["url"], str(fpath))
        return str(fpath)

    if item.get("b64_json"):
        fpath.write_bytes(base64.b64decode(item["b64_json"]))
        return str(fpath)

    raise RuntimeError(f"No url or b64_json in response: {json.dumps(result)[:500]}")


def main():
    parser = argparse.ArgumentParser(description="Agnes AI free image generation")
    parser.add_argument("prompt", help="Text prompt for image generation or editing")
    parser.add_argument("--image", nargs="*", default=[], help="Input public image URL(s) or Data URI(s) for img2img")
    parser.add_argument("--image-file", nargs="*", default=[], help="Local image file(s); converted to Data URI for img2img")
    parser.add_argument("--size", default=DEFAULT_SIZE, help=f"Output size (default: {DEFAULT_SIZE})")
    parser.add_argument("--model", default=DEFAULT_MODEL, help=f"Model name (default: {DEFAULT_MODEL})")
    parser.add_argument("--outdir", default=DEFAULT_OUTDIR, help=f"Output directory (default: {DEFAULT_OUTDIR})")
    parser.add_argument("--format", choices=["url", "b64_json"], default="url", help="API response format")
    args = parser.parse_args()

    image_inputs = list(args.image or [])
    image_inputs.extend(file_to_data_uri(p) for p in (args.image_file or []))

    print(f"Generating via Agnes: {args.prompt[:90]}...")
    result = call_api(args.prompt, args.model, args.size, image_inputs=image_inputs or None, output_format=args.format)
    fpath = save_result(result, args.outdir)
    print(fpath)


if __name__ == "__main__":
    main()
