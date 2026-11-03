#!/usr/bin/env bash
# バージョンを上げ、変更履歴の Unreleased を確定し、コミットとタグを作る。
# 使い方: scripts/bump-version.sh <major|minor|patch|X.Y.Z> [--no-commit]
set -euo pipefail
cd "$(dirname "$0")/.."

arg="${1:-}"; nocommit="${2:-}"
[ -n "$arg" ] || { echo "使い方: $0 <major|minor|patch|X.Y.Z> [--no-commit]" >&2; exit 2; }

cur=$(python3 -c 'import json;print(json.load(open(".claude-plugin/plugin.json"))["version"])')
IFS=. read -r MA MI PA <<<"$cur"
case "$arg" in
  major) new="$((MA+1)).0.0" ;;
  minor) new="$MA.$((MI+1)).0" ;;
  patch) new="$MA.$MI.$((PA+1))" ;;
  *) [[ "$arg" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]] || { echo "不正なバージョン: $arg" >&2; exit 2; }; new="$arg" ;;
esac

if [ "$nocommit" != "--no-commit" ] && [ -n "$(git status --porcelain)" ]; then
  echo "作業ツリーに未コミットの変更があります。先にコミットしてください。" >&2; exit 1
fi
if git rev-parse -q --verify "refs/tags/v$new" >/dev/null; then
  echo "タグ v$new は既に存在します。" >&2; exit 1
fi

python3 - "$new" <<'PY'
import json,sys,pathlib,re,datetime
new=sys.argv[1]
c=pathlib.Path('CHANGELOG.md'); s=c.read_text()
today=datetime.date.today().isoformat()
m=re.search(r'## \[Unreleased\]\n(.*?)(?=\n## \[)', s, re.S)
if not m or not m.group(1).strip():
    sys.exit('CHANGELOG.md の [Unreleased] が空です。変更内容を書いてから実行してください。')

p=pathlib.Path('.claude-plugin/plugin.json'); d=json.loads(p.read_text()); d['version']=new
p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
p=pathlib.Path('.claude-plugin/marketplace.json'); d=json.loads(p.read_text())
for pl in d['plugins']:
    if pl['name']=='fresh-eyes': pl['version']=new
p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
body=m.group(1).strip('\n')
s=s.replace(m.group(0), f'## [Unreleased]\n\n## [{new}] - {today}\n\n{body}\n', 1)
prev=re.search(r'\[Unreleased\]: .*/compare/v([0-9.]+)\.\.\.HEAD', s)
if prev:
    old=prev.group(1)
    s=s.replace(prev.group(0), f'[Unreleased]: https://github.com/andy0911/fresh_eyes/compare/v{new}...HEAD\n[{new}]: https://github.com/andy0911/fresh_eyes/compare/v{old}...v{new}', 1)
c.write_text(s)
print(f'{new}')
PY

echo "バージョンを $cur → $new にしました。"
if [ "$nocommit" = "--no-commit" ]; then exit 0; fi
git add .claude-plugin/plugin.json .claude-plugin/marketplace.json CHANGELOG.md
git commit -q -m "v$new"
git tag -a "v$new" -m "Fresh Eyes v$new"
echo "コミットとタグ v$new を作りました。公開するには: git push origin main --follow-tags"
