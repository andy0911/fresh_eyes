#!/usr/bin/env bash
# 文書（PPTX / DOCX / PDF / XLSX など）をペルソナが読める形に変換する。
#   to-markdown.sh <input-file> <out-dir>
# 生成物:
#   <out-dir>/content.md      MarkItDown によるテキスト化（スライドは1枚ごとの区切り付き）
#   <out-dir>/document.pdf    PPTX/DOCX の場合、LibreOffice があれば PDF 化（見た目の確認用）
#   <out-dir>/pages/NNN.png   PDF があり pdftoppm があれば各ページの画像（任意）
set -euo pipefail
in="${1:?input file}"
out="${2:?output dir}"
mkdir -p "$out"
ext="${in##*.}"
ext="$(echo "$ext" | tr '[:upper:]' '[:lower:]')"

if command -v uvx >/dev/null 2>&1; then
  uvx --from 'markitdown[pptx,docx,pdf,xlsx]' markitdown -- "$in" > "$out/content.md"
elif command -v markitdown >/dev/null 2>&1; then
  markitdown -- "$in" > "$out/content.md"
else
  echo "markitdown が見つかりません。uv (uvx) か pip install markitdown を用意してください" >&2
  exit 1
fi

case "$ext" in
  pptx|ppt|docx|doc|key|odp)
    if command -v soffice >/dev/null 2>&1; then
      soffice --headless --convert-to pdf --outdir "$out" "$in" >/dev/null 2>&1 || true
      pdf="$(ls "$out"/*.pdf 2>/dev/null | head -n1 || true)"
      if [ -n "${pdf:-}" ] && [ "$pdf" != "$out/document.pdf" ]; then mv "$pdf" "$out/document.pdf"; fi
    fi
    ;;
  pdf)
    cp "$in" "$out/document.pdf"
    ;;
esac

if [ -f "$out/document.pdf" ] && command -v pdftoppm >/dev/null 2>&1; then
  mkdir -p "$out/pages"
  pdftoppm -r 80 -png "$out/document.pdf" "$out/pages/p" >/dev/null 2>&1 || true
fi

echo "content: $out/content.md"
[ -f "$out/document.pdf" ] && echo "pdf: $out/document.pdf"
[ -d "$out/pages" ] && echo "pages: $(ls "$out/pages" 2>/dev/null | wc -l | tr -d ' ') images in $out/pages"
exit 0
