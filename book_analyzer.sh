#!/bin/bash
#
# book-analyzer.sh: Execute the book analyzer

if [[ -z "$1" || ! $1 =~ ^[0-9]+$ ]] ; then
  echo "Bad input"
  exit 1
fi

python3 src/book_analyzer.py "$@" <&0
