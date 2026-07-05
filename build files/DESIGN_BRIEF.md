# OpenRA Knowledge Base Manual - Design Brief

## Goal
Create a professional, readable Word and PDF reference document that OpenRA engine contributors, modders, and mission scripters can read on screen or print. The design must support both quick technical lookup and long-form narrative reading.

## Audience
- OpenRA engine contributors (C#)
- Modders writing YAML trait and weapon definitions
- Mission scripters writing Lua
- Technical writers maintaining the manual

## Tone and visual identity
- Clean, authoritative, technical.
- OpenRA-inspired palette: dark charcoal, steel blue, and a muted red accent.
- Avoid playful or distracting styling. Let the diagrams and code be the visual interest.

## Typography
- Body: Cambria or Georgia, 11 pt, 1.15 line spacing, left-aligned.
- Headings: Segoe UI or Calibri, bold.
  - Heading 1 (chapter titles): 20 pt, dark charcoal/steel blue, space before 24 pt, after 12 pt.
  - Heading 2 (major sections): 16 pt, dark charcoal, space before 18 pt, after 6 pt.
  - Heading 3 (subsections): 13 pt, bold, space before 12 pt, after 6 pt.
- Code / Source Code: Consolas 9.5 pt, light gray background (#F5F5F5), thin border, no spelling checks.
- Captions: 9 pt, italic, centered, color #666666.
- Footnotes / small text: 9 pt.

## Page layout
- Paper size: US Letter (8.5 x 11 in).
- Margins: 1 inch all around (or 0.75 inch for more technical density).
- Headers: Left = OpenRA Knowledge Base Manual, Right = page number.
- Footers: empty or minimal.

## Special elements
- Code blocks: light gray background, thin border, no text wrapping.
- Tables: header row with light gray background, alternating row colors optional.
- Blockquotes: left border, light gray background.
- Images: centered, with caption below.
- Internal links: blue, underlined.

## Cover page
- Title: OpenRA Knowledge Base Manual
- Subtitle: Engine and Modding Reference
- Version and date
- Optional: OpenRA logo or faction icon (if rights allow)

## Pandoc reference DOCX requirements
- Styles must be named exactly as Pandoc expects: Normal, Heading 1, Heading 2, Heading 3, Code, Source Code, Table, Caption, etc.
- The reference DOCX should contain at least one styled example of each element so Pandoc can map them.
- Save the styled file as: build files\reference.docx

## Workflow
1. Style the sample document (sample_styles.docx) in Word and save it as reference.docx.
2. Run build_manual.bat -Export docx to apply the template.
3. Review the generated DOCX and refine reference.docx.
4. Lock reference.docx once styling is final.
