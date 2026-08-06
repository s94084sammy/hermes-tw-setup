#!/usr/bin/env python3
"""Agnes AI 免費生圖 — txt2img + img2img
Usage:
  python3 generate.py "prompt" [--image URL] [--size WxH] [--model NAME] [--outdir DIR]
"""

import argparse, base64, json, os, sys, time, urllib.request, urllib.error
from pathlib import Path

BASE_URL = "https://apihub.agnes-ai.com"
ENDPOINT = f"{BASE_URL}/v1/images/generations"
DEFAULT_MODEL = "agnes-image-2.1-flash"
DEFAULT_SIZE = "1024x768"
DEFAULT_OUTDIR = "/tmp/agnes-output"


def get_api_key():
    for var in ["AGNES_API_KEY"]:
        key = os.environ.get(var)
        if key and key.startswith("sk-"):
            return key
    env_paths = [
        
        
        
        os.path.expanduser("~/.hermes/.env"),
    ]
    for p in env_paths:
        if os.path.exists(p):
            with open(p) as f:
                for line in f:
                    if line.startswith("AGNES_API_KEY="):
                        val = line.strip().split("=", 1)[1].strip().strip('"').strip("'")
                        if val.startswith("sk-"):
                            return val
    raise RuntimeError("AGNES_API_KEY not found. Add to ~/.hermes/profiles/<profile>/.env")


def call_api(prompt, model, size, image_urls=None, timeout=120):
    payload = {"model": model, "prompt": prompt, "size": size}

    if image_urls:
        payload["extra_body"] = {
            "image": image_urls,
            "response_format": "url",
        }
    else:
        payload["extra_body"] = {"response_format": "url"}

    api_key = get_api_key()
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(ENDPOINT, data=data, headers=headers, method="POST")

    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"API error {e.code}: {body[:500]}")


def download_image(url, outdir):
    path = Path(outdir)
    path.mkdir(parents=True, exist_ok=True)
    ext = ".png"
    fname = f"agnes_{int(time.time())}{ext}"
    fpath = path / fname
    urllib.request.urlretrieve(url, str(fpath))
    return str(fpath)


def main():
    parser = argparse.ArgumentParser(description="Agnes AI free image generation")
    parser.add_argument("prompt", help="Text prompt for image generation")
    parser.add_argument("--image", nargs="*", default=None, help="Input image URL(s) for img2img")
    parser.add_argument("--size", default=DEFAULT_SIZE, help=f"Output size (default: {DEFAULT_SIZE})")
    parser.add_argument("--model", default=DEFAULT_MODEL, help=f"Model name (default: {DEFAULT_MODEL})")
    parser.add_argument("--outdir", default=DEFAULT_OUTDIR, help=f"Output directory (default: {DEFAULT_OUTDIR})")
    args = parser.parse_args()

    print(f"🎨 Generating: {args.prompt[:80]}...")
    result = call_api(args.prompt, args.model, args.size, args.image)

    if "data" not in result or not result["data"]:
        print("❌ No image data in response")
        print(json.dumps(result, indent=2)[:500])
        sys.exit(1)

    image_url = result["data"][0].get("url")
    if not image_url:
        print("❌ No URL in response")
        print(json.dumps(result, indent=2)[:500])
        sys.exit(1)

    fpath = download_image(image_url, args.outdir)
    print(f"✅ {fpath}")


if __name__ == "__main__":
    main()
