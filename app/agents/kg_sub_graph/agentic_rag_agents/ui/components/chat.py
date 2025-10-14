import io
import zipfile
from typing import Any, Dict, List
from uuid import uuid4

import pandas as pd
import streamlit as st
from neo4j.exceptions import SessionExpired

from ...components.state import OutputState


def append_user_question(question: str) -> None:
    st.session_state.get("messages", []).append({"role": "user", "content": question})
    st.chat_message("user").markdown(question)


async def append_llm_response(question: str) -> None:
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        message_placeholder.status("thinking...")
        print("question: ", question)

        agent = st.session_state.get("agent")

        if agent is not None:
            response: OutputState = await agent.ainvoke({"question": question})

            message_placeholder.markdown(response.get("answer", ""))

            show_visualizations(response=response)
            show_cypher_response_information(response=response)

    st.session_state.get("messages", []).append(
        {"role": "assistant", "content": response}
    )


def show_cypher_response_information(response: OutputState) -> None:
    if response.get("cyphers") and len(response.get("cyphers", list())) > 0:
        # a list of record lists
        records_lists: List[List[Dict[str, Any]]] = [
            c.get("records", list())
            for c in response.get("cyphers", list())
            if c.get("records") is not None
        ]

        download_csv_button(cypher_results=records_lists)

        with st.expander("Cypher"):
            [
                (
                    st.write(c.get("task", "")),
                    st.code(c.get("statement"), language="cypher"),
                    st.json(
                        c.get("records") if c.get("records") is not None else "",
                        expanded=False,
                    ),
                )
                for c in response.get("cyphers", list())
            ]


def show_visualizations(response: OutputState) -> None:
    if (
        response.get("visualizations")
        and len(response.get("visualizations", list())) > 0
    ):
        with st.expander("Visuals", expanded=True):
            [
                (
                    st.write(c.get("task", "")),
                    st.write(c.get("chart_description", "")),
                    st.pyplot(c.get("chart"), clear_figure=False),
                )
                for c in response.get("visualizations", list())
            ]


async def chat(question: str) -> None:
    try:
        append_user_question(question=question)
        await append_llm_response(question=question)
    except SessionExpired as e:
        st.error(f"Neo4j Session expired. Please restart the application. Error: {e}")


def display_chat_history() -> None:
    for message in st.session_state.get("messages", []):
        with st.chat_message(message["role"]):
            if message.get("role") == "user":
                st.markdown(message.get("content"))
            else:
                st.markdown(message.get("content", dict()).get("answer"))
                show_visualizations(response=message["content"])
                show_cypher_response_information(response=message["content"])


def prepare_csv(cypher_result: List[Dict[str, Any]]) -> Any:
    index = [i for i in range(len(cypher_result[0].values()))]
    return pd.DataFrame(data=cypher_result).to_csv(index=index).encode("utf-8")


@st.fragment  # type: ignore[misc, unused-ignore]
def download_csv_button(cypher_results: List[List[Dict[str, Any]]]) -> None:
    try:
        if len(cypher_results) > 1:
            content = [prepare_csv(result) for result in cypher_results if result]
            buf = io.BytesIO()
            with zipfile.ZipFile(buf, "x") as zip:
                for file_num, csv in enumerate(content):
                    zip.writestr(f"cypher_result_part_{str(file_num + 1)}.csv", csv)

            st.download_button(
                label="Download Cypher Results Tables as CSV",
                data=buf.getvalue(),
                file_name="cypher_results.zip",
                mime="application/zip",
                help="The cypher results .csv files in a .zip.",
                key=str(uuid4()),
            )
        elif len(cypher_results) == 1:
            csv = prepare_csv(cypher_result=cypher_results[0])
            st.download_button(
                label="Download Cypher Results Table as CSV",
                data=csv,
                file_name="cypher_results.csv",
                mime="text/csv",
                help="The cypher results .csv file.",
                key=str(uuid4()),
            )
    except Exception as e:
        print(
            f"Unable to generate Download Button for most recent question. Error: {e}"
        )
