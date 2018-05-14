#!/usr/bin/env python

def strip_output(nb):
    for cell in nb.cells:
        if hasattr(cell, "outputs"):
            cell.outputs = []
        if hasattr(cell, "prompt_number"):
            del cell["prompt_number"]


if __name__ == "__main__":
    from sys import stdin, stdout
    from nbformat import read, write

    nb = read(stdin, 4)
    strip_output(nb)
    write(nb, stdout, 4)
    stdout.write("\n")
