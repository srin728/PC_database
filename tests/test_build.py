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
    assert mod.normalize_url(
        r'[https://doi.org/10.1016/S0012-365X(00)00199-0](https://doi.org/10.1016/S0012-365X\(00\)00199-0)'
    ) == 'https://doi.org/10.1016/S0012-365X(00)00199-0'


def test_survey_paths_are_recognized():
    assert mod.is_survey_bib(mod.BIB_DIR / 'survey' / 'survey.bib')
    assert mod.is_survey_bib(mod.BIB_DIR / 'Survey' / 'surveys_2026.bib')
    assert mod.is_survey_bib(mod.BIB_DIR / 'survey.bib')
    assert not mod.is_survey_bib(mod.BIB_DIR / 'SODA' / 'SODA_2026.bib')



def test_dblp_author_suffix_is_removed_from_display():
    assert mod.split_authors('Lu Liu 0030 and Alice Example') == ['Lu Liu', 'Alice Example']
    assert mod.split_authors('Liu 0030, Lu') == ['Lu Liu']
    assert mod.normalize_dblp_author_name('Author 123') == 'Author 123'


def test_safe_bib_filename():
    assert mod.safe_bib_filename('Liu2026') == 'Liu2026.bib'
    assert mod.safe_bib_filename('Key:with/slash') == 'Key_with_slash.bib'


def test_first_page_number():
    assert mod.first_page_number('3--27') == 3
    assert mod.first_page_number('123-130') == 123
    assert mod.first_page_number('S41--S50') == 41
    assert mod.first_page_number('') is None
