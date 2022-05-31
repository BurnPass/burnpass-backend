zbarimg --raw --quiet "QRcode.jpg"> qr.txt
cat qr.txt | tr -d '<\n>' | python3 ./hc1_verify.py -v -U -p