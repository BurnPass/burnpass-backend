#!/bin/sh
zbarimg --raw --quiet "theoqr.jpg">qr.txt
echo done
cat qr.txt | tr -d '<\n>' | python3 ./hc1_verify.py -v -U -p -A