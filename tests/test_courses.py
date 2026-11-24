from courses import detect_course


def test_code_without_space():
    code, search_q, unknown = detect_course("What are the prerequisites for CSN441?")
    assert code == "CSN441"
    assert unknown is None


def test_code_with_space():
    code, _, _ = detect_course("What are the prerequisites for CSN 441?")
    assert code == "CSN441"


def test_lowercase_and_dash():
    assert detect_course("prerequisites for csn-441")[0] == "CSN441"


def test_code_is_replaced_in_search_question():
    _, search_q, _ = detect_course("What are the prerequisites for CSN 441?")
    assert "441" not in search_q
    assert search_q == "What are the prerequisites for this course?"


def test_unknown_course():
    code, _, unknown = detect_course("What is the syllabus of CSN999?")
    assert code is None
    assert unknown == "CSN999"


def test_course_name_detected():
    code, search_q, _ = detect_course("What is a lexeme in compiler design?")
    assert code == "CSN401"
    assert "compiler design" in search_q      # the name stays: it helps the embedding


def test_no_course():
    assert detect_course("What is a perceptron?") == (None, "What is a perceptron?", None)