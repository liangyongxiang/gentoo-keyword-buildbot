#!/usr/bin/env python3

import os
import portage
import shutil
import subprocess
import sys
import markdown

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
    #return out.decode('utf-8').splitlines()
    return out.decode('utf-8').splitlines()[800:1000]

def markdown_to_html(text, html_file):
    with open (html_file, 'w') as f:
        html = markdown.markdown(text, extensions=['markdown.extensions.tables'])
        f.write(html)

def main():
    table_header = '''
| pakcage | keywords | eix-info |
| ------- | -------- | -------- |
'''
    riscv_keyworded_doc = '#RISCV Keyworded Pakcage\n' + table_header
    arm64_keyworded_doc = '#ARM64 Keyworded Pakcage\n' + table_header
    none_keyworded_doc  = '#None  Keyworded Pakcage\n' + table_header

    for name in eix_get_packages():
        print('process %s' % name)
        pkg = keyworded(name)
        atom_line = '| **%s** | <span style="color:blue">%s</span> | %s |\n' % (pkg['atom'], pkg['keywords'], pkg['eix-info'])
        if pkg['riscv_keyworded']:
            riscv_keyworded_doc += atom_line
        elif pkg['arm64_keyworded']:
            arm64_keyworded_doc += atom_line
        else:
            none_keyworded_doc += atom_line

    path = 'output'
    if os.path.isdir(path):
        shutil.rmtree(path)
    os.mkdir(path)

    markdown_to_html(riscv_keyworded_doc, 'output/riscv.html')
    markdown_to_html(arm64_keyworded_doc, 'output/arm64.html')
    markdown_to_html(none_keyworded_doc,  'output/none.html')

if __name__ == "__main__":
    main()
