#!/usr/bin/env pwsh
# build_manual.ps1 — verify, assemble, and export the OpenRA Knowledge Base Manual.
#
# Usage:
#   powershell -ExecutionPolicy Bypass -File build_manual.ps1
#   powershell -ExecutionPolicy Bypass -File build_manual.ps1 -Export docx
#   powershell -ExecutionPolicy Bypass -File build_manual.ps1 -Export pdf
#   powershell -ExecutionPolicy Bypass -File build_manual.ps1 -Export all
#
# This script is intentionally simple and dependency-light. It runs the same
# verification steps that the manual has used throughout development, then
# optionally calls Pandoc for a mechanical Markdown -> DOCX/PDF export.
# A separate design pass (Claude, InDesign, etc.) can polish the exported file.

param(
    [ValidateSet("none", "docx", "pdf", "all")]
    [string]$Export = "none"
)

$ErrorActionPreference = "Stop"

$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$manualRoot = Resolve-Path (Join-Path $here "..")
$combined = Join-Path $manualRoot "OpenRA_Knowledge_Base_Manual.md"

function Step($msg) {
    Write-Host "`n==> $msg" -ForegroundColor Cyan
}

function Check-Exit($msg) {
    if ($LASTEXITCODE -ne 0) {
        throw $msg
    }
}

# Locate Pandoc. Common Windows install locations are checked first, then PATH.
function Find-Pandoc {
    $candidates = @(
        "C:\Program Files\Pandoc\pandoc.exe",
        "C:\ProgramData\chocolatey\bin\pandoc.exe",
        "C:\Users\$env:USERNAME\AppData\Local\Pandoc\pandoc.exe"
    )
    foreach ($c in $candidates) {
        if (Test-Path $c) { return $c }
    }
    $inPath = Get-Command pandoc -ErrorAction SilentlyContinue
    if ($inPath) { return $inPath.Source }
    return $null
}

# Locate a LaTeX engine for PDF export. We prefer xelatex for Unicode support.
function Find-LatexEngine {
    $commonPaths = @(
        "C:\Users\$env:USERNAME\AppData\Local\Programs\MiKTeX\miktex\bin\x64",
        "C:\Program Files\MiKTeX\miktex\bin\x64",
        "C:\Program Files (x86)\MiKTeX\miktex\bin",
        "C:\texlive\2024\bin\windows",
        "C:\texlive\2025\bin\windows"
    )
    foreach ($p in $commonPaths) {
        if (Test-Path $p) {
            $env:PATH = "$p;$env:PATH"
        }
    }
    foreach ($engine in @("lualatex", "xelatex", "pdflatex")) {
        $cmd = Get-Command $engine -ErrorAction SilentlyContinue
        if ($cmd) { return $engine }
    }
    return $null
}

# Locate the bundled rsvg-convert for SVG -> PDF/EMF conversion.
function Find-RsvgConvert {
    $bundled = Join-Path $here "tools\rsvg-convert\rsvg-convert.exe"
    if (Test-Path $bundled) {
        $env:PATH = "$(Split-Path -Parent $bundled);$env:PATH"
        $fc = Join-Path (Split-Path -Parent $bundled) "etc\fonts"
        if (Test-Path $fc) { $env:FONTCONFIG_PATH = $fc }
        return $bundled
    }
    $inPath = Get-Command rsvg-convert -ErrorAction SilentlyContinue
    if ($inPath) { return $inPath.Source }
    return $null
}

Step "Assembling combined manual..."
py (Join-Path $here "assemble_manual.py")
Check-Exit "assemble_manual.py failed"

Step "Verifying OpenRA source paths..."
py (Join-Path $here "verify_paths.py")
Check-Exit "verify_paths.py failed"

Step "Verifying internal Markdown links..."
py (Join-Path $here "verify_internal_links.py")
Check-Exit "verify_internal_links.py failed"

