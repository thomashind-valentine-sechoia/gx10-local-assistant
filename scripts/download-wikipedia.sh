#!/bin/bash
set -euo pipefail
cd "$HOME/kiwix"
file=wikipedia_en_all_maxi_2026-08.zim
if [[ -f "$file" ]]; then exit 0; fi
wget --continue --tries=0 --timeout=60 --progress=dot:giga -O "$file.part" "https://download.kiwix.org/zim/wikipedia/$file"
echo "34162d18b9f96f494eac48a73a309c72e0bc95d85f76be405d0f5de795854aa6  $file.part" | sha256sum -c -
mv "$file.part" "$file"
date --iso-8601=seconds > download-complete.txt
