import os
import logging
from langchain.chains import ConversationalRetrievalChain
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.memory import ConversationBufferMemory
from langchain_chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains import create_history_aware_retriever, create_retrieval_chain
from langchain_community.vectorstores import FAISS
from langchain_groq import ChatGroq
from langchain_huggingface import ChatHuggingFace, HuggingFaceEmbeddings, HuggingFaceEndpoint, HuggingFacePipeline
from langchain_google_genai import ChatGoogleGenerativeAI
from unstructured.partition.auto import partition
from flask_login import current_user
from flask import session, current_app
import PIL
import cv2

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Embeddings
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2", model_kwargs={'device': 'cpu'})

# Extracting text from uploaded file
def extract_text_from_file(file_path):    
    logging.info(f"Extracting text from file: {file_path}")
    elements = partition(filename=file_path)
    text = "\n\n".join([str(el) for el in elements])
    logging.info("Text extraction complete.")
    return text

# Function to handle conversation with the chatbot
def conversation_chat(query, chain, history):
    logging.info(f"Received query: {query}")
    result = chain.invoke({"input": query, "chat_history": history})
    
    answer = result.get("answer", "Maaf, saya tidak tahu jawabannya.")
    history.append(("human", query))
    history.append(("ai", answer))
    logging.info(f"Answer generated: {answer}")

    # Assuming result contains relevant document metadata, such as filenames
    if "context" in result and result["context"]:
        logging.info("Source documents retrieved.")
        return history, answer, result["context"]
    
    logging.warning("No source documents found.")
    return history, answer, None

# Function to create the conversational chain
def create_conversational_chain(vector_store):
    retriever = vector_store.as_retriever(
        search_type="similarity_score_threshold", 
        search_kwargs={"k": 1, 'score_threshold': 0.1}
    )

    # LLAMA GROQ initialization
    llm = ChatGroq(
        groq_api_key=os.getenv('GROQ_API_KEY'), 
        model_name='llama3-70b-8192'
    )

    # Contextualize question prompt (in Bahasa Indonesia)
    contextualize_q_system_prompt = (
        "Berdasarkan riwayat percakapan dan pertanyaan terbaru dari pengguna "
        "yang mungkin merujuk pada konteks dalam riwayat percakapan, "
        "formulasikan pertanyaan yang dapat dipahami tanpa perlu melihat riwayat percakapan. "
        "Jangan menjawab pertanyaan tersebut, hanya reformulasikan jika perlu, "
        "dan jika tidak perlu perubahan, kembalikan seperti semula."
    )

    contextualize_q_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", contextualize_q_system_prompt),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}")  # Replace {input} correctly to handle the user's query
        ]
    )

    # Create a history-aware retriever to contextualize the query based on chat history
    history_aware_retriever = create_history_aware_retriever(
        llm, retriever, contextualize_q_prompt
    )

    # Question-answering system prompt (GuideBot PT SPIL style)
    qa_system_prompt = (
        "Anda adalah GuideBot, asisten AI untuk PT. Salam Pacific Indonesia Lines. "
        "Gunakan potongan konteks berikut untuk menjawab pertanyaan. Jika Anda tidak tahu jawabannya, "
        "katakan 'Maaf, saya tidak tahu jawabannya'."
        "\n\n\"{context}\""
    )

    qa_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", qa_system_prompt),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}")  # This is where the user's query will be inserted
        ]
    )

    # Create a document chain for answering questions using retrieved context
    question_answer_chain = create_stuff_documents_chain(llm, qa_prompt)

    # Combine the history-aware retriever with the question-answer chain
    rag_chain = create_retrieval_chain(
        history_aware_retriever, question_answer_chain
    )

    return rag_chain



def load_vector_store(embeddings):
    logging.info("Loading vector store.")
    vector_store = Chroma(
        collection_name="SPIL",
        embedding_function=embeddings or HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2", model_kwargs={'device': 'cpu'}), 
        persist_directory="vector_store"
    )
    logging.info("Vector store loaded successfully.")
    return vector_store

# Function to save uploaded file to the server
def save_uploaded_file(uploaded_file):
    save_dir = 'data'
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)

    file_path = os.path.join(save_dir, uploaded_file.filename)
    uploaded_file.save(file_path)
    return file_path

# Function to load all saved files from the server
def load_saved_files():
    save_dir = 'data'
    if not os.path.exists(save_dir):
        return []
    return [os.path.join(save_dir, f) for f in os.listdir(save_dir)]

# Function to split documents into smaller chunks
def split_documents(text):
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=100,
        length_function=len,
        is_separator_regex=False,
    )
    return text_splitter.split_text(text)
