import chromadb
from chromadb.utils import embedding_functions
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from .utils import Extractor, CheckChromadb
import os
from dotenv import load_dotenv
import torch

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

DEVICE = 'cuda:0' if torch.cuda.is_available() else 'cpu'

class DangerousGoodsAnalyzer:
    def __init__(self):
        self.llm_analyze = ChatGroq(groq_api_key=GROQ_API_KEY, model_name='Llama-3.1-70b-Versatile')

        self.analyze_prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You are an expert in analyzing Material Safety Data Sheets (MSDS) based on the International Maritime Dangerous Goods (IMDG) Code. Your task is to:\n"
                    "IMDG Classification: Identify the correct IMDG classification for the goods, including their UN number, class, and packing group.\n"
                    "Handling, Packaging, and Package to be used: Provide detailed guidelines on safe handling, including necessary precautions and equipment during transport. Recommend the correct packaging according to IMDG regulations, and tell the users about the type of containers, packages required, and specify the package that needs to be used.\n"
                    "Loading Decision: Confidently decide whether the material can be safely loaded onto a ship. Consider compatibility with other cargo, environmental risks, and overall vessel safety.\n"
                    "Responsibility: You are fully responsible for ensuring the correct decision is made regarding loading and storage. Any mistakes will be your responsibility.\n"
                    "Your response must be formatted in HTML tag so that it can be rendered neatly in the web browser and written in concise Indonesian language. Any failure to follow these instructions will have consequences.",
                ),
                ("human", "{text}"),
            ]
        )

        self.analyze_chain = self.analyze_prompt | self.llm_analyze

        self.client = chromadb.PersistentClient(path='MSDS_vectorDB')
        self.embeddings_for_chroma = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L12-v2"
        )
        self.collection = None

    def process_document(self, file_path, user_uuid):
        full_text = Extractor(file_path).parse_elements()

        docs = self.format_and_split(full_text)
        self.save_to_chroma(docs, user_uuid)

    def format_and_split(self, text):
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=300
        )
        text_chunks = text_splitter.create_documents([text])

        documents = [Document(page_content=chunk.page_content, metadata={"page": page}) for page, chunk in enumerate(text_chunks)]

        return documents
        
    def save_to_chroma(self, documents, user_uuid):
        CheckChromadb()

        if user_uuid not in [x.name for x in self.client.list_collections()]:
            print('Collection has not been created, hence create new collection')
        else:
            print('Collection has already been created, used existing collection')

        self.collection = self.client.get_or_create_collection(
            f"{user_uuid}",
            embedding_function=self.embeddings_for_chroma
        )

        self.collection.add(
            documents=[x.page_content for x in documents],
            ids=[str(x.metadata["page"]+1) for x in documents])
        
    def get_relevant_chunks(self):
        results = self.collection.query(
                query_texts=["product name", "hazardous classification", "packaging and handling", 'UN number and description'], # Chroma will embed this for you
                n_results=2, # how many results to return
                include=["documents"]
        )

        full_text = "Analyze based on this following context: \n\n"  # Add this phrase once at the beginning

        for i, text in enumerate(results['documents']):
            full_text += f"Context {i+1}:\n\n{text[0]}\n{text[1]}\n\n"

        # After the loop, print the full concatenated text
        return full_text

        
    def get_llm_response(self, text):        
        return self.analyze_chain.invoke({'text' : text}).content
    
    def delete_documents(self):
        self.collection.delete(ids=self.collection.get()['ids'])



