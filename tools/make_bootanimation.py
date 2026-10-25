#!/usr/bin/env python3
"""Retired provisional-art generator; official boot media is required."""
import sys


def main():
    print("The provisional animation generator is retired by ROADMAP.md. "
          "Use: python3 tools/bootanimation_from_video.py /path/1000915952.mp4 --official",
          file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
