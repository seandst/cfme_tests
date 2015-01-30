import subprocess

from utils.conf import rdb
from utils.path import project_path

for breakpoint in rdb['breakpoints']:
    print breakpoint['summary']
    for file, line_hashes in breakpoint['line_hashes'].items():
        for line, hash in line_hashes.items():
            print file, line, hash
            filename = project_path.join(file).strpath
            cmd = 'git blame -L {line},+1 -p {filename}'.format(
                line=line, filename=filename
            )
            blame = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE)
            returncode = blame.wait()
            if returncode != 0:
                print 'wat'
                continue
            blame_hash = blame.stdout.read().splitlines()[0].split()[0]
            if blame_hash.startswith(hash):
                print 'woot'

