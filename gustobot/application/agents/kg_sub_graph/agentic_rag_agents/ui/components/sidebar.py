import streamlit as st


def sidebar() -> None:
    """
    The Streamlit app side bar.
    """

    st.sidebar.title("Example Questions")
    with st.sidebar.expander("Example Questions"):
        for ex in st.session_state.get("example_questions", []):
            if st.sidebar.button(label=ex, key=ex):
                st.session_state["current_question"] = ex

    st.sidebar.divider()
    if len(st.session_state.get("messages", list())) > 0:
        if st.sidebar.button("Reset Chat", type="primary"):
            st.session_state["messages"] = list()
            del st.session_state["current_question"]
