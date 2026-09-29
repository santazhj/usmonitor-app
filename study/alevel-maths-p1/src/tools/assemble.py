import sys, re, pathlib
n, body, out = sys.argv[1], sys.argv[2], sys.argv[3]
h = pathlib.Path(__file__).with_name('header.md').read_text().replace('{N}', n)
pathlib.Path(out).write_text(h + pathlib.Path(body).read_text())
