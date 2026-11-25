import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
QML_DIR = ROOT / "plasmoid" / "contents" / "ui"
PO_DIR = ROOT / "po"

STRING = r'"((?:[^"\\]|\\.)*)"'
I18N_CALL = re.compile(r'\bi18n\(\s*' + STRING + r'|\bi18nc\(\s*' + STRING + r'\s*,\s*' + STRING)
PLACEHOLDER = re.compile(r"%\d")


def qml_messages():
    messages = set()
    for path in QML_DIR.glob("*.qml"):
        for plain, context, text in I18N_CALL.findall(path.read_text()):
            messages.add((None, plain) if plain else (context, text))
    return messages


def po_entries(path):
    entries = {}
    context = None
    msgid = None
    for line in path.read_text().splitlines():
        match = re.match(r'(msgctxt|msgid|msgstr) ' + STRING + r'$', line)
        if not match:
            continue
        keyword, value = match.groups()
        if keyword == "msgctxt":
            context = value
        elif keyword == "msgid":
            msgid = value
        elif msgid:
            entries[(context, msgid)] = value
            context = None
    return entries


class TranslationsTest(unittest.TestCase):
    def test_catalogs_match_the_widget(self):
        expected = qml_messages()
        self.assertTrue(expected)
        for po in PO_DIR.glob("*.po"):
            with self.subTest(po=po.name):
                entries = po_entries(po)
                self.assertEqual(set(entries), expected)
                for (_, msgid), msgstr in entries.items():
                    self.assertTrue(msgstr, msgid)
                    self.assertEqual(sorted(PLACEHOLDER.findall(msgstr)), sorted(PLACEHOLDER.findall(msgid)), msgid)


if __name__ == "__main__":
    unittest.main()
