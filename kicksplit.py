import difflib
import json
import os.path
import re
from subprocess import Popen, PIPE
from tempfile import NamedTemporaryFile

# Path to the full TiddlyWiki
twpath = "wiki.html"

# Roughly how many chunks should the file be broken into?
max_chunks = 100

filesize = os.path.getsize(twpath)
maxchunk = filesize / max_chunks
jsonpath = '%s.json' % twpath
state = {'bytes': filesize, 'chunks': []}
pc = 0

if os.path.isfile(jsonpath):
    with open(jsonpath, 'r') as f:
        state = json.load(f)

    old = ""
    for c in state['chunks']:
        old += open(c['path']).read()

    p = Popen(['diff', '-wn', '-', twpath], stdin=PIPE, stdout=PIPE, bufsize=1)
    out, err = p.communicate(old)
    diff = out.splitlines()

    altered = [None]*len(state['chunks'])
    mode = None
    diffat = 0
    delta = 0
    remain = 0
    def find_chunk(at):
        global state
        global altered
        global orig
        i = 0
        n = 0
        for c in state['chunks']:
            if at < n + c['lines']:
                if not altered[i]:
                    altered[i] = {'lines': open(c['path']).readlines(),
                        'start': n, 'index': i}
                return altered[i]
            n += c['lines'] 
            i += 1

    for diffline in diff:
        if mode == "a":
            if remain > 0:
                c = find_chunk(diffat)
                c['lines'].insert(diffat - c['start'], diffline + "\n")
                delta += 1
                state['chunks'][c['index']]['lines'] = len(c['lines'])
                remain -= 1
                diffat += 1
            if remain == 0:
                mode = None
        else:
            m = re.match(r"^([ad])(\d+) (\d+)", diffline)
            if m:
                mode = m.group(1)
                diffat = int(m.group(2)) + delta
                remain = int(m.group(3))

                if mode == "d":
                    while remain > 0:
                        c = find_chunk(diffat)
                        del c['lines'][(diffat - c['start']) - 1]
                        state['chunks'][c['index']]['lines'] = len(c['lines'])
                        delta -= 1
                        remain -= 1
                    mode = None

    i = 0
    delta = 0
    for a in altered:
        if a:
            str = ''.join(a['lines'])
            fname = state['chunks'][i]['path']
            print("Updating %s" % fname)
            with open(fname, 'w') as f:
                f.write(str)
            delta = len(str)
        i += 1

    print("Changed bytes: %d" % delta)

else:
    linecount = 0
    chunk = ""

    def add_chunk():
        global pc
        global chunk
        global state
        global twpath
        global linecount
        if len(chunk) > 0:
            path = '%s.%03d' % (twpath, pc)
            state['chunks'].append({'lines': linecount, 'path': path})
            with open(path, 'w') as f:
                f.write(chunk)

            linecount = 0
            chunk = ""
            pc += 1

    # Ensure that files end on line endings, to make applying diffs
    # much simpler.
    txt = open(twpath).readlines()
    for line in txt:
        if len(line) > maxchunk:
            add_chunk()
            chunk = line
            linecount = 1
            add_chunk()
        else:
            chunk += line
            linecount += 1
            if len(chunk) > maxchunk:
                add_chunk()
    add_chunk()

with open(jsonpath, 'w') as f:
    f.write(json.dumps(state))
