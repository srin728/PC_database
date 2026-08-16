from pathlib import Path
import importlib.util
import unittest

MODULE_PATH = Path(__file__).resolve().parents[1] / 'scripts' / 'build.py'
spec = importlib.util.spec_from_file_location('pcdb_build_link_policy', MODULE_PATH)
mod = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(mod)


class PaperLinkPolicyTest(unittest.TestCase):
    def test_normal_doi_remains_primary(self):
        self.assertEqual(mod.preferred_paper_url('10.1000/example', 'https://dblp.org/x', 'DBLP:conf/test/Example'), 'https://doi.org/10.1000/example')

    def test_5555_uses_real_url(self):
        doi = '10.5555/3709347.3743822'
        url = 'https://dl.acm.org/doi/10.5555/3709347.3743822'
        self.assertEqual(mod.preferred_paper_url(doi, url, 'DBLP:conf/ifaamas/SchlotterC25'), url)
        self.assertEqual(mod.doi_resolver_url(doi), '')

    def test_5555_doi_url_is_rejected_and_dblp_used(self):
        doi = '10.5555/1283383.1283413'
        url = 'https://doi.org/10.5555/1283383.1283413'
        self.assertTrue(mod.is_non_resolving_doi_url(url))
        self.assertEqual(mod.preferred_paper_url(doi, url, 'DBLP:conf/soda/DemaineHM07'), 'https://dblp.org/rec/conf/soda/DemaineHM07')

    def test_dblp_key_fills_missing_legacy_link(self):
        self.assertEqual(mod.preferred_paper_url('', '', 'DBLP:conf/stacs/KawarabayashiK12a'), 'https://dblp.org/rec/conf/stacs/KawarabayashiK12a')

    def test_non_dblp_without_link_stays_unlinked(self):
        self.assertEqual(mod.preferred_paper_url('', '', 'LocalKey'), '')

    def test_other_test_unmaintained_prefixes_are_blocked(self):
        self.assertEqual(mod.doi_resolver_url('10.88888/example'), '')
        self.assertEqual(mod.doi_resolver_url('10.50505/example'), '')


if __name__ == '__main__':
    unittest.main()
