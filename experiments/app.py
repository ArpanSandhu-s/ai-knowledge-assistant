import streamlit as st
import concurrent.futures

from core.rag import create_vector_db

from core.agents import (
    rag_agent,
    summary_agent,
    quiz_agent,
    keypoints_agent
)

st.set_page_config(page_title="Multi-Agent PDF Assistant")

st.title("Chapter 5 Multi-Agent PDF Assistant")

pdf = st.file_uploader(
    "Upload PDF",
    type="pdf"
)

if pdf:

    with open(pdf.name, "wb") as f:
        f.write(pdf.getbuffer())

    st.success("PDF Uploaded")

    question = st.text_input(
        "Ask a question"
    )

    pattern = st.selectbox(
        "Choose Pattern",
        ["Sequential", "Concurrent"]
    )

    if st.button("Run"):

        try:

            st.write("Creating vector database...")

            db = create_vector_db(pdf.name)

            st.write("Searching document...")

            docs = db.similarity_search(
                question,
                k=3
            )

            context = "\n".join(
                [doc.page_content for doc in docs]
            )

            st.write("Running agents...")

            answer = rag_agent(
                context,
                question
            )

            if pattern == "Sequential":

                summary = summary_agent(answer)

                quiz = quiz_agent(summary)

                st.subheader("Answer")
                st.write(answer)

                st.subheader("Summary")
                st.write(summary)

                st.subheader("Quiz")
                st.write(quiz)

            else:

                with concurrent.futures.ThreadPoolExecutor() as executor:

                    future_summary = executor.submit(
                        summary_agent,
                        answer
                    )

                    future_quiz = executor.submit(
                        quiz_agent,
                        answer
                    )

                    future_keypoints = executor.submit(
                        keypoints_agent,
                        answer
                    )

                    summary = future_summary.result()
                    quiz = future_quiz.result()
                    keypoints = future_keypoints.result()

                st.subheader("Answer")
                st.write(answer)

                st.subheader("Summary")
                st.write(summary)

                st.subheader("Quiz")
                st.write(quiz)

                st.subheader("Key Points")
                st.write(keypoints)

        except Exception as e:

            st.error(str(e))