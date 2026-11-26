import streamlit as st

from courses import COURSES
from rag import answer
from search import get_model

st.set_page_config(page_title="DIT Course Notes Q&A", page_icon="📚")


@st.cache_resource
def warm_up():
    """Load the embedding model once when the app starts, not on every question."""
    get_model()
    return True


warm_up()

# Chat history lives in session_state so it survives reruns
if "messages" not in st.session_state:
    st.session_state.messages = []

# ---------- Sidebar ----------
with st.sidebar:
    st.header("Settings")
    options = ["Auto-detect from question"] + [f"{code} – {name}" for code, name in COURSES.items()]
    choice = st.selectbox("Course", options)
    course = None if choice.startswith("Auto") else choice.split(" ")[0]

    st.markdown("**Try asking:**")
    st.markdown("- What is a lexeme?\n"
                "- What are the prerequisites for CSN 441?\n"
                "- What is the Hebbian learning rule?")

    if st.button("Clear chat"):
        st.session_state.messages = []

# ---------- Main page ----------
st.title("📚 DIT Course Notes Q&A")
st.caption("Answers come only from the course notes, with file and page citations.")


def show_details(result):
    """Show cited sources and small debug info under an answer."""
    cited = [s for s in result["sources"] if s["n"] in result["cited"]]
    if cited:
        with st.expander(f"Sources ({len(cited)})"):
            for s in cited:
                st.markdown(f"**[{s['n']}]** {s['label']}")
    if result["invalid_citations"]:
        st.warning(f"Some citations don't match a source: {result['invalid_citations']}")

    info = [f"course: {result['course'] or 'all'}"]
    if result["top_similarity"] is not None:
        info.append(f"top similarity: {result['top_similarity']}")
    if result["model"]:
        info.append(f"model: {result['model']}")
    st.caption(" · ".join(info))


# Redraw the whole conversation (the script reruns on every interaction)
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("result"):
            show_details(msg["result"])

# New question
if question := st.chat_input("Ask about your course notes..."):
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        with st.spinner("Searching your notes..."):
            try:
                result = answer(question, course)
                text = result["answer"]
            except RuntimeError:
                result = None
                text = "Sorry, the answer service is busy right now. Please try again in a minute."
        st.markdown(text)
        if result:
            show_details(result)

    st.session_state.messages.append({"role": "assistant", "content": text, "result": result})