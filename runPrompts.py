import logging
import os
import shutil
import subprocess
import argparse

import torch
from flask import Flask, jsonify, request
from langchain.chains import RetrievalQA
from langchain.embeddings import HuggingFaceInstructEmbeddings

# from langchain.embeddings import HuggingFaceEmbeddings
from run_localGPT import load_model
from prompt_template_utils import get_prompt_template

# from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from langchain.vectorstores import Chroma
from werkzeug.utils import secure_filename

from constants import CHROMA_SETTINGS, EMBEDDING_MODEL_NAME, PERSIST_DIRECTORY, MODEL_ID, MODEL_BASENAME


DEVICE_TYPE = "cuda"
# if torch.backends.mps.is_available():
#     DEVICE_TYPE = "mps"
# elif torch.cuda.is_available():
#     DEVICE_TYPE = "cuda"
# else:
#     DEVICE_TYPE = "cpu"

SHOW_SOURCES = True
logging.info(f"Running on: {DEVICE_TYPE}")
logging.info(f"Display Source Documents set to: {SHOW_SOURCES}")

EMBEDDINGS = HuggingFaceInstructEmbeddings(model_name=EMBEDDING_MODEL_NAME, model_kwargs={"device": DEVICE_TYPE})

# uncomment the following line if you used HuggingFaceEmbeddings in the ingest.py
# EMBEDDINGS = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL_NAME)
# if os.path.exists(PERSIST_DIRECTORY):
#     try:
#         shutil.rmtree(PERSIST_DIRECTORY)
#     except OSError as e:
#         print(f"Error: {e.filename} - {e.strerror}.")
# else:
#     print("The directory does not exist")

# run_langest_commands = ["python", "ingest.py"]
# if DEVICE_TYPE == "cpu":
#     run_langest_commands.append("--device_type")
#     run_langest_commands.append(DEVICE_TYPE)

# result = subprocess.run(run_langest_commands, capture_output=True)
# if result.returncode != 0:
#     raise FileNotFoundError(
#         "No files were found inside SOURCE_DOCUMENTS, please put a starter file inside before starting the API!"
#     )

# load the vectorstore
DB = Chroma(
    persist_directory=PERSIST_DIRECTORY,
    embedding_function=EMBEDDINGS,
    client_settings=CHROMA_SETTINGS,
)

RETRIEVER = DB.as_retriever()

LLM = load_model(device_type=DEVICE_TYPE, model_id=MODEL_ID, model_basename=MODEL_BASENAME)
prompt, memory = get_prompt_template(promptTemplate_type="llama", history=False)

QA = RetrievalQA.from_chain_type(
    llm=LLM,
    chain_type="stuff",
    retriever=RETRIEVER,
    return_source_documents=SHOW_SOURCES,
    chain_type_kwargs={
        "prompt": prompt,
    },
)
user_prompt="How can I load a source code as documents, for a QA over code, spliting the code in classes and functions?"
res = QA(user_prompt)
answer, docs = res["result"], res["source_documents"]
print(answer)