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

from debug import debug_cprint, enable_debug


EXEMPLAR_LIST = [
    "book-flight",
    "choose-date",
    "click-button-sequence",
    "click-button",
    "click-checkboxes-large",
    "click-checkboxes-soft",
    "click-collapsible-2",
    "click-collapsible",
    "click-color",
    "click-dialog-2",
    "click-dialog",
    "click-link",
    "click-menu",
    "click-pie",
    "click-scroll-list",
    "click-shades",
    "click-shape",
    "click-tab-2",
    "click-tab",
    "click-widget",
    "copy-paste-2",
    "count-shape",
    "email-inbox-nl-turk",
    "enter-date",
    "enter-password",
    "enter-text-dynamic",
    "enter-time",
    "find-word",
    "focus-text-2",
    "focus-text",
    "grid-coordinate",
    "guess-number",
    "identify-shape",
    "login-user-popup",
    "multi-layouts",
    "navigate-tree",
    "read-table",
    "search-engine",
    "simple-algebra",
    "social-media-all",
    "social-media-some",
    "social-media",
    "terminal",
    "text-transform",
    "tic-tac-toe",
    "use-autocomplete",
    "use-slider",
    "use-spinner",

    # CompWoB
    "click-button_click-dialog",
    "click-button_click-dialog-reverse",
    "click-checkboxes-soft_enter-password",
    "click-checkboxes-soft_enter-password-reverse",
    "click-link_click-dialog",
    "click-link_click-dialog-reverse",
    "enter-date_login-user",
    "enter-date_login-user-reverse",
    "login-user_navigate-tree",
    "login-user_navigate-tree-reverse",
    "multi-layouts_login-user",
    "multi-layouts_login-user-reverse",
    "enter-password_click-checkboxes_login-user-popup",
    "enter-password_click-checkboxes_login-user-popup-reverse",
    "use-autocomplete_click-dialog",
    "use-autocomplete_click-dialog-reverse",
    "click-button-sequence_use-autocomplete",
    "click-button-sequence_use-autocomplete-reverse",
    "click-checkboxes-soft_multi-layouts",
    "click-checkboxes-soft_multi-layouts-reverse",
    "click-dialog-2_click-widget",
    "click-dialog-2_click-widget-reverse",
    "click-dialog-2_login-user-popup",
    "click-dialog-2_login-user-popup-reverse",
    "click-dialog_search-engine",
    "click-dialog_search-engine-reverse",
    "click-link_enter-text",
    "click-link_enter-text-reverse",
    "click-option_enter-text",
    "click-option_enter-text-reverse",
    "click-checkboxes-transfer_enter-password_click-dialog",
    "click-checkboxes-transfer_enter-password_click-dialog-reverse",
]


def build_memory(memory_path: str):
    # enable_debug()

    debug_cprint(f"memory_path: {memory_path}", "white")
    with open(os.path.join(memory_path, "specifiers.json"), "r") as rf:
        specifier_dict = json.load(rf)
        exemplar_names = []
        specifiers = []
        for k, v in specifier_dict.items():
            assert k in EXEMPLAR_LIST
            for query in v:
                exemplar_names.append(k)
                specifiers.append(query)
    debug_cprint(f"len(list(set(exemplar_names))): {len(list(set(exemplar_names)))}", "white")
    debug_cprint(f"len(EXEMPLAR_LIST): {len(EXEMPLAR_LIST)}", "white")
    missing_elements = set(EXEMPLAR_LIST) - set(exemplar_names)
    debug_cprint(f"missing: {missing_elements}", "white")
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
    """
    FAISSからqueryに近い要素をtop_k取得し、最頻値のnameを返す
    """
    debug_cprint(f"memory retrieve_exemplar_name()", "white")
    retriever = memory.as_retriever(search_kwargs={"k": top_k})
    debug_cprint(f" retriever: {retriever}", "white")
    docs = retriever.get_relevant_documents(query)
    debug_cprint(f" docs: {docs}", "white")
    retrieved_exemplar_names = [doc.metadata["name"] for doc in docs]
    debug_cprint(f" retrieved_exemplar_names: {retrieved_exemplar_names}", "white")
    logger.info(f"Retrieved exemplars: {retrieved_exemplar_names}")
    data = Counter(retrieved_exemplar_names)
    debug_cprint(f" data: {data}", "white")
    retrieved_exemplar_name = data.most_common(1)[0][0]

    return retrieved_exemplar_name


def load_memory(memory_path):
    embedding = OpenAIEmbeddings(model="text-embedding-ada-002")
    memory = FAISS.load_local(memory_path, embedding)

    return memory
