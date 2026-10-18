#!/usr/bin/env python3
"""統計 AI 自動化與腳本數量，寫入 AI_VERSION_REGISTRY.md 的「數量統計」區塊。

用法：
  python3 scripts/registry_stats.py          # 只印出統計
  python3 scripts/registry_stats.py --write  # 更新 AI_VERSION_REGISTRY.md 的統計區塊

統計範圍：Automations/*.yaml（自動化，一項一個 id）與 Scripts/*.yaml（腳本，一個含 sequence 的 key 一支）。
Automations／Scripts 目錄是 AI 管理的檔案（SOP-17），configuration.yaml 以 !include_dir_merge_list／named 載入。
"""
import datetime
import glob
import os
import sys

import yaml

H = '/homeassistant'
REG = H + '/AI_VERSION_REGISTRY.md'
BEGIN = '<!-- STATS:BEGIN -->'
END = '<!-- STATS:END -->'


class _Loader(yaml.SafeLoader):
    pass


def _any_tag(loader, suffix, node):
    if isinstance(node, yaml.ScalarNode):
        return loader.construct_scalar(node)
    if isinstance(node, yaml.SequenceNode):
        return loader.construct_sequence(node)
    return loader.construct_mapping(node)


_Loader.add_multi_constructor('!', _any_tag)


def _load(path):
    with open(path, encoding='utf-8') as f:
        return yaml.load(f, Loader=_Loader)


def count():
    a_files = sorted(glob.glob(os.path.join(H, 'Automations', '*.yaml')))
    s_files = sorted(glob.glob(os.path.join(H, 'Scripts', '*.yaml')))
    n_auto = 0
    for f in a_files:
        d = _load(f) or []
        n_auto += sum(1 for x in d if isinstance(x, dict) and 'id' in x)
    n_script = 0
    for f in s_files:
        d = _load(f) or {}
        if isinstance(d, dict):
            n_script += sum(1 for v in d.values() if isinstance(v, dict) and 'sequence' in v)
    return {'auto_files': len(a_files), 'auto': n_auto, 'script_files': len(s_files), 'script': n_script}


def block(c):
    today = datetime.date.today().isoformat()
    return '\n'.join([
        BEGIN,
        '## 數量統計（`scripts/registry_stats.py` 產生，更新於 %s）' % today,
        '',
        '| 項目 | 檔案數 | 數量 |',
        '|---|---|---|',
        '| AI 自動化（`Automations/*.yaml`，一項一個 id） | %d | **%d** |' % (c['auto_files'], c['auto']),
        '| AI 腳本（`Scripts/*.yaml`，一支一個 key） | %d | **%d** |' % (c['script_files'], c['script']),
        '',
        END,
    ])


def main():
    c = count()
    print('automation files %(auto_files)d / automations %(auto)d; script files %(script_files)d / scripts %(script)d' % c)
    if '--write' not in sys.argv:
        return
    s = open(REG, encoding='utf-8').read()
    b = block(c)
    if BEGIN in s and END in s:
        i = s.index(BEGIN)
        j = s.index(END) + len(END)
        s = s[:i] + b + s[j:]
    else:
        anchor = '## 現況總表（Automations）'
        assert s.count(anchor) == 1
        s = s.replace(anchor, b + '\n\n' + anchor, 1)
    open(REG, 'w', encoding='utf-8').write(s)
    print('registry updated')


if __name__ == '__main__':
    main()

