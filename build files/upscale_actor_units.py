from pathlib import Path
from PIL import Image

base = Path(r'C:\Users\Kmoney\Documents\AI Projects\Cameo Work\Game Sources and Development Reference Materials\OpenRA Manual\images\actors')

TARGET_MAX = 64  # after scaling, longest side will be at most 64 pixels

for mod in ['ra', 'cnc', 'd2k']:
    mod_dir = base / mod
    if not mod_dir.exists():
        continue
    for f in sorted(mod_dir.glob('*_unit.png')):
        im = Image.open(f)
        if im.mode == 'P':
            im = im.convert('RGBA')
        max_dim = max(im.width, im.height)
        scale = TARGET_MAX / max_dim
        new_size = (max(1, int(im.width * scale)), max(1, int(im.height * scale)))
        scaled = im.resize(new_size, Image.NEAREST)
        scaled.save(f)
        print(f'{f}: {im.width}x{im.height} -> {new_size[0]}x{new_size[1]}')

print('done')
