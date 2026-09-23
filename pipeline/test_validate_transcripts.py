import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).with_name("validate-transcripts.py")
SPEC = importlib.util.spec_from_file_location("validate_transcripts", MODULE_PATH)
assert SPEC and SPEC.loader
validator = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = validator
SPEC.loader.exec_module(validator)


class TranscriptValidationTests(unittest.TestCase):
    def test_parse_teams_markup_and_whisperx_speaker_prefixes(self):
        teams_vtt = """WEBVTT

cue-id
00:00:03.955 --> 00:00:05.000
<v A Person>Hej verden.</v>
"""
        whisperx_vtt = """WEBVTT

00:03.955 --> 00:05.000
[SPEAKER_02]: Hej verden!
"""
        with tempfile.TemporaryDirectory() as directory:
            directory_path = Path(directory)
            teams_path = directory_path / "teams.vtt"
            whisperx_path = directory_path / "whisperx.vtt"
            teams_path.write_text(teams_vtt, encoding="utf-8")
            whisperx_path.write_text(whisperx_vtt, encoding="utf-8")

            teams = validator.parse_vtt(teams_path)
            whisperx = validator.parse_vtt(whisperx_path)

        self.assertEqual(teams[0].start, whisperx[0].start)
        self.assertEqual(validator.normalize_tokens(teams[0].text), ["hej", "verden"])
        self.assertEqual(validator.normalize_tokens(whisperx[0].text), ["hej", "verden"])

    def test_edit_counts_identify_each_error_type(self):
        self.assertEqual(validator.edit_counts(["vej", "holder"], ["vej", "virker"]), (1, 0, 0, 1))
        self.assertEqual(validator.edit_counts(["vej", "holder"], ["vej"]), (0, 1, 0, 1))
        self.assertEqual(validator.edit_counts(["vej"], ["vej", "holder"]), (0, 0, 1, 1))


if __name__ == "__main__":
    unittest.main()