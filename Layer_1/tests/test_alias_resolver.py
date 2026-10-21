"""Offline resolver regressions; compatible with unittest and pytest."""
import ast
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'scripts'))
from alias_resolver import resolve_alias_entry
from profile_fit import resolve_alias_flags, _alias_data


def record(brand, holding='Group', blocked=False):
    return {'marca': brand, 'holding': holding, 'hard_block': blocked}


def data(**aliases):
    return {'aliases': aliases}


class AliasResolverTests(unittest.TestCase):
    def test_empty_inputs(self):
        for raw in (None, '', '   ', '\t'):
            self.assertIsNone(resolve_alias_entry(raw, data(armani=record('Armani', blocked=True))))

    def test_exact_short_and_generic_labels_remain_valid(self):
        for alias in ('lv', 'lg', 'ysl', 'h&m', 'd&g', 'nike', 'zara', 'viva', 'beyond'):
            entry = record(alias)
            self.assertEqual(resolve_alias_entry('  ' + alias.upper() + '  ', data(**{alias: entry})), entry)

    def test_short_keys_are_exact_only(self):
        for alias, raw in [('adm', 'administradora'), ('bic', 'ubicación'), ('otb', 'football'), ('lv', 'Calvin Klein México'), ('nike', 'Nike México')]:
            self.assertIsNone(resolve_alias_entry(raw, data(**{alias: record(alias)})))

    def test_generic_keys_are_exact_only(self):
        for alias in ('beyond', 'confidencial', 'encanto', 'marketstrat', 'viva', 'yello'):
            self.assertIsNone(resolve_alias_entry(alias + ' consultores', data(**{alias: record(alias)})))

    def test_complete_phrase_matches(self):
        entry = record('Louis Vuitton')
        self.assertEqual(resolve_alias_entry('Louis Vuitton México', data(**{'louis vuitton': entry})), entry)

    def test_no_reverse_match(self):
        self.assertIsNone(resolve_alias_entry('aurora', data(**{'aurora profesional': record('Aurora Profesional')})))
        self.assertIsNone(resolve_alias_entry('giorgio', data(**{'giorgio armani beauty': record('Armani', blocked=True)})))

    def test_no_substrings_inside_words(self):
        for alias, raw in [('apple', "Applebee's"), ('honor', 'honorarios profesionales'), ('gucci', 'guccissimo')]:
            self.assertIsNone(resolve_alias_entry(raw, data(**{alias: record(alias)})))

    def test_regex_characters_are_literal(self):
        entry = record('Carter’s')
        self.assertEqual(resolve_alias_entry("Carter's México", data(**{"carter's": entry})), entry)
        self.assertIsNone(resolve_alias_entry('ACMEZTEST México', data(**{'acme.test': record('Other')})))

    def test_whitespace_unicode_normalization(self):
        entry = record('Louis Vuitton')
        self.assertEqual(resolve_alias_entry('ＬＯＵＩＳ  ＶＵＩＴＴＯＮ', data(**{'louis vuitton': entry})), entry)
        self.assertEqual(resolve_alias_entry('Louis\tVuitton México', data(**{'louis vuitton': entry})), entry)

    def test_does_not_drop_accents_or_punctuation(self):
        self.assertIsNone(resolve_alias_entry('estee lauder', data(**{'estée lauder': record('Estée Lauder')})))
        self.assertIsNone(resolve_alias_entry('loreal', data(**{"l'oréal": record("L'Oréal")})))

    def test_nested_specific_phrase_wins_in_both_orders(self):
        entries = [('giorgio armani', record('Giorgio Armani')), ('giorgio armani beauty', record('Armani Beauty'))]
        for pairs in (entries, entries[::-1]):
            self.assertEqual(resolve_alias_entry('Giorgio Armani Beauty México', {'aliases': dict(pairs)})['marca'], 'Armani Beauty')

    def test_specific_zara_home_beats_parent_if_present(self):
        aliases = {'zara': record('Zara'), 'zara home': record('Zara Home')}
        self.assertEqual(resolve_alias_entry('Zara Home México', {'aliases': aliases})['marca'], 'Zara Home')

    def test_calvin_klein_does_not_match_lv(self):
        aliases = {'lv': record('Louis Vuitton'), 'calvin klein': record('Calvin Klein')}
        self.assertEqual(resolve_alias_entry('Calvin Klein México', {'aliases': aliases})['marca'], 'Calvin Klein')

    def test_unrelated_companies_are_ambiguous_even_with_different_lengths(self):
        aliases = {'gucci': record('Gucci'), 'louis vuitton': record('Louis Vuitton')}
        for pairs in (list(aliases.items()), list(aliases.items())[::-1]):
            self.assertIsNone(resolve_alias_entry('Gucci / Louis Vuitton', {'aliases': dict(pairs)}))

    def test_equivalent_matches_are_not_ambiguous(self):
        entry = record('Armani', blocked=True)
        self.assertEqual(resolve_alias_entry('Armani / Armani Beauty', data(armani=entry, **{'armani beauty': entry})), entry)

    def test_disagreeing_flags_are_ambiguous(self):
        aliases = {'company alpha': record('Same', blocked=True), 'company beta': record('Same', blocked=False)}
        self.assertIsNone(resolve_alias_entry('Company Alpha / Company Beta', {'aliases': aliases}))

    def test_flags_and_input_remain_unchanged(self):
        entry = record('Armani', blocked=True)
        aliases = data(armani=entry)
        before = json.dumps(aliases)
        self.assertIs(resolve_alias_entry('Armani México', aliases), entry)
        self.assertEqual(json.dumps(aliases), before)

    def test_normalized_key_collision_is_ambiguous(self):
        aliases = {'company  alpha': record('One'), 'company\talpha': record('Two')}
        self.assertIsNone(resolve_alias_entry('COMPANY ALPHA', {'aliases': aliases}))

    def test_every_published_alias_keeps_exact_result(self):
        aliases = json.loads((ROOT / 'config/alias_map.json').read_text())
        for alias, entry in aliases['aliases'].items():
            with self.subTest(alias=alias):
                self.assertEqual(resolve_alias_entry(alias, aliases), entry)

    def test_profile_fit_wrapper_uses_shared_resolver(self):
        _alias_data.cache_clear()
        self.assertEqual(resolve_alias_flags('Armani México'), (True, 'Armani'))
        self.assertEqual(resolve_alias_flags('administradora de inmuebles'), (False, None))
        self.assertEqual(resolve_alias_flags('   '), (False, None))

    def test_feed_processor_wrapper_without_notion_imports(self):
        # Execute the unchanged wrapper AST, avoiding Notion/env initialization.
        tree = ast.parse((ROOT / 'scripts/feed_processor.py').read_text())
        node = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'resolve_alias')
        namespace = {'resolve_alias_entry': resolve_alias_entry}
        exec(compile(ast.Module(body=[node], type_ignores=[]), 'feed_processor.py', 'exec'), namespace)
        resolve = namespace['resolve_alias']
        self.assertEqual(resolve('Armani México', data(armani=record('Armani', "L'Oréal", True))), ('Armani', "L'Oréal", True))
        self.assertEqual(resolve('administradora', data(adm=record('ADM'))), (None, None, None))


if __name__ == '__main__':
    unittest.main()
