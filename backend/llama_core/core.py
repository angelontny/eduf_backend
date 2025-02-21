from cohere.types import tool
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, Settings, StorageContext, load_index_from_storage
from llama_index.core.node_parser import SentenceSplitter
from llama_index.llms.huggingface_api import HuggingFaceInferenceAPI
from llama_index.embeddings.huggingface_api import HuggingFaceInferenceAPIEmbedding
from llama_index.llms.cohere import Cohere
from llama_index.embeddings.cohere import CohereEmbedding
from pathlib import Path
from llama_core.config import get_settings
import os
from llama_core.pydantic_model import FlashCards

# Global transformation settings
# Hugging face model configuration
# token = get_settings().hugging_face_token
# Settings.embed_model = HuggingFaceInferenceAPIEmbedding(
#     model_name="BAAI/bge-small-en-v1.5", token=token
# )
token = get_settings().cohere_key
# Text Splitter configuration
text_splitter = SentenceSplitter(chunk_size=256, chunk_overlap=50)
Settings.text_splitter = text_splitter

Settings.embed_model = CohereEmbedding(
        cohere_api_key=token,
        model_name="embed-english-v3.0",
        input_type="search_document"
)


Settings.llm = Cohere(
    model="command-r",
    api_key=token,
    
)
# Settings.llm = HuggingFaceInferenceAPI(
#     model_name="HuggingFaceH4/zephyr-7b-alpha", token=token
# ).as_structured_llm(FlashCards)

def ingest(path: str):
    # Folder to persistently store the created index
    persist_dir = Path(path) / "index"
    files_dir = Path(path) / "files"
    os.makedirs(persist_dir, exist_ok=True)

    # Load the uploaded documents
    documents = SimpleDirectoryReader(files_dir).load_data()

    # Generate and store the index
    index = VectorStoreIndex.from_documents(
        documents,
        show_progress=True
    )
    index.storage_context.persist(persist_dir=persist_dir)

def query(path: str, question: str):
    # Read from previously stored index
    persist_dir = Path(path) / "index"

    # rebuild storage context
    storage_context = StorageContext.from_defaults(persist_dir=str(persist_dir))

    # load index
    index = load_index_from_storage(storage_context)
    query_engine = index.as_query_engine()
    response = query_engine.query(question)
    return response

def generate_cards(path: str):
    # Read from previously stored index
    persist_dir = Path(path) / "index"

    # rebuild storage context
    storage_context = StorageContext.from_defaults(persist_dir=str(persist_dir))

    # load index
    index = load_index_from_storage(storage_context)
    query_engine = index.as_query_engine()
    response = query_engine.query(
            '''Generate a comprehensive list of question and answer pair from the given information.
            Each question and answer pair should be accompanied by a topic. The output should be in the
            format topic, question and answer. The topic, question and answer should only have a ":" between them.
            I don't need any additional text formatting just the topic, question and answer. Return as many as possible
            without repeatition. Generate a minimum of 10 questions.'''
    )
    flash_card_strings = str(response).split("\n")
    flash_card_list = []
    for combined_string in flash_card_strings:
        if combined_string != "":
            topic = combined_string.split(":")[0]
            question = combined_string.split(":")[1].split("?")[0]
            answer = combined_string.split(":")[1].split("?")[1]
            flash_card_list.append([topic, question, answer])

    return flash_card_list
