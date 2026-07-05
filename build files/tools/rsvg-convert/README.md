# Bundled rsvg-convert

This directory contains a bundled copy of `rsvg-convert` 2.40.20 for Windows, used by the `build_manual.ps1` export pipeline to convert the manual's SVG diagrams into PDF/DOCX-compatible images.

## Why it is bundled

Pandoc can convert Markdown to PDF and DOCX, but it requires an external SVG converter to embed SVG images. The standard tool is `rsvg-convert` from the GNOME librsvg project. Bundling it here means the manual can be exported on a clean Windows machine without requiring the user to install it separately or run Chocolatey as an administrator.

## License

`rsvg-convert` and its associated libraries are free software. The bundled copy is licensed under the terms in the included `COPYING` file (GPL / LGPL). This license applies **only** to the bundled tool in this directory, not to the manual text or game assets elsewhere in the repository.

## How it is used

`build_manual.ps1` automatically detects this bundled copy and adds its directory to the temporary `PATH` before invoking Pandoc. If a system-installed `rsvg-convert` is present, the script will use that instead.

## Updating

To update to a newer version, download a Windows build of `rsvg-convert` and replace the files in this directory, or install `rsvg-convert` system-wide (e.g., `choco install rsvg-convert -y` as Administrator) and remove this bundled copy.
