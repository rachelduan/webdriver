#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import random

def load_text(filename, dedup=False, shuffle=False):
    text = []
    for line in open(filename):
        line = line.strip()
        if line:
            text.append(line)
    if dedup:
        text = list(set(text))
    if shuffle:
        random.shuffle(text)
    return text


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(-1)
    locals()[sys.argv[1]](*sys.argv[2:])
