import re, sys
from pathlib import Path

p = Path(sys.argv[1])
text = p.read_text(encoding='utf-8')

# Replace longtable column specs with versions that draw vertical lines between columns.
def rebuild(spec):
    # Tokenize column types: >{...}p{...}, >{...}l, @{...}, p{...}, m{...}, b{...}, X, l, r, c, |.
    # Treat the optional >{...} prefix and the column letter/type as a single token.
    tokens = re.findall(r'@\{(?:[^{}]|\{[^{}]*\})*\}|(?:>\{(?:[^{}]|\{[^{}]*\})*\})?(?:p\{(?:[^{}]|\{[^{}]*\})*\}|m\{(?:[^{}]|\{[^{}]*\})*\}|b\{(?:[^{}]|\{[^{}]*\})*\}|X|l|r|c)|\|', spec)
    # Build result with | between adjacent column-type tokens
    result = []
    prev_is_col = False
    for tok in tokens:
        if tok == '|':
            result.append(tok)
            prev_is_col = False
            continue
        if tok.startswith('@'):
            result.append(tok)
            prev_is_col = False
            continue
        # column-type token
        if prev_is_col:
            result.append('|')
        result.append(tok)
        prev_is_col = True
    new_spec = ''.join(result)
    # Ensure leading and trailing vertical bars
    if not new_spec.startswith('|'):
        new_spec = '|' + new_spec
    if not new_spec.endswith('|'):
        new_spec = new_spec + '|'
    return new_spec

def replace_widths(spec, widths):
    """Replace each \real{0.XXXX} in the column spec with custom relative widths."""
    width_pattern = re.compile(r'\\real\{0\.[0-9]+\}')
    matches = list(width_pattern.finditer(spec))
    if len(matches) != len(widths):
        return spec
    result = spec
    for m, w in zip(reversed(matches), reversed(widths)):
        result = result[:m.start()] + f'\\real{{{w:.4f}}}' + result[m.end():]
    return result

def actor_columnspec(widths):
    """Build a wrapping longtable column spec for the actor reference tables.
    The Preview column contains the cameo and unit sprite stacked vertically;
    the last (Notable traits) column is a p-column so long trait lists wrap
    instead of sprawling off the page."""
    return '|' + '|'.join([
        r'>{\centering\arraybackslash}p{' + f'{widths[0]:.4f}' + r'\linewidth}',
        r'p{' + f'{widths[1]:.4f}' + r'\linewidth}',
        r'p{' + f'{widths[2]:.4f}' + r'\linewidth}',
        r'p{' + f'{widths[3]:.4f}' + r'\linewidth}',
        r'>{\raggedleft\arraybackslash}p{' + f'{widths[4]:.4f}' + r'\linewidth}',
        r'>{\raggedleft\arraybackslash}p{' + f'{widths[5]:.4f}' + r'\linewidth}',
        r'p{' + f'{widths[6]:.4f}' + r'\linewidth}',
        r'>{\raggedleft\arraybackslash}p{' + f'{widths[7]:.4f}' + r'\linewidth}',
        r'>{\raggedleft\arraybackslash}p{' + f'{widths[8]:.4f}' + r'\linewidth}',
        r'p{' + f'{widths[9]:.4f}' + r'\linewidth}',
        r'p{' + f'{widths[10]:.4f}' + r'\linewidth}',
    ]) + '|'

# Replace booktabs rules with plain \hline BEFORE we detect table headers by looking for \hline.
text = text.replace(r'\toprule\noalign{}', r'\hline')
text = text.replace(r'\midrule\noalign{}', r'\hline')
text = text.replace(r'\bottomrule\noalign{}', r'\hline')

