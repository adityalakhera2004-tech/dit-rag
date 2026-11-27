from followup import is_follow_up


def test_clear_follow_ups():
    assert is_follow_up("give me an example")
    assert is_follow_up("explain it in simple words")
    assert is_follow_up("what about the interpreter?")
    assert is_follow_up("tell me more")
    assert is_follow_up("Can you elaborate?")


def test_new_questions_are_not_follow_ups():
    assert not is_follow_up("What is a perceptron?")
    assert not is_follow_up("What is the Hebbian learning rule?")
    assert not is_follow_up("What are the prerequisites for this course?")


def test_empty_question():
    assert not is_follow_up("")
    