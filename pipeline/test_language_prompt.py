import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


PIPELINE = Path(__file__).parent
POWERSHELL = shutil.which("pwsh") or shutil.which("powershell")


@unittest.skipUnless(POWERSHELL, "PowerShell is required for pipeline tests")
class LanguagePromptTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.pipeline = self.root / "pipeline"
        self.pipeline.mkdir()
        shutil.copyfile(PIPELINE / "run-meetings.ps1", self.pipeline / "run-meetings.ps1")
        transcriber = (PIPELINE / "diarize-meetings.ps1").read_text(encoding="utf-8")
        self.assertIn(".venv\\Scripts\\whisperx.exe", transcriber)
        (self.pipeline / "diarize-meetings.ps1").write_text(
            transcriber.replace(".venv\\Scripts\\whisperx.exe", "test-whisperx.ps1"),
            encoding="utf-8",
        )
        (self.pipeline / "convert-meetings.ps1").write_text(
            "'converted' | Set-Content (Join-Path $PSScriptRoot 'conversion.txt')",
            encoding="utf-8",
        )
        (self.pipeline / "test-whisperx.ps1").write_text(
            "$args | ConvertTo-Json | Set-Content (Join-Path $PSScriptRoot 'arguments.json')\n"
            "$global:LASTEXITCODE = 0\n",
            encoding="utf-8",
        )
        (self.root / ".env").write_text("HF_TOKEN=test-token\n", encoding="utf-8")
        audio = self.root / "output" / ".audio"
        audio.mkdir(parents=True)
        (audio / "meeting.wav").touch()

    def run_script(self, parameters="", answers=(), script="run-meetings.ps1"):
        answer_json = json.dumps(list(answers))
        driver = self.pipeline / "test-driver.ps1"
        driver.write_text(
            "$ErrorActionPreference = 'Stop'\n"
            f"$global:answers = @('{answer_json}' | ConvertFrom-Json)\n"
            "$global:promptCount = 0\n"
            "function global:Read-Host {\n"
            "    param([string] $Prompt)\n"
            "    if ($global:promptCount -ge $global:answers.Count) {\n"
            "        throw 'Unexpected language prompt'\n"
            "    }\n"
            "    $answer = $global:answers[$global:promptCount]\n"
            "    $global:promptCount++\n"
            "    return $answer\n"
            "}\n"
            f"& (Join-Path $PSScriptRoot '{script}') {parameters}\n"
            "$global:promptCount | Set-Content (Join-Path $PSScriptRoot 'prompts.txt')\n",
            encoding="utf-8",
        )
        return subprocess.run(
            [POWERSHELL, "-NoProfile", "-NonInteractive", "-File", str(driver)],
            capture_output=True,
            text=True,
            timeout=30,
        )

    def assert_language(self, language, prompts):
        arguments = json.loads(
            (self.pipeline / "arguments.json").read_text(encoding="utf-8-sig")
        )
        self.assertEqual(arguments[arguments.index("--language") + 1], language)
        self.assertEqual(
            int((self.pipeline / "prompts.txt").read_text(encoding="utf-8-sig")),
            prompts,
        )

    def test_prompted_language_reaches_whisperx(self):
        result = self.run_script("-OutputFormat json", answers=[" EN "])
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assert_language("en", 1)

    def test_empty_and_malformed_answers_prompt_again(self):
        result = self.run_script("-OutputFormat json", answers=[" ", "English", "de"])
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assert_language("de", 3)

    def test_explicit_language_skips_prompt_and_preserves_other_arguments(self):
        result = self.run_script("-Language DA -OutputFormat json -Model medium -BatchSize 2")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assert_language("da", 0)
        arguments = json.loads(
            (self.pipeline / "arguments.json").read_text(encoding="utf-8-sig")
        )
        self.assertEqual(arguments[arguments.index("--model") + 1], "medium")
        self.assertEqual(arguments[arguments.index("--batch_size") + 1], 2)

    def test_invalid_explicit_language_fails_before_conversion(self):
        for language in ("English", "''"):
            with self.subTest(language=language):
                result = self.run_script(f"-Language {language} -OutputFormat json")
                self.assertNotEqual(result.returncode, 0)
                self.assertFalse((self.pipeline / "conversion.txt").exists())

    def test_direct_transcriber_requires_language(self):
        result = self.run_script("-OutputFormat json", script="diarize-meetings.ps1")
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse((self.pipeline / "arguments.json").exists())

    def test_direct_transcriber_forwards_explicit_language(self):
        result = self.run_script(
            "-Language EN -OutputFormat json", script="diarize-meetings.ps1"
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assert_language("en", 0)

    def test_whatif_does_not_run_whisperx(self):
        result = self.run_script("-WhatIf", answers=["en"])
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertFalse((self.pipeline / "arguments.json").exists())


if __name__ == "__main__":
    unittest.main()
