-- Preprocess images for the PDF pipeline:
-- 1. Replace SVG references with cached PDFs rendered via Edge/Chrome so
--    foreignObject/HTML text labels appear correctly.
-- 2. Remove the manual Markdown "Table of Contents" section so Pandoc's own
--    TOC (with page numbers) is the only one in the PDF.
function Image(el)
  if el.src:match("%.svg$") then
    local pdf_src = el.src:gsub("^images/", "build files/svg-pdf-cache/")
    pdf_src = pdf_src:gsub("%.svg$", ".pdf")
    el.src = pdf_src
  end
  return el
end

function Pandoc(doc)
  local new_blocks = {}
  local skip = false
  for _, block in ipairs(doc.blocks) do
    if block.t == "Header" and block.level == 2 then
      local text = pandoc.utils.stringify(block.content)
      if text == "Table of Contents" then
        skip = true
      elseif skip then
        skip = false
        table.insert(new_blocks, block)
      else
        table.insert(new_blocks, block)
      end
    elseif skip then
      -- Drop the manual TOC entries and the trailing horizontal rule.
      if block.t == "HorizontalRule" then
        skip = false
      end
    else
      table.insert(new_blocks, block)
    end
  end
  doc.blocks = new_blocks
  return doc
end
