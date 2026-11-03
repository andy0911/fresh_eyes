#!/usr/bin/env bash
# 分担して書かれたレポートの断片を report.md に結合する。
# 使い方: assemble-report.sh <run-dir>
set -euo pipefail
d="${1:?run-dir}"
out="$d/report.md"
if [ -f "$out" ] && [ ! -f "$d/report-head.md" ]; then
  echo "report.md は既にあります（分担なし）: $out"; exit 0
fi
missing=""
for f in report-head.md report-body.md report-appendix.md; do
  [ -f "$d/$f" ] || missing="$missing $f"
done
if [ -n "$missing" ]; then
  echo "断片がありません:$missing" >&2
fi
{
  [ -f "$d/report-head.md" ] && cat "$d/report-head.md" && echo
  [ -f "$d/report-body.md" ] && cat "$d/report-body.md" && echo
  [ -f "$d/report-appendix.md" ] && cat "$d/report-appendix.md" && echo
} > "$out"
echo "結合しました: $out ($(wc -c < "$out") bytes)"
[ -z "$missing" ]
