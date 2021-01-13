#!/bin/bash

IMPL=${IMPL:-py}
HACK=${HACK:-0}

py() {
    case "$HACK" in
        0) ./synacor.py challenge.bin ;;
        1) ./synacor.py challenge.bin --poke '0209 0001 8007 0001' '156b 0001 8000 0001 0001 8001 0004' ;;
    esac
}

c() {
    case "$HACK" in
        0) ./synacor challenge.bin ;;
        1) ./synacor challenge.bin -p '0209 0001 8007 0001' -p '1576 7ffd'
    esac
}

if [ -z "$1" ]; then
    for i in 1 2 3 4 5 6 7 8; do
        echo
        $0 $i
    done
else
    exec 2>/dev/null
    case "$1" in
    1)
        echo '1: RTFM'
        cat arch-spec | grep "Here's a code"
        ;;
    2)
        echo '2: intro message'
        cat /dev/null | $IMPL | head -3
        ;;
    3)
        echo '3: self test'
        cat /dev/null | $IMPL | head -8 | tail -2
        ;;
    4)
        echo '4: tablet'
        cat dungeon.txt | head -2 | $IMPL | tail -4 | head -1
        ;;
    5)
        echo '5: twisty maze of little passages, all alike'
        cat dungeon.txt | head -17 | $IMPL | tail -16 | head -5
        ;;
    6)
        echo '6: teleporter'
        cat dungeon.txt | head -52 | $IMPL | tail -17 | head -5
        ;;
    B)
        echo 'B: book contents'
        cat dungeon.txt | head -55 | $IMPL | tail -46 | head -43
        ;;
    7)
        echo '7: hacked teleporter'
        cat dungeon.txt | head -52 | HACK=1 $IMPL | tail -15 | head -5
        ;;
    8)
        echo '8: vault'
        cat dungeon.txt | HACK=1 $IMPL | tail -6 | head -1
        ;;
    esac
fi

# head -52 dungeon.txt | ./synacor.py challenge.bin --debug --poke '209 1 8007 1' '1566 1 8000 1 1 8001 4 11 178b 1 8007 7ffd 15 15'
