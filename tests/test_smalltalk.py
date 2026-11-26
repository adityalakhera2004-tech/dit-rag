from smalltalk import small_talk_reply


def test_greeting_gets_reply():
    assert small_talk_reply("hello") is not None
    assert small_talk_reply("Hello!!") is not None       # punctuation ignored
    assert small_talk_reply("  Good Morning  ") is not None


def test_thanks_gets_reply():
    assert small_talk_reply("thank you") is not None


def test_real_question_is_not_small_talk():
    assert small_talk_reply("Hello, what is a lexeme?") is None
    assert small_talk_reply("What is a translator?") is None