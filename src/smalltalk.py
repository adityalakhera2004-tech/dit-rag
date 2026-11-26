import re

GREETINGS = {"hi", "hii", "hello", "hey", "hey there", "hello there",
             "good morning", "good afternoon", "good evening", "namaste"}
THANKS = {"thanks", "thank you", "thank you so much", "thx", "ok", "okay",
          "cool", "great", "bye", "goodbye"}

GREETING_REPLY = ("Hi! I answer questions from your DIT course notes, with page citations. "
                  "Try: \"What is a lexeme?\" or \"What are the prerequisites for CSN 441?\"")
THANKS_REPLY = "You're welcome! Ask another question about your course notes whenever you like."


def small_talk_reply(question):
    """Return a friendly reply for pure greetings/thanks, else None."""
    text = re.sub(r"[^a-z ]", "", question.lower())   # drop punctuation: "Hello!!" → "hello"
    text = re.sub(r"\s+", " ", text).strip()
    if text in GREETINGS:
        return GREETING_REPLY
    if text in THANKS:
        return THANKS_REPLY
    return None