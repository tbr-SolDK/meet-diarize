import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).with_name("review-transcripts.py")
SPEC = importlib.util.spec_from_file_location("review_transcripts", MODULE_PATH)
assert SPEC and SPEC.loader
reviewer = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = reviewer
SPEC.loader.exec_module(reviewer)


class TranscriptReviewTests(unittest.TestCase):
    def test_review_links_recording_and_seeks_each_cue(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            transcript = root / "output" / "meeting.vtt"
            transcript.parent.mkdir()
            transcript.write_text(
                "WEBVTT\n\n00:00:03.955 --> 00:00:05.000\n[SPEAKER_01]: Hej <verden> & alle.\n\n"
                "00:00:06.000 --> 00:00:08.000\n[SPEAKER_02]: Næste sætning.\n",
                encoding="utf-8",
            )
            media = root / "input" / "meeting #1.mp4"
            media.parent.mkdir()
            media.touch()
            report = root / "output" / "meeting.review.html"

            reviewer.write_review(transcript, media, report)
            page = report.read_text(encoding="utf-8")

            self.assertIn('src="../input/meeting%20%231.mp4"', page)
            self.assertIn('data-seek="3.955"', page)
            self.assertIn('data-seek="6.0"', page)
            self.assertEqual(page.count('<tr data-start='), 2)
            self.assertIn('Hej &amp; alle.', page)
            self.assertIn("video.currentTime=Number(row.dataset.start)", page)


if __name__ == "__main__":
    unittest.main()