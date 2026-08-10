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


def test_doi_normalization_removes_tex_escape():
    assert mod.normalize_doi(r'10.1007/978-3-031-38906-1\_8') == '10.1007/978-3-031-38906-1_8'
    assert mod.normalize_doi(r'10.1007/978-3-031-38906-1/\_8') == '10.1007/978-3-031-38906-1_8'
    assert mod.normalize_doi(r'https://doi.org/10.1007/978-3-031-38906-1\_8') == '10.1007/978-3-031-38906-1_8'
    assert mod.normalize_url(r'https://doi.org/10.1007/978-3-031-38906-1/\_8') == 'https://doi.org/10.1007/978-3-031-38906-1_8'


def test_survey_paths_are_recognized():
    assert mod.is_survey_bib(mod.BIB_DIR / 'survey' / 'survey.bib')
    assert mod.is_survey_bib(mod.BIB_DIR / 'Survey' / 'surveys_2026.bib')
    assert mod.is_survey_bib(mod.BIB_DIR / 'survey.bib')
    assert not mod.is_survey_bib(mod.BIB_DIR / 'SODA' / 'SODA_2026.bib')
