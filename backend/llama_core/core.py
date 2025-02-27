from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, Settings, StorageContext, load_index_from_storage
from llama_index.core.node_parser import SentenceSplitter
from llama_index.embeddings.cohere import CohereEmbedding
from pathlib import Path
from llama_core.config import get_settings
import os
from llama_index.llms.groq import Groq
from llama_core.pydantic_model import FlashCards, QAS

# Tokens
cohere_token = get_settings().cohere_key
groq_token = get_settings().groq_key

text_splitter = SentenceSplitter(chunk_size=512, chunk_overlap=50)
Settings.text_splitter = text_splitter

def ingest(path: str):
    ''' Creates the index from the files contained in the folder '''

    Settings.embed_model = CohereEmbedding(
            cohere_api_key=cohere_token,
            model_name="embed-english-v3.0",
            input_type="search_document"
    )

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
    ''' Query files in the chat '''

    # Read from previously stored index
    persist_dir = Path(path) / "index"
    # rebuild storage context
    storage_context = StorageContext.from_defaults(persist_dir=str(persist_dir))

    Settings.llm = Groq(
            model="gemma2-9b-it",
            api_key=groq_token
    )
    # load index
    index = load_index_from_storage(storage_context)
    query_engine = index.as_query_engine()
    response = query_engine.query(question)
    return response

def generate_cards(path: str, nc: int):
    ''' Generate flash ards from the given list of files '''

    # Read from previously stored index
    persist_dir = Path(path) / "index"

    Settings.llm = Groq(
            model="gemma2-9b-it",
            api_key=groq_token
    ).as_structured_llm(FlashCards)

    # rebuild storage context
    storage_context = StorageContext.from_defaults(persist_dir=str(persist_dir))

    # load index
    index = load_index_from_storage(storage_context)
    query_engine = index.as_query_engine()
    response = query_engine.query(
            f'''
            Generate {nc} number of question and answer pairs.
            '''
            # '''Generate a very very comprehensive list of question and answer pair accompanied by a topic from all the given information.
            # The output should be in the format topic, question and answer. The question should come before the answer.
            # The topic, question and answer should be separated by a ":" between them and should be in the same line. I don't need any
            # additional text formatting just the topic, question and answer.
            # '''
    )

    # Error with the module, ide complains of an error
    return response.response.dict()["cards"]

def generate_quiz(path: str, nq: int):
    ''' Generate a quiz from the uploaded files '''

    # Read from previously stored index
    persist_dir = Path(path) / "index"

    # Need to change the llm as we're using Cohere for embeddings
    Settings.llm = Groq(
            model="gemma2-9b-it",
            api_key=groq_token
    ).as_structured_llm(QAS)



    # rebuild storage context
    storage_context = StorageContext.from_defaults(persist_dir=str(persist_dir))

    # load index
    index = load_index_from_storage(storage_context)
    query_engine = index.as_query_engine()
    response = query_engine.query(
            f'''
            Generate {nq} number of questions with answer.
            '''
            # '''Generate a very very comprehensive list of question and answer pair accompanied by a topic from all the given information.
            # The output should be in the format topic, question and answer. The question should come before the answer.
            # The topic, question and answer should be separated by a ":" between them and should be in the same line. I don't need any
            # additional text formatting just the topic, question and answer.
            # '''
    )

    # Same IDE error as above
    return response.response.dict()["qas"]
