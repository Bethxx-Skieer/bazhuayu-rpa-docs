#!/bin/bash
IMGDIR="C:/Users/1/Documents/bazhuayu-rpa-docs/commands/datatable/images"
BASE="https://rpa.bazhuayu.com/helpcenter/docs"

declare -A SLUGS
SLUGS=(
  [0]="writetocellcommand"
  [1]="writetorowcommand"
  [2]="deletedatasheetrowcommand"
  [3]="adddatasheetcolumncommand"
  [4]="loopdatasheetcommand_1"
  [5]="readdatasheetcommand"
  [6]="importexceltodatasheetcommand"
  [7]="importcsvtodatasheetcommand"
  [8]="exportdatasheettofilecommand"
  [9]="exportmultidatasheettofilecommand"
)

for slug in "${SLUGS[@]}"; do
  echo "=== Processing $slug ==="
  html=$(curl -sL "$BASE/$slug")
  
  # Extract data-origin URLs in DOM order
  urls=$(echo "$html" | grep -oP "data-origin='[^']*'" | sed "s/data-origin='//;s/'//")
  
  if [ -z "$urls" ]; then
    echo "  No data-origin images found for $slug, trying og:image..."
    og=$(echo "$html" | grep -oP 'meta property="og:image" content="[^"]*"' | sed 's/.*content="//;s/"//')
    if [ -n "$og" ]; then
      urls="$og"
    fi
  fi
  
  i=1
  echo "$urls" | while IFS= read -r url; do
    if [ -n "$url" ]; then
      fname=$(printf "%s-%02d.png" "$slug" "$i")
      echo "  Downloading $url -> $fname"
      curl -sL -o "$IMGDIR/$fname" "$url"
      i=$((i+1))
    fi
  done
done

echo "Done downloading all images."
ls -la "$IMGDIR/"
