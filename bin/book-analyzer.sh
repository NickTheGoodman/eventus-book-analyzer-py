#!/bin/bash
#
# book-analyzer.sh: Execute the book analyzer

if [[ -z "$1" || ! $1 =~ ^[0-9]+$ ]] ; then
  echo "Bad input"
  exit 1
fi
targetSize="$1"

python src/book-analyzer.py "$targetSize" <&0