# Process each longtable opening manually so we can consume the entire column spec.
pattern = re.compile(r'(\\begin\{longtable\}(?:\[[^\]]*\])?\{)')
parts = []
last_end = 0
n = 0
for m in pattern.finditer(text):
    parts.append(text[last_end:m.start()])
    start = m.end()
    depth = 0
    i = start
    while i < len(text):
        c = text[i]
        if c == '{':
            depth += 1
        elif c == '}':
            if depth == 0:
                break
            depth -= 1
        i += 1
    spec = text[start:i]
    # Peek at the first header row to identify the table type.
    hline_pos = text.find('\\hline', i + 1)
    next_hline_pos = text.find('\\hline', hline_pos + 1) if hline_pos != -1 else -1
    header_text = text[hline_pos:next_hline_pos] if hline_pos != -1 and next_hline_pos != -1 else ''
    if 'Preview' in header_text and 'Notable traits' in header_text:
        # Widen the Preview column so the cameo + unit sprite stack is readable.
        actor_widths = [0.18, 0.09, 0.11, 0.07, 0.05, 0.05, 0.06, 0.05, 0.05, 0.09, 0.10]
        new_spec = actor_columnspec(actor_widths)
    elif 'Preview' in header_text and 'Primary Terrain' in header_text:
        terrain_widths = [0.26, 0.06, 0.13, 0.05, 0.07, 0.43]
        new_spec = replace_widths(rebuild(spec), terrain_widths)
    elif 'Preview' in header_text and 'Key Traits' in header_text and 'Notes' in header_text:
        # Appendix K — Environmental Actor Reference
        # Widen the Preview column so small actors (civilians, TS structures) are readable;
        # trim the Actor/Size/Notes columns slightly to make room.
        environmental_widths = [0.18, 0.08, 0.18, 0.08, 0.18, 0.26]
        new_spec = replace_widths(rebuild(spec), environmental_widths)
    else:
        new_spec = rebuild(spec)
    parts.append(m.group(1) + new_spec + text[i])
    last_end = i + 1
    n += 1
parts.append(text[last_end:])
text = ''.join(parts)
print(f'Added vertical lines to {n} longtable specs')

# Add horizontal lines between every row in longtables (spreadsheet style).
# Process each longtable separately so we do not add \hline outside tables.
def add_hlines_to_longtable(m):
    table = m.group(0)
    table = re.sub(
        r'\\\\\n(?!\s*\\(?:hline|endhead|endlastfoot|end\{longtable\}))',
        r'\\\\\n\\hline\n',
        table,
        flags=re.MULTILINE
    )
    return table

text = re.sub(
    r'\\begin\{longtable\}.*?\\end\{longtable\}',
    add_hlines_to_longtable,
    text,
    flags=re.DOTALL
)

# Wrap wide reference appendices (I, J, K) in landscape for better table fit.
# Use the section labels as anchors because Pandoc may split the section title across lines.
# Switch to plain page style and smaller type inside landscape to keep longtables on page.
landscape_prefix = (
    '\\begin{landscape}\\pagestyle{fancy}\\scriptsize'
    '\\setlength{\\LTpre}{0pt}\\setlength{\\LTpost}{0pt}'
    '\\renewcommand{\\arraystretch}{1.2}\n'
)
landscape_suffix = '\\end{landscape}\\clearpage\\pagestyle{fancy}\n'


def wrap_landscape(m, title):
    r"""Wrap a landscape appendix and force the running header to its clean title.

    The \markboth is placed *before* the landscape environment so that the mark
    is recorded before pdflscape ships the page; this stops the header from
    carrying over the previous appendix's title (especially when one landscape
    appendix follows another)."""
    content = m.group(1)
    # Split the leading \section{...} command from the rest so we can insert a
    # \markboth after it. The section title may contain a newline, so [^}]* works.
    section_match = re.match(r'(\\section\{[^}]*\})(.*)', content, re.DOTALL)
    if not section_match:
        clean_title = title.replace('\n', ' ')
        return f'\\clearpage\\markboth{{{clean_title}}}{{{clean_title}}}\n' + landscape_prefix + content + landscape_suffix
    section_cmd, rest = section_match.groups()
    section_cmd = section_cmd.replace('\n', ' ')
    clean_title = title.replace('\n', ' ')
    return (f'\\clearpage\\markboth{{{clean_title}}}{{{clean_title}}}\n' +
            landscape_prefix + section_cmd + '\n' +
            f'\\def\\leftmark{{{clean_title}}}\n' +
            rest + f'\n\\markboth{{{clean_title}}}{{{clean_title}}}\n' +
            landscape_suffix)


