import argparse
import os

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

llm = ChatOpenAI(
    model="gpt-4.1-mini",
    temperature=0
)

rewrite_prompt = ChatPromptTemplate.from_template(
    "Rewrite this question to be more clear and specific:\n\n{question}"
)
rewrite_chain = rewrite_prompt | llm | StrOutputParser()

answer_prompt = ChatPromptTemplate.from_template(
    "Answer this question clearly and concisely:\n\n{improved_question}"
)
answer_chain = answer_prompt | llm | StrOutputParser()

def full_chain(question: str):
    improved_question = rewrite_chain.invoke({"question": question})
    answer = answer_chain.invoke({"improved_question": improved_question})
    return {
        "original_question": question,
        "improved_question": improved_question,
        "answer": answer,
    }

def main():
    parser = argparse.ArgumentParser(
        description="Rewrite a question and answer it with LangChain + ChatGPT."
    )
    parser.add_argument(
        "question",
        nargs="*",
        default=["what", "is", "ai"],
        help="The original question to rewrite and answer."
    )
    args = parser.parse_args()

    question = " ".join(args.question)
    result = full_chain(question)

    print("\n=== LangChain Demo ===")
    print("Original Question :", result["original_question"])
    print("Improved Question :", result["improved_question"])
    print("Answer            :", result["answer"])

if __name__ == "__main__":
    main()
