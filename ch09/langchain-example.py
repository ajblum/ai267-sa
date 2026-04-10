from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# Initialize model
llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0
)

# Step 1: Rewrite the question
rewrite_prompt = ChatPromptTemplate.from_template(
    "Rewrite this question to be more clear and specific:\n\n{question}"
)
rewrite_chain = rewrite_prompt | llm | StrOutputParser()

# Step 2: Answer the improved question
answer_prompt = ChatPromptTemplate.from_template(
    "Answer this question clearly and concisely:\n\n{improved_question}"
)
answer_chain = answer_prompt | llm | StrOutputParser()

# Combine into a full chain
def full_chain(question: str):
    improved_question = rewrite_chain.invoke({"question": question})
    answer = answer_chain.invoke({"improved_question": improved_question})
    return {
        "original_question": question,
        "improved_question": improved_question,
        "answer": answer
    }

# Run it
if __name__ == "__main__":
    result = full_chain("how do i run a vm in openshift")

    print("Original:", result["original_question"])
    print("Improved:", result["improved_question"])
    print("Answer:", result["answer"])
