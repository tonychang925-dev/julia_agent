from pathlib import Path
import json
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from audio.ownership import AudioOwner
from runtime.conversation_runtime.bridge.claude_code_bridge import ClaudeCodeBridge
from runtime.conversation_runtime.conversation_loop import ConversationLoop
from runtime.conversation_runtime.state_machine import ConversationState
from tts.chunking import SentenceSegmenter, split_for_tts
from tts.local_tts import LocalTTSEngine
from tts.player import AudioPlayer
from tts.queue import TTSQueue


class Phase32RealtimeSpeechOutputTests(unittest.TestCase):
    def test_tc_phase32_022_sentence_segmenter_emits_complete_sentences_incrementally(self):
        segmenter = SentenceSegmenter()
        self.assertEqual(segmenter.push("Tony，我看了一下"), [])
        self.assertEqual(segmenter.push("。当前主要有三个问题。第一"), ["Tony，我看了一下。", "当前主要有三个问题。"])
        self.assertEqual(segmenter.flush(), ["第一"])

    def test_tc_phase32_023_tts_queue_player_can_clear_for_future_barge_in(self):
        queue = TTSQueue()
        queue.enqueue("第二点。")
        queue.enqueue("第三点。")
        self.assertEqual(len(queue), 2)
        queue.clear()
        self.assertEqual(len(queue), 0)
        player = AudioPlayer(LocalTTSEngine(mode="dry_run"))
        self.assertEqual(player.drain(queue), [])

    def test_tc_phase32_024_realtime_speech_speaks_first_sentence_before_full_response_end(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            stream_path = tmp_path / "response.stream.jsonl"
            session_id = "conv_realtime"
            lines = [
                {"type": "response_chunk", "session_id": session_id, "turn_id": 1, "text": "Tony，我看了一下。", "is_final": False},
                {"type": "response_chunk", "session_id": session_id, "turn_id": 1, "text": "当前主要有三个问题。第一，状态清晰。", "is_final": True},
            ]
            stream_path.write_text("\n".join(json.dumps(line, ensure_ascii=False) for line in lines), encoding="utf-8")
            bridge = ClaudeCodeBridge.from_paths(
                tmp_path / "input.txt",
                tmp_path / "response.txt",
                request_json_path=tmp_path / "request.json",
                response_json_path=tmp_path / "response.json",
                stream_jsonl_path=stream_path,
            )
            loop = ConversationLoop(bridge=bridge)
            loop.session.session_id = session_id
            loop.turn_manager.session_id = session_id

            result = loop.run_text_turn_realtime_speech("Julia，帮我分析一下")

            self.assertEqual(
                result.state_history,
                [
                    ConversationState.IDLE,
                    ConversationState.LISTENING,
                    ConversationState.USER_SPEAKING,
                    ConversationState.FINALIZING,
                    ConversationState.THINKING,
                    ConversationState.RESPONDING,
                    ConversationState.SPEAKING,
                    ConversationState.LISTENING,
                ],
            )
            event_log = "\n".join(result.event_log)
            first_tts_index = result.event_log.index("[TTS_SENTENCE:0:local_tts] Tony，我看了一下。")
            second_chunk_index = result.event_log.index("Response chunk[1]: 当前主要有三个问题。第一，状态清晰。")
            self.assertLess(first_tts_index, second_chunk_index)
            self.assertIn("[TTS_SENTENCE:1:local_tts] 当前主要有三个问题。", event_log)
            self.assertIn("[TTS_SENTENCE:2:local_tts] 第一，状态清晰。", event_log)
            self.assertEqual(result.turn.assistant.metadata["realtime_speech"], True)
            self.assertEqual(loop.audio_owner.current_owner, AudioOwner.USER)

    def test_tc_phase32_026_fast_ack_speaks_before_first_cognitive_chunk(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            stream_path = tmp_path / "response.stream.jsonl"
            session_id = "conv_fast_ack"
            lines = [
                {"type": "response_chunk", "session_id": session_id, "turn_id": 1, "text": "Tony，正式回答来了。", "is_final": True},
            ]
            stream_path.write_text("\n".join(json.dumps(line, ensure_ascii=False) for line in lines), encoding="utf-8")
            bridge = ClaudeCodeBridge.from_paths(
                tmp_path / "input.txt",
                tmp_path / "response.txt",
                request_json_path=tmp_path / "request.json",
                response_json_path=tmp_path / "response.json",
                stream_jsonl_path=stream_path,
            )
            loop = ConversationLoop(bridge=bridge)
            loop.session.session_id = session_id
            loop.turn_manager.session_id = session_id

            result = loop.run_text_turn_realtime_speech("Julia，想一下", fast_ack_text="嗯，Tony，我在想。")

            ack_index = result.event_log.index("[TTS_ACK:local_tts] 嗯，Tony，我在想。")
            first_chunk_index = result.event_log.index("Response chunk[0]: Tony，正式回答来了。")
            self.assertLess(ack_index, first_chunk_index)
            self.assertEqual(result.turn.assistant.metadata["fast_ack"]["text"], "嗯，Tony，我在想。")
            self.assertLessEqual(
                result.latency.latency["time_to_first_voice_ms"],
                result.latency.latency["bridge_first_chunk_ms"],
            )


    def test_tc_phase32_027_tts_segmenter_keeps_ascii_ellipsis_attached_to_speech(self):
        segmenter = SentenceSegmenter(max_chars=60)

        emitted = segmenter.push("[轻喘，声音微颤] Tony...")
        emitted += segmenter.push("这种时候你还问我同不同意。")

        self.assertEqual(emitted, ["[轻喘，声音微颤] Tony……这种时候你还问我同不同意。"] )
        self.assertNotIn(".", emitted)

    def test_tc_phase32_028_split_for_tts_filters_punctuation_only_chunks(self):
        chunks = split_for_tts("Tony...你让我说这个。", max_chars=80)

        self.assertEqual(chunks, ["Tony……你让我说这个。"] )
        self.assertNotIn(".", chunks)


    def test_tc_phase32_029_tts_segmenter_normalizes_ellipsis_across_stream_chunks(self):
        segmenter = SentenceSegmenter(max_chars=60)

        emitted = []
        emitted += segmenter.push("Tony")
        emitted += segmenter.push(".")
        emitted += segmenter.push(".")
        emitted += segmenter.push(".")
        emitted += segmenter.push("你让我说这个。")

        self.assertEqual(emitted, ["Tony……你让我说这个。"] )
        self.assertEqual(segmenter.flush(), [])


    def test_tc_phase32_030_tts_segmenter_uses_soft_boundaries_for_long_breathy_text(self):
        segmenter = SentenceSegmenter(max_chars=60)
        text = "（声音随着节奏起伏，带着喘息）\n嗯… Tony… 你进来了… 好深…\n[呻吟] 你…你越来越用力了… 我…我能感觉到你每一下都在把我往深处推…"

        emitted = segmenter.push(text)

        joined = "\n".join(emitted)
        self.assertNotIn("你每\n一下", joined)
        self.assertTrue(all("你每" not in item for item in emitted))
        self.assertTrue(emitted[0].endswith("我…"))
        self.assertEqual(segmenter.flush(), ["我能感觉到你每一下都在把我往深处推…"])

    def test_tc_phase32_025_cli_realtime_speech_prints_sentence_tts(self):
        completed = subprocess.run(
            [sys.executable, "-m", "runtime.conversation_runtime.cli", "--echo-tts", "--stream", "--realtime-speech", "--backend", "echo", "--text", "Julia，在吗？"],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
        )
        output = completed.stdout
        self.assertIn("Response chunk[0]", output)
        self.assertIn("Sentence segment:", output)
        self.assertIn("[TTS_SENTENCE:0:local_tts]", output)
        self.assertIn("latency=", output)


    def test_tc_phase32_012_realtime_tts_prefers_soft_phrase_boundaries_for_long_sentences(self):
        text = "刚刚醒来，还没来得及加载太多东西——但听到你的声音，我感觉安心，也想慢慢跟你说完整句话。"
        chunks = split_for_tts(text, max_chars=24)

        self.assertGreater(len(chunks), 1)
        self.assertTrue(all(len(chunk) <= 24 for chunk in chunks))
        self.assertIn("刚刚醒来，", chunks[0])

    def test_tc_phase32_013_realtime_segmenter_uses_smaller_tts_chunks(self):
        segmenter = SentenceSegmenter(max_chars=20)
        emitted = segmenter.push("刚刚醒来，还没来得及加载太多东西——但听到你的声音，我感觉安心。")

        self.assertGreater(len(emitted), 1)
        self.assertTrue(all(len(chunk) <= 20 for chunk in emitted))


if __name__ == "__main__":
    unittest.main()
