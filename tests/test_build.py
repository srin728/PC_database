from pathlib import Path
import importlib.util

MODULE_PATH = Path(__file__).resolve().parents[1] / 'scripts' / 'build.py'
spec = importlib.util.spec_from_file_location('pcdb_build', MODULE_PATH)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def test_nested_braces_and_tags():
    text = r'''@inproceedings{Key2026,
      author = {Garc{\\'i}a, Ana and Bob Example},
      title = {A {Parameterized} Result for $k$-Path},
      year = {2026},
      keywords = {kernelization; FPT algorithms, graph algorithms},
      doi = {10.1/example}
    }'''
    entries = mod.parse_bibtex(text)
    assert len(entries) == 1
    f = entries[0]['fields']
    assert mod.latex_to_text(f['title']) == 'A Parameterized Result for $k$-Path'
    assert mod.split_tags(f['keywords']) == ['kernelization', 'FPT algorithms', 'graph algorithms']
    assert mod.split_authors(f['author'])[1] == 'Bob Example'
