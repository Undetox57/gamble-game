"""Report every tr()/txf() key (literal + runtime data) that has no Turkish entry yet.

Moved into the repo (E batch, 1.1.5) so CI can run it on every push:
    python tools/i18n_check.py        # exit 1 when a translation is missing
"""
import ast
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from gamble import config                       # noqa: E402
from gamble.i18n import TR, tr, set_lang         # noqa: E402

set_lang('tr')

tr_keys = set()


def walk(node):
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in ('tr', 'txf'):
        if node.args and isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str):
            tr_keys.add(node.args[0].value)
    for ch in ast.iter_child_nodes(node):
        walk(ch)


for dirpath, _dirs, files in os.walk(os.path.join(ROOT, 'gamble')):
    for f in files:
        if f.endswith('.py'):
            walk(ast.parse(open(os.path.join(dirpath, f), encoding='utf-8').read()))

# runtime keys: everything the UI prints through tr()
runtime = set(config.GAME_NAMES.values()) | set(config.GAME_SUBTITLES.values())
runtime |= {name for name, _ in config.CATEGORIES}
runtime |= {d['name'] for d in config.DIFFICULTIES.values()}
runtime |= {d['desc'] for d in config.DIFFICULTIES.values()}
runtime |= {t for _k, t, _d, _r in config.ACHIEVEMENTS} | {d for _k, _t, d, _r in config.ACHIEVEMENTS}
runtime |= {t for t, _kind, _body in config.ENDINGS.values()}
runtime |= {body for _t, _k, body in config.ENDINGS.values()}
runtime |= {j['name'] for j in config.JOBS}
runtime |= {i['name'] for i in config.ITEMS} | {i['desc'] for i in config.ITEMS}
from gamble.style import KEY_NAMES                                    # noqa: E402
runtime |= set(KEY_NAMES.values())

keys = tr_keys | runtime
have = set(TR['tr'])
missing = sorted(k for k in keys if k not in have)
unused = sorted(k for k in have if k not in keys)
still_en = sorted(k for k in missing if tr(k) == k and k != 'Blackjack')
print(f'{len(keys)} keys used, {len(have)} in the table, {len(missing)} missing, {len(unused)} unused')
print(f'{len(still_en)} of the missing are NOT translated:')
for k in still_en:
    print('  ', repr(k))
sys.exit(1 if missing else 0)
