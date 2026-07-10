#!/usr/bin/env bash
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
out="$root/assets/structures/breeding-structure"
mkdir -p "$out"

fetch() {
  local name="$1"
  local url="$2"
  echo "$name"
  curl -L --fail --retry 3 --retry-delay 2 \
    -A 'Mozilla/5.0' \
    -o "$out/$name" \
    "$url"
}

fetch normal-breeding-structure.webp 'https://static.wikia.nocookie.net/mysingingmonsters/images/f/fe/Breeding_Structure.webp/revision/latest?cb=20251101020706'
fetch enhanced-breeding-structure.webp 'https://static.wikia.nocookie.net/mysingingmonsters/images/5/5d/Enhanced_Breeding_Structure.webp/revision/latest?cb=20251101021047'
fetch locked-breeding-structure.webp 'https://static.wikia.nocookie.net/mysingingmonsters/images/b/b7/Breeding_Structure_%28Locked%29.webp/revision/latest?cb=20230613032306'
fetch paironormal-breeding-structure.webp 'https://static.wikia.nocookie.net/mysingingmonsters/images/6/68/%22Breeding_Structure%22_of_the_Beyond.webp/revision/latest?cb=20251213214522'
fetch paironormal-enhanced-breeding-structure.webp 'https://static.wikia.nocookie.net/mysingingmonsters/images/d/db/Enhanced_%22Breeding_Structure%22_of_the_Beyond.webp/revision/latest?cb=20251213214551'
fetch paironormal-locked-breeding-structure.webp 'https://static.wikia.nocookie.net/mysingingmonsters/images/f/f4/%22Breeding_Structure%22_of_the_Beyond_%28Locked%29.webp/revision/latest?cb=20251213214225'

file "$out"/* || true
