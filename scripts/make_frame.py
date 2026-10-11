"""Wraps any image in an animated rounded-square frame (SVG) for the README.

Usage: python scripts/make_frame.py <image> <output.svg>
Example: python scripts/make_frame.py assets/my-photo.png assets/my-photo-frame.svg
"""
import base64, sys

if len(sys.argv) != 3:
    sys.exit("Usage: python scripts/make_frame.py <image> <output.svg>")
src, out = sys.argv[1], sys.argv[2]
try:
    data = open(src, "rb").read()
except FileNotFoundError:
    sys.exit(f"File not found: {src} (check the exact file name in the folder)")
# Detect the real format from the file contents (the extension can lie)
if data[:3] == b"\xff\xd8\xff":
    mime = "image/jpeg"
elif data[:4] == b"\x89PNG":
    mime = "image/png"
elif data[:6] in (b"GIF87a", b"GIF89a"):
    mime = "image/gif"
elif data[:4] == b"RIFF" and data[8:12] == b"WEBP":
    mime = "image/webp"
else:
    sys.exit("Unsupported image format (use JPG, PNG, GIF or WEBP).")
img = base64.b64encode(data).decode()


def rect(i, rx, **attrs):
    a = " ".join(f'{k.rstrip("_").replace("_", "-")}="{v}"' for k, v in attrs.items())
    return f'<rect x="{i}" y="{i}" width="{360-2*i}" height="{360-2*i}" rx="{rx}" {a}/>'


rivets = "".join(f'<circle cx="{x}" cy="{y}" r="3.5"/>' for x, y in
                 [(180, 28), (180, 332), (28, 180), (332, 180), (100, 28), (260, 28), (100, 332), (260, 332), (28, 100), (28, 260), (332, 100), (332, 260)])
svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="360" height="360" viewBox="0 0 360 360">
  <defs>
    <linearGradient id="steel" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#e3e9e6"/><stop offset="0.45" stop-color="#9aa7a1"/>
      <stop offset="0.55" stop-color="#6f7b76"/><stop offset="1" stop-color="#c3ccc8"/>
    </linearGradient>
    <clipPath id="clip">{rect(36, 18)}</clipPath>
    <radialGradient id="vignette" cx="0.5" cy="0.5" r="0.72">
      <stop offset="0.6" stop-color="#000" stop-opacity="0"/><stop offset="1" stop-color="#0d1110" stop-opacity="0.8"/>
    </radialGradient>
    <filter id="glow" x="-10%" y="-10%" width="120%" height="120%">
      <feGaussianBlur stdDeviation="5" result="b"/>
      <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>
    <style>
      @keyframes march {{ to {{ stroke-dashoffset: -200 }} }}
      @keyframes marchBack {{ to {{ stroke-dashoffset: 200 }} }}
      @keyframes pulse {{ 0%,100% {{ opacity: .35 }} 50% {{ opacity: 1 }} }}
      .ring {{ animation: march 8s linear infinite }}
      .ring2 {{ animation: marchBack 12s linear infinite }}
      .pulse {{ animation: pulse 3s ease-in-out infinite }}
    </style>
  </defs>
  {rect(4, 40, class_="ring", fill="none", stroke="#2e7d32", stroke_width="2", stroke_dasharray="12 8")}
  {rect(13, 34, class_="ring2", fill="none", stroke="#43a047", stroke_width="1", stroke_dasharray="2 8", opacity=".7")}
  {rect(22, 28, class_="pulse", fill="none", stroke="#7bd88f", stroke_width="3", filter="url(#glow)")}
  {rect(23, 27, fill="url(#steel)")}
  {rect(32, 21, fill="#0d1110")}
  <g clip-path="url(#clip)">
    <image x="36" y="36" width="288" height="288" preserveAspectRatio="xMidYMid slice" href="data:{mime};base64,{img}"/>
    {rect(36, 18, fill="url(#vignette)")}
  </g>
  {rect(36, 18, fill="none", stroke="#1b5e20", stroke_width="3")}
  <g fill="#5d6964" stroke="#d4dcd8" stroke-width="1">{rivets}</g>
</svg>
'''
open(out, "w", encoding="utf-8", newline="\n").write(svg)
print(f"Created {out} ({len(svg) // 1024} KB)")
