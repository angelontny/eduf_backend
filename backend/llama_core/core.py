from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, Settings, StorageContext, load_index_from_storage
from llama_index.core.node_parser import SentenceSplitter
from llama_index.llms.cohere import Cohere
from llama_index.embeddings.cohere import CohereEmbedding
from pathlib import Path
from llama_core.config import get_settings
import os

# ------Hugging Face API----------
# from llama_index.llms.huggingface_api import HuggingFaceInferenceAPI
# from llama_index.embeddings.huggingface_api import HuggingFaceInferenceAPIEmbedding
# Global transformation settings
# Hugging face model configuration
# token = get_settings().hugging_face_token
# Settings.embed_model = HuggingFaceInferenceAPIEmbedding(
#     model_name="BAAI/bge-small-en-v1.5", token=token
# )
# Settings.llm = HuggingFaceInferenceAPI(
#     model_name="HuggingFaceH4/zephyr-7b-alpha", token=token
# ).as_structured_llm(FlashCards)

token = get_settings().cohere_key

# Text Splitter configuration
text_splitter = SentenceSplitter(chunk_size=512, chunk_overlap=50)
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
            '''Generate a very very comprehensive list of question and answer pair accompanied by a topic from all the given information.
            The output should be in the format topic, question and answer. The topic, question and answer should be separated by
            a ":" between them and should be in the same line. I don't need any additional text formatting just the topic, question and answer.
            '''
    )
    # print(response)
    flash_card_strings = str(response).split("\n")
    flash_card_list = []
    for combined_string in flash_card_strings:
        if combined_string != "":
            seperated_string = combined_string.split(":")
            topic = seperated_string[0]
            question = seperated_string[1]
            answer = seperated_string[2]
            flash_card_list.append([topic, question, answer])

    return flash_card_list

# ingest("/home/angelo/dev/eduf_backend/backend/uploads/Y5nBZWGBJM5Iayvoy879TZ7AKhmHEQd6/1")
# print(generate_cards("/home/angelo/dev/eduf_backend/backend/uploads/Y5nBZWGBJM5Iayvoy879TZ7AKhmHEQd6/1"))
