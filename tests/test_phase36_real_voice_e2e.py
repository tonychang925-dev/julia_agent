from pathlib import Path
import os
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class Phase36RealVoiceE2ETests(unittest.TestCase):
    def make_fake_stt(self, tmp_path: Path, text: str = "Julia，在吗？", exit_code: int = 0) -> Path:
        stt = tmp_path / "fake_stt"
        stt.write_text(f"#!/usr/bin/env bash\necho '{text}'\nexit {exit_code}\n", encoding="utf-8")
        stt.chmod(0o755)
        return stt

    def make_sequence_stt(self, tmp_path: Path, outputs: list[str]) -> Path:
        stt = tmp_path / "fake_stt_sequence"
        state = tmp_path / "fake_stt_sequence.count"
        lines = [
            "#!/usr/bin/env python3",
            "from pathlib import Path",
            f"state=Path({str(state)!r})",
            f"outputs={outputs!r}",
            "i=int(state.read_text()) if state.exists() else 0",
            "state.write_text(str(i+1))",
            "print(outputs[i] if i < len(outputs) else outputs[-1])",
        ]
        stt.write_text("\n".join(lines) + "\n", encoding="utf-8")
        stt.chmod(0o755)
        return stt

    def test_tc_phase36_001_real_voice_cli_uses_speech_lab_stt_then_conversation_loop(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            fake_stt = self.make_fake_stt(tmp_path, "Julia，在吗？")
            env = dict(os.environ)
            env["ELEVENLABS_API_KEY"] = "test-key"
            completed = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "runtime.conversation_runtime.cli",
                    "--real-voice",
                    "--real-voice-turns",
                    "1",
                    "--backend",
                    "echo",
                    "--stream",
                    "--realtime-speech",
                    "--speech-lab-root",
                    str(tmp_path),
                    "--stt-bin",
                    str(fake_stt),
                    "--trace",
                ],
                cwd=ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env,
                check=True,
            )

            output = completed.stdout
            self.assertIn("[VOICE] 请开始说话", output)
            self.assertIn("text=Julia，在吗？", output)
            self.assertIn("state=THINKING", output)
            self.assertIn("[TTS_SENTENCE:0:local_tts]", output)
            self.assertIn("'backend': 'echo_adapter'", output)

    def test_tc_phase36_002_real_voice_cli_reports_stt_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            fake_stt = tmp_path / "fake_stt_fail"
            fake_stt.write_text("#!/usr/bin/env bash\necho '[FATAL] 语音识别未授权' >&2\nexit 1\n", encoding="utf-8")
            fake_stt.chmod(0o755)
            completed = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "runtime.conversation_runtime.cli",
                    "--real-voice",
                    "--real-voice-turns",
                    "1",
                    "--backend",
                    "echo",
                    "--speech-lab-root",
                    str(tmp_path),
                    "--stt-bin",
                    str(fake_stt),
                ],
                cwd=ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True,
            )

            self.assertIn("state=ERROR", completed.stdout)
            self.assertIn("Speech Recognition permission", completed.stdout)

    def test_tc_phase36_003_real_voice_cli_can_use_elevenlabs_conversation_tts(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            fake_stt = self.make_fake_stt(tmp_path, "Julia，在吗？")
            fake_tts = tmp_path / "fake_el_speak.py"
            fake_tts.write_text(
                "#!/usr/bin/env python3\nimport sys\nprint('[FAKE_TTS] ' + sys.argv[1])\n",
                encoding="utf-8",
            )
            fake_tts.chmod(0o755)
            env = dict(os.environ)
            env["ELEVENLABS_API_KEY"] = "test-key"
            completed = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "runtime.conversation_runtime.cli",
                    "--real-voice",
                    "--real-voice-turns",
                    "1",
                    "--backend",
                    "echo",
                    "--stream",
                    "--realtime-speech",
                    "--conversation-tts-engine",
                    "elevenlabs-script",
                    "--elevenlabs-script",
                    str(fake_tts),
                    "--tts-timeout",
                    "5",
                    "--speech-lab-root",
                    str(tmp_path),
                    "--stt-bin",
                    str(fake_stt),
                    "--trace",
                ],
                cwd=ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env,
                check=True,
            )

            output = completed.stdout
            self.assertIn("text=Julia，在吗？", output)
            self.assertIn("[TTS_SENTENCE:0:elevenlabs_script]", output)
            self.assertIn("'tts': 'elevenlabs_script'", output)

    def test_tc_phase36_004_real_voice_normalizes_julia_wake_word_mishearing(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            fake_stt = self.make_fake_stt(tmp_path, "兄弟你在吗")
            completed = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "runtime.conversation_runtime.cli",
                    "--real-voice",
                    "--real-voice-turns",
                    "1",
                    "--backend",
                    "echo",
                    "--stream",
                    "--realtime-speech",
                    "--speech-lab-root",
                    "/Users/admin/Desktop/speech_lab",
                    "--stt-bin",
                    str(fake_stt),
                ],
                cwd=ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True,
            )

            self.assertIn("text=Julia你在吗。", completed.stdout)
            self.assertNotIn("text=兄弟你在吗", completed.stdout)

    def test_tc_phase36_005_julia_wake_word_aliases_normalize_to_julia(self):
        from stt.speech_lab_stt import SpeechLabSTT, SpeechLabSTTConfig

        stt = SpeechLabSTT(SpeechLabSTTConfig(speech_lab_root=Path("/Users/admin/Desktop/speech_lab")))
        cases = {
            "朱莉亚你在吗": "Julia你在吗。",
            "朱丽娅你在吗": "Julia你在吗。",
            "茱莉娅你在吗": "Julia你在吗。",
            "助理呀你在吗": "Julia你在吗。",
            "兄弟你在吗": "Julia你在吗。",
            "你好兄弟你在吗": "你好Julia你在吗。",
        }
        for raw, expected in cases.items():
            with self.subTest(raw=raw):
                self.assertEqual(stt._normalize_text(raw), expected)

    def test_tc_phase36_006_wake_word_calibration_cli_saves_supervised_samples(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            fake_stt = self.make_fake_stt(tmp_path, "对呀你在吗")
            calibration = tmp_path / "wake_word_calibration.jsonl"
            completed = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "runtime.conversation_runtime.cli",
                    "--calibrate-wake-word",
                    "1",
                    "--speech-lab-root",
                    "/Users/admin/Desktop/speech_lab",
                    "--stt-bin",
                    str(fake_stt),
                    "--wake-word-training-text",
                    "Julia你在吗。",
                    "--wake-word-calibration",
                    str(calibration),
                ],
                cwd=ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True,
            )

            self.assertTrue(calibration.exists())
            content = calibration.read_text(encoding="utf-8")
            self.assertIn("对呀你在吗", content)
            self.assertIn("Julia你在吗。", content)
            self.assertIn('"training_text": "Julia你在吗。"', content)
            self.assertIn('"accepted": true', content)
            self.assertIn("accepted=True", completed.stdout)
            self.assertIn("[CALIBRATE] saved=", completed.stdout)

    def test_tc_phase36_007_wake_word_calibration_alias_corrector_applies_persisted_alias(self):
        from stt.speech_lab_stt import SpeechLabSTT, SpeechLabSTTConfig
        from stt.wake_word_calibration import WakeWordCalibrationStore, WakeWordSample

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            calibration = tmp_path / "wake_word_calibration.jsonl"
            store = WakeWordCalibrationStore(calibration)
            store.append(WakeWordSample(raw_text="猪呀你在吗", normalized_text="Julia你在吗。"))
            stt = SpeechLabSTT(
                SpeechLabSTTConfig(
                    speech_lab_root=Path("/Users/admin/Desktop/speech_lab"),
                    calibration_path=calibration,
                )
            )

            self.assertEqual(stt._normalize_text("猪呀你在吗"), "Julia你在吗。")

    def test_tc_phase36_008_repairs_incomplete_julia_wake_query(self):
        from stt.speech_lab_stt import SpeechLabSTT, SpeechLabSTTConfig

        stt = SpeechLabSTT(SpeechLabSTTConfig(speech_lab_root=Path("/Users/admin/Desktop/speech_lab")))
        self.assertEqual(stt._normalize_text("Julia你。"), "Julia你在吗？")
        self.assertEqual(stt._normalize_text("Julia你"), "Julia你在吗？")
        self.assertEqual(stt._normalize_text("Julia在。"), "Julia你在吗？")

    def test_tc_phase36_009_training_learns_english_julia_homophone_without_hardcoding(self):
        from stt.speech_lab_stt import SpeechLabSTT, SpeechLabSTTConfig
        from stt.wake_word_calibration import WakeWordCalibrationStore, WakeWordSample

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            calibration = tmp_path / "wake_word_calibration.jsonl"
            store = WakeWordCalibrationStore(calibration)
            store.append(WakeWordSample(raw_text="对呀你在吗", normalized_text="Julia你在吗。"))
            stt = SpeechLabSTT(
                SpeechLabSTTConfig(
                    speech_lab_root=Path("/Users/admin/Desktop/speech_lab"),
                    calibration_path=calibration,
                )
            )

            self.assertEqual(stt._normalize_text("对呀你在吗"), "Julia你在吗。")


    def test_tc_phase36_010_training_rejects_unlearnable_bad_captures(self):
        from stt.wake_word_calibration import WakeWordCalibrationStore

        self.assertFalse(WakeWordCalibrationStore.is_trainable_sample("嗯", "Julia你在吗。"))
        self.assertFalse(WakeWordCalibrationStore.is_trainable_sample("你在吗", "Julia你在吗。"))
        self.assertFalse(WakeWordCalibrationStore.is_trainable_sample("你在哪", "Julia你在吗。"))
        self.assertTrue(WakeWordCalibrationStore.is_trainable_sample("对啊你在吗", "Julia你在吗。"))

    def test_tc_phase36_011_training_generalizes_wake_query_template(self):
        from stt.speech_lab_stt import SpeechLabSTT, SpeechLabSTTConfig
        from stt.wake_word_calibration import WakeWordCalibrationStore, WakeWordSample

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            calibration = tmp_path / "wake_word_calibration.jsonl"
            store = WakeWordCalibrationStore(calibration)
            store.append(WakeWordSample(raw_text="对啊你在吗", normalized_text="Julia你在吗。"))
            store.append(WakeWordSample(raw_text="姐你在吗", normalized_text="Julia你在吗。"))
            store.append(WakeWordSample(raw_text="嗯", normalized_text="Julia你在吗。", accepted=False))
            stt = SpeechLabSTT(
                SpeechLabSTTConfig(
                    speech_lab_root=Path("/Users/admin/Desktop/speech_lab"),
                    calibration_path=calibration,
                )
            )

            self.assertEqual(stt._normalize_text("助力呀你在吗"), "Julia你在吗。")
            self.assertEqual(stt._normalize_text("助力呀你在吗。"), "Julia你在吗。")


    def test_tc_phase36_012_training_recovers_dropped_wake_word_for_learned_suffix(self):
        from stt.speech_lab_stt import SpeechLabSTT, SpeechLabSTTConfig
        from stt.wake_word_calibration import WakeWordCalibrationStore, WakeWordSample

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            calibration = tmp_path / "wake_word_calibration.jsonl"
            store = WakeWordCalibrationStore(calibration)
            store.append(WakeWordSample(raw_text="对啊你在吗", normalized_text="Julia你在吗。"))
            store.append(WakeWordSample(raw_text="姐你在吗", normalized_text="Julia你在吗。"))
            stt = SpeechLabSTT(
                SpeechLabSTTConfig(
                    speech_lab_root=Path("/Users/admin/Desktop/speech_lab"),
                    calibration_path=calibration,
                )
            )

            self.assertEqual(stt._normalize_text("你在吗。"), "Julia你在吗。")

    def test_tc_phase36_013_real_voice_retries_empty_capture_once(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            fake_stt = self.make_sequence_stt(tmp_path, ["", "Julia，在吗？"])
            completed = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "runtime.conversation_runtime.cli",
                    "--real-voice",
                    "--real-voice-turns",
                    "1",
                    "--backend",
                    "echo",
                    "--stream",
                    "--realtime-speech",
                    "--speech-lab-root",
                    str(tmp_path),
                    "--stt-bin",
                    str(fake_stt),
                    "--stt-retries",
                    "1",
                ],
                cwd=ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True,
            )

            self.assertIn("[STT_RETRY] empty capture; retry 1/1", completed.stdout)
            self.assertIn("text=Julia，在吗？", completed.stdout)
            self.assertIn("state=THINKING", completed.stdout)

    def test_tc_phase36_014_real_voice_can_run_multiple_turns_in_one_session(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            fake_stt = self.make_sequence_stt(tmp_path, ["Julia，在吗？", "今天怎么样？"])
            completed = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "runtime.conversation_runtime.cli",
                    "--real-voice",
                    "--real-voice-turns",
                    "2",
                    "--backend",
                    "echo",
                    "--stream",
                    "--realtime-speech",
                    "--speech-lab-root",
                    str(tmp_path),
                    "--stt-bin",
                    str(fake_stt),
                    "--trace",
                ],
                cwd=ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True,
            )

            output = completed.stdout
            self.assertIn("[VOICE_TURN] 1/2", output)
            self.assertIn("[VOICE_TURN] 2/2", output)
            self.assertIn("text=Julia，在吗？", output)
            self.assertIn("text=今天怎么样？", output)
            self.assertGreaterEqual(output.count("state=LISTENING"), 3)
            self.assertEqual(output.count("trace="), 2)


    def test_tc_phase36_015_repairs_narrow_huang_hua_confusion(self):
        from stt.speech_lab_stt import SpeechLabSTT, SpeechLabSTTConfig

        stt = SpeechLabSTT(SpeechLabSTTConfig(speech_lab_root=Path("/Users/admin/Desktop/speech_lab")))
        self.assertEqual(stt._normalize_text("为什么不那么花。"), "为什么不那么慌。")

    def test_tc_phase36_016_multi_turn_voice_session_continues_after_empty_capture(self):
        # TC-PHASE36-016: empty STT capture is a recoverable listening miss in
        # multi-turn birth tests, not a hard Runtime error.
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            fake_stt = self.make_sequence_stt(tmp_path, ["", "", "Julia，在吗？", "今天有点累。"])
            completed = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "runtime.conversation_runtime.cli",
                    "--real-voice",
                    "--real-voice-turns",
                    "2",
                    "--backend",
                    "echo",
                    "--stream",
                    "--realtime-speech",
                    "--speech-lab-root",
                    str(tmp_path),
                    "--stt-bin",
                    str(fake_stt),
                    "--stt-retries",
                    "1",
                ],
                cwd=ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True,
            )

            output = completed.stdout
            self.assertIn("[STT_EMPTY] no speech captured for turn 1; empty_count=1/3; continuing to listen.", output)
            self.assertIn("[VOICE_TURN] 1/2", output)
            self.assertIn("[VOICE_TURN] 2/2", output)
            self.assertIn("text=Julia，在吗？", output)
            self.assertIn("text=今天有点累。", output)
            self.assertNotIn("state=ERROR", output)


if __name__ == "__main__":
    unittest.main()
