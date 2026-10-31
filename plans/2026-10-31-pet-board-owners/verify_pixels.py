"""Compare complete typed screens and active pixels; requires Pillow."""
from pathlib import Path
import gzip
from PIL import Image
root=Path(__file__).parent
for model,width,height,top in [("3032",320,200,8),("4032",320,200,36),("8032",640,250,11)]:
    ours=gzip.decompress((root/f"emu198x-{model}-screen.bin.gz").read_bytes())
    reference=gzip.decompress((root/f"vice-{model}-screen.bin.gz").read_bytes())
    assert ours == reference, f"{model}: screen RAM differs"
    a=Image.open(root/f"emu198x-{model}-typed.png").convert("RGB")
    b=Image.open(root/f"vice-{model}-typed.png").convert("RGB")
    # Fixed active apertures from the reference captures. Host palette and
    # presentation borders differ; every active monochrome pixel is checked.
    differences=sum(any(a.getpixel((x+32,y+24))) != any(b.getpixel((x+32,y+top)))
                    for y in range(height) for x in range(width))
    assert differences == 0, f"{model}: {differences} differing active pixels"
    print(f"{model}: {len(ours)} screen bytes and {width*height} active pixels match")