$pandoc = Find-Pandoc
if (-not $pandoc) {
    Write-Host "`nWARNING: Pandoc not found. Skipping DOCX/PDF export." -ForegroundColor Yellow
    Write-Host "Install Pandoc from https://pandoc.org/installing.html" -ForegroundColor Yellow
    exit 0
}
Write-Host "Found Pandoc at $pandoc" -ForegroundColor Green

$rsvg = Find-RsvgConvert
if ($rsvg) {
    Write-Host "Found rsvg-convert at $rsvg" -ForegroundColor Green
} else {
    Write-Host "`nWARNING: rsvg-convert not found. SVG images will be replaced by descriptions in DOCX/PDF export." -ForegroundColor Yellow
    Write-Host "Install rsvg-convert with: choco install rsvg-convert -y" -ForegroundColor Yellow
}

if ($Export -in @("docx", "all")) {
    Step "Exporting DOCX via Pandoc..."
    $out = Join-Path $manualRoot "OpenRA_Knowledge_Base_Manual.docx"
    $ref = Join-Path $here "reference.docx"
    Push-Location $manualRoot
    try {
        if (Test-Path $ref) {
            & $pandoc $combined -o $out --reference-doc=$ref
        } else {
            & $pandoc $combined -o $out
        }
    } finally {
        Pop-Location
    }
    Check-Exit "Pandoc DOCX export failed"
    Write-Host "Wrote $out" -ForegroundColor Green
}

if ($Export -in @("pdf", "all")) {
    Step "Exporting PDF via Pandoc..."
    $engine = Find-LatexEngine
    if (-not $engine) {
        Write-Host "`nERROR: No LaTeX engine found for PDF export." -ForegroundColor Red
        Write-Host "Install MiKTeX (recommended) or TeX Live, then re-run." -ForegroundColor Red
        Write-Host "MiKTeX: https://miktex.org/download" -ForegroundColor Red
        exit 1
    }
    Write-Host "Using LaTeX engine: $engine" -ForegroundColor Green

    $out = Join-Path $manualRoot "OpenRA_Knowledge_Base_Manual.pdf"
    $tex = Join-Path $manualRoot "OpenRA_Knowledge_Base_Manual.tex"
    $vlinesScript = Join-Path $here "format_tables_vlines.py"
    Push-Location $manualRoot
    try {
        $header = Join-Path $here "header.tex"
        $filter = Join-Path $here "svg-to-pdf.lua"
        $svgConverter = Join-Path $here "convert_svgs_for_pdf.py"
        if (Test-Path $svgConverter) {
            Step "Converting SVGs to PDFs via Edge/Chrome for correct text rendering..."
            & py $svgConverter
        }
        Step "Generating LaTeX source..."
        & $pandoc $combined -o $tex --pdf-engine=$engine --toc --lua-filter=$filter -V title="OpenRA Knowledge Base Manual" -V toc-title="Table of Contents" -V geometry:margin=0.75in -V fontsize=11pt -V colorlinks=true -V linkcolor=blue -V urlcolor=blue --include-in-header=$header
        Check-Exit "Pandoc LaTeX generation failed"
        Step "Adding vertical lines to tables..."
        & py $vlinesScript $tex
        Check-Exit "Table vertical-line post-processing failed"
        Step "Compiling PDF from LaTeX (pass 1)..."
        & $engine -interaction=nonstopmode -halt-on-error $tex
        Check-Exit "LaTeX PDF compilation failed"
        Step "Compiling PDF from LaTeX (pass 2 for TOC and hyperlinks)..."
        & $engine -interaction=nonstopmode -halt-on-error $tex
        Check-Exit "LaTeX PDF compilation failed"
    } finally {
        Pop-Location
    }
    if (Test-Path $out) {
        Write-Host "Wrote $out" -ForegroundColor Green
    } else {
        throw "PDF output not found after compilation"
    }
}

Write-Host "`nBuild complete." -ForegroundColor Green
