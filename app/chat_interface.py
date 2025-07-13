# app/chat_interface.py
import time
from typing import Tuple, List
import textwrap
import re
import os
import xml.etree.ElementTree as ET

from huggingface_hub import InferenceClient
import chromadb
from chromadb.utils.embedding_functions import DefaultEmbeddingFunction
from langchain.prompts import PromptTemplate
from langchain.memory import ConversationBufferMemory

# === CONFIG ===
CHROMA_DB_DIR = os.path.join(os.path.dirname(__file__), "chroma_db_patents")
COLLECTION_NAME = "patent_docs"
MISTRAL_MODEL = "mistralai/Mistral-7B-Instruct-v0.3"
HF_TOKEN = os.getenv("HF_TOKEN") or os.getenv("HUGGINGFACEHUB_API_TOKEN")
if not HF_TOKEN:
    raise EnvironmentError("Please set HF_TOKEN or HUGGINGFACEHUB_API_TOKEN")

# === DB + EMBEDDING ===
client = chromadb.PersistentClient(path=CHROMA_DB_DIR)
collection = client.get_collection(COLLECTION_NAME, embedding_function=DefaultEmbeddingFunction())

# === LLM ===
inference = InferenceClient(model=MISTRAL_MODEL, api_key=HF_TOKEN)

# === MEMORY ===
memory = ConversationBufferMemory(memory_key="history", input_key="question")

# === PROMPT ===
prompt_context = PromptTemplate(
    input_variables=["history", "context", "question"],
    template=textwrap.dedent("""
        Previous history:
        {history}

        Patent context:
        {context}

        User question: {question}
    """)
)

system_message = textwrap.dedent("""
You are a helpful assistant answering queries to the user politely and concisely.
Follow the below instructions carefully:
 - Always provide a clear and concise answer.
 - Use context, chat history, and a user question to use as a basis for your response.
 - If the context and user query does not match, then skip patent id search and provide a response that is relevant to the question and say - "There's no relevant content in knowledge base".
 - Do not include patent id's if the context and query does not match.
 - If the context and user query match, then provide a response that is relevant to the question.  
 - Grab the relevant patent IDs from the context and include them in your response.    
 - If you cannot find any relevant patent IDs, just say "None".     
 - Response should be in following format *only*: 
    <response>
        <answer> 
            YOUR_ANSWER_HERE 
        </answer>
        <patents>
            <pid>PID1</pid>
            <pid>PID2</pid>
            ...
        </patents>
    </response>        
 - Do not include any other tags or text outside of the <response>...</response> block.
 - I do not want you to hallucinate.
""")

# === UTIL ===
def extract_response_xml(text: str) -> str:
    starts = [m.start() for m in re.finditer(r"<response", text, re.IGNORECASE)]
    ends = [m.end() for m in re.finditer(r"</response>", text, re.IGNORECASE)]
    if starts and ends:
        return text[starts[0]:ends[-1]]
    return f"<response>\n{text.strip()}\n<patents></patents>\n</response>"

def parse_response(xml_text: str) -> Tuple[str, List[str]]:
    try:
        root = ET.fromstring(xml_text)
        answer_node = root.find('answer')
        ans = ''.join(answer_node.itertext()).strip() if answer_node is not None else '[No answer]'
        pids = [pid.text.strip() for pid in root.findall(".//pid") + root.findall(".//id") if pid.text]
        return ans, pids
    except ET.ParseError:
        answer_match = re.search(r'<answer>([\s\S]*?)</answer>', xml_text)
        ans = answer_match.group(1).strip() if answer_match else '[No answer]'
        ids = re.findall(r'<pid>(\d+)</pid>', xml_text) + re.findall(r'<id>(\d+)</id>', xml_text)
        return ans, list(dict.fromkeys(ids))

# === MAIN FUNCTION ===
async def run_query(message: str) -> Tuple[str, List[str]]:
    search = collection.query(query_texts=[message], n_results=3)
    documents = search.get("documents", [[]])[0]
    context = "\n---\n".join(documents)
    history_text = memory.load_memory_variables({})["history"] or ""

    if len(history_text) > 1000:
        history_text = history_text[-500:]
    if len(context) > 2000:
        context = context[:2000] + "\n[...context truncated...]"

    prompt = prompt_context.format(history=history_text, context=context, question=message)

    messages = [
        {"role": "system", "content": system_message},
        {"role": "user", "content": prompt},
    ]

    response = inference.chat_completion(messages=messages, max_tokens=512, temperature=0.0)
    raw_output = response.choices[0].message.content

    xml = extract_response_xml(raw_output)
    answer, pids = parse_response(xml)
    memory.save_context({"question": message}, {"answer": answer})
    return answer, pids
