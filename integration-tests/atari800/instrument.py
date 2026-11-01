#!/usr/bin/env python3
"""Add a test-only RAM result observer to Atari800's no-video main loop.

The emulator's CPU, POKEY and NetSIO are unchanged. Atari800 disables H: while
NetSIO is active, so the test guest signals completion via reserved RAM.
"""
from pathlib import Path
import sys

path = Path(sys.argv[1]) / 'src/atari_basic.c'
source = path.read_text()
if 'NIO_ATARI800_RESULT' in source:
    old = 'init=%u completed=%u failures=%u slow=%u\\n'
    if old in source:
        source = source.replace(old, 'init=%u completed=%u failures=%u slow=%u dli=%u\\n')
        source = source.replace('MEMORY_dGetByte(0x7004), MEMORY_dGetByte(0x7005));',
                                'MEMORY_dGetByte(0x7004), MEMORY_dGetByte(0x7005), MEMORY_dGetByte(0x7006));')
        path.write_text(source)
    raise SystemExit(0)
source = source.replace('#include "atari.h"', '#include "atari.h"\n#include "memory.h"\n#include <stdio.h>\n#include <stdlib.h>', 1)
old = '\twhile (TRUE) {\n\t\tAtari800_Frame();\n\t}'
new = '''\twhile (TRUE) {
        const char *path;
        Atari800_Frame();
        path = getenv("NIO_ATARI800_RESULT");
        if (path && MEMORY_dGetByte(0x7000) == 0xa5 && MEMORY_dGetByte(0x7001) == 0x5a) {
            FILE *out = fopen(path, "w");
            if (out) {
                fprintf(out, "init=%u completed=%u failures=%u slow=%u dli=%u\\n",
                    MEMORY_dGetByte(0x7002), MEMORY_dGetByte(0x7003),
                    MEMORY_dGetByte(0x7004), MEMORY_dGetByte(0x7005), MEMORY_dGetByte(0x7006));
                fclose(out);
            }
            return out ? 0 : 1;
        }
    }'''
if old not in source:
    raise SystemExit('Atari800 no-video main loop changed; review the observer')
path.write_text(source.replace(old, new, 1))
