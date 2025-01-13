import logging
import json
import openai
import os
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.vectorstores import FAISS
from collections import Counter

logger = logging.getLogger(__name__)

# .envを環境変数に登録
from dotenv import load_dotenv
load_dotenv()


EXEMPLAR_LIST = [
    "click-option_enter-text",                      # compwob
    "click-option_enter-text-reverse",              # compwob
    "click-option_login-user",                      # compwob
    "click-option_login-user-reverse",              # compwob
    "click-option_login-user-transition",           # compwob
    "click-option_login-user-transition-reverse",   # compwob
    "click-button-test"  # add for testing
]


def build_memory(memory_path: str):
    # print(f"memory_path: {memory_path}")
    with open(os.path.join(memory_path, "specifiers.json"), "r") as rf:
        specifier_dict = json.load(rf)
        exemplar_names = []
        specifiers = []
        for k, v in specifier_dict.items():
            assert k in EXEMPLAR_LIST
            for query in v:
                exemplar_names.append(k)
                specifiers.append(query)
    # print(f"len(list(set(exemplar_names))): {len(list(set(exemplar_names)))}")
    # print(f"len(EXEMPLAR_LIST): {len(EXEMPLAR_LIST)}")
    # missing_elements = set(EXEMPLAR_LIST) - set(exemplar_names)
    # print(f"missing: {missing_elements}")
    assert sorted(list(set(exemplar_names))) == sorted(EXEMPLAR_LIST)

    # embed memory_keys into VectorDB
    logger.info("Initilizing memory")
    openai.api_key = os.environ["OPENAI_API_KEY"]
    embedding = OpenAIEmbeddings(model="text-embedding-ada-002")
    metadatas = [{"name": name} for name in exemplar_names]
    memory = FAISS.from_texts(
        texts=specifiers,
        embedding=embedding,
        metadatas=metadatas,
    )
    memory.save_local(memory_path)


def retrieve_exemplar_name(memory, query: str, top_k) -> str:
    print(f"memory retrieve_exemplar_name()")
    retriever = memory.as_retriever(search_kwargs={"k": top_k})
    print(f" retriever: {retriever}")
    docs = retriever.get_relevant_documents(query)
    print(f" docs: {docs}")
    retrieved_exemplar_names = [doc.metadata["name"] for doc in docs]
    print(f" retrieved_exemplar_names: {retrieved_exemplar_names}")
    logger.info(f"Retrieved exemplars: {retrieved_exemplar_names}")
    data = Counter(retrieved_exemplar_names)
    print(f" data: {data}")
    retrieved_exemplar_name = data.most_common(1)[0][0]

    return retrieved_exemplar_name


def load_memory(memory_path):
    embedding = OpenAIEmbeddings(model="text-embedding-ada-002")
    memory = FAISS.load_local(memory_path, embedding)

    return memory
