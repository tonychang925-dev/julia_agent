import unittest

from runtime.conversation_runtime.cli import is_voice_exit_command


class RealVoiceManualExitCLITests(unittest.TestCase):
    def test_voice_exit_command_matches_exact_chinese_command_with_punctuation(self):
        self.assertTrue(is_voice_exit_command("退出。", "退出,结束,再见"))
        self.assertTrue(is_voice_exit_command("再见！", "退出,结束,再见"))

    def test_voice_exit_command_does_not_match_embedded_phrase(self):
        self.assertFalse(is_voice_exit_command("不要退出。", "退出,结束,再见"))
        self.assertFalse(is_voice_exit_command("我们继续，不要结束。", "退出,结束,再见"))


if __name__ == "__main__":
    unittest.main()
