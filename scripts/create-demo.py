"""Build a labelled evidence replay, not a fabricated live screen recording.
Requires Pillow and ffmpeg, used only for generating submission media.
"""
import json
import subprocess
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont

ROOT=Path(__file__).resolve().parents[1]
report=json.loads((ROOT/'docs/evidence/qwen-1.7b.json').read_text())
out=ROOT/'.dev/demo-video';out.mkdir(parents=True,exist_ok=True)
font_path='/System/Library/Fonts/Supplemental/Arial.ttf'
bold_path='/System/Library/Fonts/Supplemental/Arial Bold.ttf'
def font(size,bold=False):return ImageFont.truetype(bold_path if bold else font_path,size)
def slide(title, subtitle, lines, number, chart=False):
 im=Image.new('RGB',(1280,720),'#101b20');d=ImageDraw.Draw(im)
 d.rounded_rectangle((54,48,222,83),radius=10,fill='#b8f77c')
 d.text((67,56),'HERMES WATT',font=font(18,True),fill='#13251c')
 d.text((58,118),title,font=font(49,True),fill='#f6faf5')
 d.text((60,188),subtitle,font=font(23),fill='#b7c8c4')
 if chart:
  a,b=report['baseline'],report['candidate']
  for i,r in enumerate([a,b]):
   y=278+i*135
   d.text((60,y),r['label'],font=font(24,True),fill='#f6faf5')
   d.text((845,y),f"{r['median_joules']:.3f} J",font=font(24,True),fill='#b8f77c')
   d.rounded_rectangle((60,y+48,60+int(1000*r['median_joules']/a['median_joules']),y+70),radius=10,fill='#b8f77c' if i else '#73988d')
   d.text((60,y+80),f"{r['passed']}/{r['checked']} correct | {r['runs']} repetitions | median {r['median_seconds']:.2f}s",font=font(21),fill='#b7c8c4')
 else:
  for i,line in enumerate(lines):
   d.text((60,283+i*64),line,font=font(27,i==0),fill='#b8f77c' if i==0 else '#e8f0ed')
 d.line((60,628,1220,628),fill='#344c48',width=1)
 d.text((60,651),'RECORDED EVIDENCE REPLAY | Estimated local CPU + GPU | Not cloud energy',font=font(17),fill='#a6b9b2')
 d.text((1180,651),f'{number}/5',font=font(17),fill='#a6b9b2')
 path=out/f'slide-{number}.png';im.save(path);return path
slides=[
 slide('Good work. Less waste.','AI has an energy footprint. Token counts do not measure it.',[
  'A working observer plugin for Hermes 0.23+',
  'Task receipts, linked requests, failures and duration.',
  'Opt-in Apple Silicon energy estimates.',
  'No prompts stored. No telemetry uploads.'],1),
 slide('Make the boundary visible.','Every receipt separates local activity from remote inference.',[
  'Local CPU + GPU: estimated, system-wide.',
  'Cloud inference: unknown without provider telemetry.',
  'Missing counters never become zero.',
  'Overlapping task windows are excluded from totals.'],2),
 slide('Same task. Checked answers.','Qwen3-1.7B-Q8_0 | 12 synthetic tickets | alternating run order',[],3,True),
 slide(f"{report['observed_reduction_percent']:.1f}% lower in this experiment.",'Estimated chip energy on one M3 Max. Small repeated-run demonstration.',[
  '72 / 72 checked answers correct across both variants.',
  'An earlier, smaller model failed the checks.',
  'That run received no saving claim.',
  'Quality first. Then compare the energy.'],4),
 slide('An energy receipt for your agent.','Native Desktop page + /watt | MIT | Public APIs only',[
  'github.com/michaelversluis/hermes-watt',
  'Raw samples, checks and reproduction steps included.',
  'No universal savings or CO2 claim.',
  'Built for the Nous Research Hermes Plugin Hackathon.'],5)
]
for i,p in enumerate(slides):
 subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-n','-loop','1','-i',str(p),'-t','12','-r','24','-c:v','libx264','-pix_fmt','yuv420p',str(out/f'part-{i}.mp4')],check=True)
concat=out/'concat.txt';concat.write_text(''.join(f"file part-{i}.mp4\n" for i in range(len(slides))))
subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-n','-f','concat','-safe','0','-i',str(concat),'-c','copy','-movflags','+faststart',str(out/'hermes-watt-demo.mp4')],check=True)
# Use the genuine data chart as the repository's evidence image, not a fake UI screenshot.
(ROOT/'docs/evidence/comparison.png').write_bytes(slides[2].read_bytes())
print(out/'hermes-watt-demo.mp4')