text = re.sub(
    r'(\\section\{Appendix I --- Actor\nReference\}.*?)(?=\\section\{Appendix J)',
    lambda m: wrap_landscape(m, 'Appendix I --- Actor Reference'),
    text,
    flags=re.DOTALL
)
text = re.sub(
    r'(\\section\{Appendix J --- Terrain Tile\nReference\}.*?)(?=\\section\{Appendix K)',
    lambda m: wrap_landscape(m, 'Appendix J --- Terrain Tile Reference'),
    text,
    flags=re.DOTALL
)
text = re.sub(
    r'(\\section\{Appendix K --- Environmental Actor\nReference\}.*?)(?=\\end\{document\})',
    lambda m: wrap_landscape(m, 'Appendix K --- Environmental Actor Reference'),
    text,
    flags=re.DOTALL
)

# Limit terrain preview image height so longtable rows stay short.
def limit_terrain_image(m):
    opts = m.group(1)
    filename = m.group(2)
    if 'height=' in opts:
        return m.group(0)
    # Increase preview size substantially (effective visible size is ~0.55 * this due to pandocbounded scaling).
    if opts.strip():
        return f'\\includegraphics[{opts},height=96pt]{{{filename}}}'
    return f'\\includegraphics[height=96pt]{{{filename}}}'

text = re.sub(
    r'\\includegraphics\[([^\]]*)\]\{((?:images/terrain/)[^}]+)\}',
    limit_terrain_image,
    text
)

# Limit actor cameo/unit images in the actor reference tables.
def limit_actor_image(m):
    opts = m.group(1)
    filename = m.group(2)
    is_unit = filename.endswith('_unit.png')
    # Unit sprites (battlefield preview) are capped at half the column width so
    # wide D2K/TS buildings don't dwarf the row, while the cameo still fills the
    # column. Both are height-limited to keep the stacked pair compact.
    # D2K buildings were previously too large and then looked horizontally compressed.
    # 0.33\linewidth gives them ~33% more width than the 0.25\linewidth cap while still
    # keeping them smaller than the other mods' 0.5\linewidth unit previews.
    if is_unit and '/d2k/' in filename:
        width = '0.33\\linewidth'
    else:
        width = '0.5\\linewidth' if is_unit else '\\linewidth'
    if 'height=' in opts and 'width=' in opts:
        return m.group(0)
    if 'height=' in opts:
        return f'\\includegraphics[{opts},width={width}]{{{filename}}}'
    if 'width=' in opts:
        return f'\\includegraphics[{opts},height=96pt]{{{filename}}}'
    return f'\\includegraphics[width={width},height=96pt]{{{filename}}}'

text = re.sub(
    r'\\includegraphics\[([^\]]*)\]\{((?:images/actors/)[^}]+)\}',
    limit_actor_image,
    text
)

# Stack the cameo and unit images vertically in the actor Preview column
# (the Markdown source places them side-by-side; Pandoc emits them on the
# same line, so we insert a paragraph break in the LaTeX output).
text = re.sub(
    r'(\\pandocbounded\{\\includegraphics\[[^\]]*\]\{(?:images/actors/)[^}]+\}\})\s*(\\pandocbounded\{\\includegraphics\[[^\]]*\]\{(?:images/actors/)[^}]+\}\})',
    r'\1\\par\2',
    text
)

# Limit environmental preview images in the environmental actor reference tables.
def limit_environmental_image(m):
    opts = m.group(1) or ''
    filename = m.group(2)
    if 'height=' in opts or 'width=' in opts:
        return m.group(0)
    # Stretch the preview image to fill the wider environmental Preview column.
    # Cap height so tall cropped images (e.g. civilians) do not make rows too large.
    if opts.strip():
        return f'\\includegraphics[{opts},width=\\linewidth,height=160pt]{{{filename}}}'
    return f'\\includegraphics[width=\\linewidth,height=160pt]{{{filename}}}'

text = re.sub(
    r'\\includegraphics(?:\[([^\]]*)\])?\{((?:images/environmental/)[^}]+)\}',
    limit_environmental_image,
    text
)

p.write_text(text, encoding='utf-8')
print('updated', p)
