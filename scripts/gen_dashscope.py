"""Generate AI images for Train Decade via DashScope Wan2.6-t2i.

Reads keys from ~/.hermes/.env, calls the workspace-scoped endpoint, downloads
the generated image. Produces the hero + 2 article covers.

Style target: dark, cinematic, moody fitness imagery with neon accents — NOT
flat vector (that was the boring placeholder). Real photographic/illustrative
AI art.
"""
import os
import json
import sys
import urllib.request
import urllib.error

ENV = os.path.expanduser("~/.hermes/.env")


def load_env(path):
    cfg = {}
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            cfg[k.strip()] = v.strip().strip('"').strip("'")
    return cfg


def main():
    cfg = load_env(ENV)
    key = cfg.get("ALIBABA_MAAS_API_KEY", "")
    base = cfg.get("ALIBABA_MAAS_BASE_URL", "")
    if not key or not base:
        print("MISSING ALIBABA_MAAS_API_KEY or BASE_URL in .env", file=sys.stderr)
        sys.exit(2)
    # ensure scheme
    if not base.startswith("http"):
        base = "https://" + base
    # strip any OpenAI-compatible chat suffix — image gen uses the workspace root
    for suffix in ("/compatible-mode/v1", "/compatible-mode/v1/"):
        if base.endswith(suffix):
            base = base[: -len(suffix)]
    base = base.rstrip("/")
    endpoint = base + "/api/v1/services/aigc/multimodal-generation/generation"

    prompt = sys.argv[1]
    out_path = sys.argv[2]
    size = sys.argv[3] if len(sys.argv) > 3 else "1024*1024"

    body = {
        "model": "wan2.6-t2i",
        "input": {"messages": [{"role": "user", "content": [{"text": prompt}]}]},
        "parameters": {"size": size, "n": 1},
    }
    req = urllib.request.Request(
        endpoint,
        data=json.dumps(body).encode(),
        headers={
            "Authorization": "Bearer " + key,
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            resp = json.loads(r.read())
    except urllib.error.HTTPError as e:
        print("HTTP", e.code, e.read().decode()[:800], file=sys.stderr)
        sys.exit(1)

    # extract image URL
    try:
        choices = resp.get("output", {}).get("choices", [])
        img_url = choices[0]["message"]["content"][0]["image"]
    except (KeyError, IndexError, TypeError):
        print("BAD RESPONSE:", json.dumps(resp)[:800], file=sys.stderr)
        sys.exit(1)

    # download
    urllib.request.urlretrieve(img_url, out_path)
    print("WROTE", out_path)


if __name__ == "__main__":
    main()
