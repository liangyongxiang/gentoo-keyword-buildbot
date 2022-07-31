#!/usr/bin/env python3

import os
import portage
import shutil
import subprocess
import sys
import markdown
from datetime import datetime

def keyworded(atom):
    pkg = dict()
    pkg['atom'] = atom

    settings = portage.config(clone=portage.settings)
    matches = portage.portdb.match(atom)
    if len(matches) >= 1:
        settings.setcpv(portage.best(matches), mydb=portage.portdb)

    pkg['keywords'] = settings.get('KEYWORDS', '')
    pkg['riscv_keyworded'] = 'riscv' in pkg['keywords']
    pkg['arm64_keyworded'] = 'arm64' in pkg['keywords']

    sp = subprocess.Popen(("eix --pure-packages --compact --pattern %s" % atom).split(), stdout=subprocess.PIPE)
    out = sp.communicate()[0]
    assert sp.returncode == 0
    pkg['eix-info'] = out.decode('utf-8').split(':')[1].strip()

    return pkg

def eix_get_packages():
    subprocess.run("eix-update".split())

    sp = subprocess.Popen("eix --only-names --in-overlay gentoo".split(), stdout=subprocess.PIPE)
    out = sp.communicate()[0]
    assert sp.returncode == 0
    return out.decode('utf-8').splitlines()

def markdown_to_html(filename, text, md_text):
    with open (filename + '.txt', 'w') as f:
        f.write(text)

    with open (filename + '.html', 'w') as f:
        html = markdown.markdown(md_text, extensions=['markdown.extensions.tables'])
        f.write(html)

def main():
    table_header = '''
| pakcage | keywords | eix-info |
| ------- | -------- | -------- |
'''
    riscv_keyworded_md = '#RISCV Keyworded Pakcage\n' + table_header
    arm64_keyworded_md = '#ARM64 Keyworded Pakcage\n' + table_header
    none_keyworded_md  = '#None  Keyworded Pakcage\n' + table_header
    riscv_keyworded_text = ''
    arm64_keyworded_text = ''
    none_keyworded_text  = ''

    for name in eix_get_packages():
        print('process %s' % name)
        pkg = keyworded(name)
        md_line = '| **%s** | <span style="color:blue">%s</span> | %s |\n' % (pkg['atom'], pkg['keywords'], pkg['eix-info'])
        text_line = '%s\n' % pkg['atom']

        if pkg['riscv_keyworded']:
            riscv_keyworded_md += md_line
            riscv_keyworded_text += text_line
        elif pkg['arm64_keyworded']:
            arm64_keyworded_md += md_line
            arm64_keyworded_text += text_line
        else:
            none_keyworded_md += md_line
            none_keyworded_text += text_line

    path = 'output'
    if os.path.isdir(path):
        shutil.rmtree(path)
    os.mkdir(path)

    markdown_to_html('output/riscv', riscv_keyworded_text, riscv_keyworded_md)
    markdown_to_html('output/arm64', arm64_keyworded_text, arm64_keyworded_md)
    markdown_to_html('output/none',  none_keyworded_text,  none_keyworded_md)

if __name__ == "__main__":
    main()
