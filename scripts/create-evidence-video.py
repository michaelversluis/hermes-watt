"""Create a labelled data replay from public samples, never a native-UI screenshot.

Optional developer tool; requires Pillow, ffmpeg and the macOS Arial fonts.
"""
import json
import subprocess
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / '.dev/evidence-video-v02'
OUT.mkdir(parents=True, exist_ok=True)
REPORTS = [json.loads((ROOT / f'docs/evidence/qwen-1.7b-{name}-10.json').read_text())
           for name in ('tickets', 'extraction')]


def font(size, bold=False):
    name = 'Arial Bold.ttf' if bold else 'Arial.ttf'
    return ImageFont.truetype('/System/Library/Fonts/Supplemental/' + name, size)


def fitted(draw, text, size, width, bold=False):
    while draw.textlength(text, font=font(size, bold)) > width:
        size -= 1
    return font(size, bold)


def slide(number, title, subtitle, lines=(), report=None):
    im = Image.new('RGB', (1280, 720), '#101b20')
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((54, 48, 222, 83), radius=10, fill='#b8f77c')
    d.text((67, 56), 'HERMES WATT', font=font(18, True), fill='#13251c')
    d.text((58, 118), title, font=fitted(d, title, 49, 1160, True), fill='#f6faf5')
    d.text((60, 190), subtitle, font=fitted(d, subtitle, 24, 1160), fill='#b7c8c4')
    if report:
        maximum = max(report['baseline']['median_joules'], report['candidate']['median_joules'])
        for i, key in enumerate(('baseline', 'candidate')):
            row = report[key]
            y = 274 + i * 142
            d.text((60, y), row['label'], font=font(24, True), fill='#f6faf5')
            d.text((865, y), f"{row['median_joules']:.3f} J", font=font(24, True), fill='#b8f77c')
            width = int(1080 * row['median_joules'] / maximum)
            d.rounded_rectangle((60, y + 44, 60 + width, y + 66), radius=10,
                                fill='#b8f77c' if i else '#73988d')
            d.text((60, y + 80), f"{row['passed']}/{row['checked']} correct · {row['runs']} repetitions · median {row['median_seconds']:.2f}s",
                   font=font(22), fill='#b7c8c4')
    else:
        for i, text in enumerate(lines):
            d.text((60, 282 + i * 65), text, font=fitted(d, text, 28, 1150, i == 0),
                   fill='#b8f77c' if i == 0 else '#e8f0ed')
    d.line((60, 611, 1220, 611), fill='#344c48', width=1)
    d.text((60, 634), 'RECORDED DATA REPLAY · Not a live Desktop screen recording', font=font(18), fill='#a6b9b2')
    d.text((60, 665), 'Estimated local CPU + GPU · Includes other processes · Cloud energy unknown', font=font(17), fill='#a6b9b2')
    d.text((1180, 634), f'{number}/6', font=font(17), fill='#a6b9b2')
    path = OUT / f'slide-{number}.png'
    im.save(path)
    return path


slides = [
    slide(1, 'Same good work. Less energy.', 'Token counts are not electricity measurements.', [
        'An energy receipt for your Hermes agent.',
        'Then test a more efficient way to do the same work.',
        'A saving only counts when every answer passes.',
        'Public code, raw samples and reproduction steps.']),
    slide(2, 'Try a comparison inside Hermes Watt.', 'Choose a fixed example task. Give consent. Start the local test.', [
        'One request per item versus one batch.',
        '3, 5 or 10 repetitions per approach; live progress.',
        'Stop safely. Keep your last completed result.',
        'No automatic downloads, cloud routing or model switching.']),
    slide(3, f"Tickets: {REPORTS[0]['observed_reduction_percent']:.1f}% lower local energy.",
          'Qwen3-1.7B-Q8_0 · Apple M3 Max · Ten repetitions per approach', report=REPORTS[0]),
    slide(4, f"Extraction: {REPORTS[1]['observed_reduction_percent']:.1f}% lower local energy.",
          'Invoice reference + exact amount from twelve fictional notes', report=REPORTS[1]),
    slide(5, 'Quality decides the result.', 'Two narrow tasks. Forty measured runs. Same checks for both approaches.', [
        '480 / 480 answers correct.',
        'An earlier smaller-model experiment failed its checks.',
        'It received no saving claim.',
        'These examples do not prove general task quality.']),
    slide(6, 'Good work. Less waste.', 'Native Desktop plugin + /watt · MIT · Public Hermes APIs', [
        'github.com/michaelversluis/hermes-watt',
        'Local estimates; provider inference energy stays unknown.',
        'No universal savings or CO2 claim.',
        'Built for the Nous Research Hermes Plugin Hackathon.']),
]
for i, path in enumerate(slides):
    subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-n', '-loop', '1', '-i', str(path),
                    '-t', '10', '-r', '24', '-c:v', 'libx264', '-pix_fmt', 'yuv420p', str(OUT / f'part-{i}.mp4')], check=True)
concat = OUT / 'concat.txt'
concat.write_text(''.join(f'file part-{i}.mp4\n' for i in range(len(slides))))
video = OUT / 'hermes-watt-evidence-v02.mp4'
subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-n', '-f', 'concat', '-safe', '0', '-i', str(concat),
                '-c', 'copy', '-movflags', '+faststart', str(video)], check=True)

# Catalog banner is a data illustration, labelled as such; never a fabricated screenshot.
im = Image.new('RGB', (1200, 600), '#101b20')
d = ImageDraw.Draw(im)
d.text((46, 38), 'HERMES WATT', font=font(20, True), fill='#b8f77c')
d.text((46, 86), 'Good work. Less waste.', font=font(48, True), fill='#f6faf5')
d.text((46, 153), '480/480 checked answers · 10 repetitions per approach', font=font(24), fill='#b7c8c4')
for i, report in enumerate(REPORTS):
    x = 46 + 568 * i
    d.rounded_rectangle((x, 222, x + 538, 476), radius=16, outline='#344c48', width=2)
    d.text((x + 24, 246), report['workload_label'], font=font(24, True), fill='#f6faf5')
    d.text((x + 24, 298), f"{report['observed_reduction_percent']:.1f}% lower", font=font(42, True), fill='#b8f77c')
    d.text((x + 24, 362), 'estimated local CPU + GPU energy', font=font(21), fill='#b7c8c4')
    d.text((x + 24, 409), f"{report['baseline']['median_joules']:.2f} J → {report['candidate']['median_joules']:.2f} J median", font=font(23), fill='#f6faf5')
d.text((46, 512), 'Recorded evidence illustration · Qwen3-1.7B · One M3 Max, two fixed tasks', font=font(20), fill='#b7c8c4')
d.text((46, 550), 'Includes other processes. No cloud, CO2 or universal savings claim.', font=font(20), fill='#b7c8c4')
im.save(ROOT / 'docs/evidence/comparison-v02.png')
print(video)
