import os
import time
import xml.etree.ElementTree as ET
from typing import List, Dict
import textwrap
import re

import chromadb
from chromadb.utils.embedding_functions import DefaultEmbeddingFunction
from huggingface_hub import InferenceClient
from langchain.prompts import PromptTemplate
from langchain.memory import ConversationBufferMemory

# === Configuration ===
CHROMA_DB_DIR = "chroma_db_patents"
COLLECTION_NAME = "patent_docs"
EMBED_FN = DefaultEmbeddingFunction()
MISTRAL_MODEL = "mistralai/Mistral-7B-Instruct-v0.3"

HF_TOKEN = os.getenv("HF_TOKEN") or os.getenv("HUGGINGFACEHUB_API_TOKEN")
if not HF_TOKEN:
    raise EnvironmentError(
        "Please set HF_TOKEN (or HUGGINGFACEHUB_API_TOKEN) with proper permissions")

# === Load ChromaDB ===
client = chromadb.PersistentClient(path=CHROMA_DB_DIR)
try:
    collection = client.get_collection(
        COLLECTION_NAME, embedding_function=EMBED_FN)
except Exception as e:
    raise RuntimeError(f"Could not load collection '{COLLECTION_NAME}': {e}")

# === Set up Remote Inference Client ===
inference = InferenceClient(model=MISTRAL_MODEL, api_key=HF_TOKEN)

# === Memory Setup ===
memory = ConversationBufferMemory(memory_key="history", input_key="question")

# === Prompt Templates ===
prompt_context = PromptTemplate(
    input_variables=["history", "context", "question"],
    template=textwrap.dedent("""\
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
 - Do not include pid if the context and query does not match.
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

# === Helper Functions ===


def ask_llm(messages: List[Dict], max_tokens: int = 512) -> str:
    start = time.time()
    response = inference.chat_completion(
        messages=messages,
        max_tokens=max_tokens,
        temperature=0.0
    )
    elapsed = time.time() - start
    print(f"🧠 LLM responded in {elapsed:.2f}s")
    return response.choices[0].message.content


def extract_response_xml(text: str) -> str:
    # Capture from first <response> to last </response>
    starts = [m.start() for m in re.finditer(
        r"<response", text, re.IGNORECASE)]
    ends = [m.end() for m in re.finditer(r"</response>", text, re.IGNORECASE)]
    if starts and ends:
        return text[starts[0]:ends[-1]]
    return f"<response>\n{text.strip()}\n<patents></patents>\n</response>"


def parse_response(xml_text: str):
    try:
        root = ET.fromstring(xml_text)
        # Extract and clean answer text
        answer_node = root.find('answer')
        if answer_node is not None:
            # Remove any nested patent tags inside answer
            for child in list(answer_node):
                if child.tag.lower() in ('patents', 'patent', 'id', 'title', 'abstract', 'claims'):
                    answer_node.remove(child)
            ans = ''.join(answer_node.itertext()).strip()
        else:
            ans = (root.text or '').strip()

        # Extract patent IDs
        pids = []
        patents_node = root.find('patents')
        if patents_node is not None:
            # IDs under <pid> or nested under <patent>/<id>
            for pid in patents_node.findall('.//pid') + patents_node.findall('.//id'):
                if pid.text:
                    pids.append(pid.text.strip())
        return ans or '[No answer]', pids

    except ET.ParseError:
        # Fallback regex extraction
        answer_match = re.search(r'<answer>([\s\S]*?)</answer>', xml_text)
        ans = answer_match.group(1).strip() if answer_match else ''
        ids = re.findall(r'<pid>(\d+)</pid>', xml_text) + \
            re.findall(r'<id>(\d+)</id>', xml_text)
        unique_ids = list(dict.fromkeys(ids))
        return ans or '[No answer]', unique_ids

# === Main Chat Loop ===


def chatbot():
    print("🤖 PatentBot ready. Type 'exit' to quit.")
    while True:
        query = input("\n🧠 You: ").strip()
        if query.lower() in ('exit', 'quit'):
            break

        search = collection.query(query_texts=[query], n_results=3)
        contexts = search.get('documents', [[]])[0]
        print(f"\n🔍 Found {len(contexts)} relevant patent documents.")

        history_text = memory.load_memory_variables({})['history'] or ''
        if len(history_text) > 1000:
            history_text = history_text[-500:]
        ctx_text = '\n---\n'.join(contexts)
        if len(ctx_text) > 2000:
            ctx_text = ctx_text[:2000] + "\n[...context truncated...]"

        user_prompt = prompt_context.format(
            history=history_text, context=ctx_text, question=query)
        messages = [
            {'role': 'system', 'content': system_message},
            {'role': 'user', 'content': user_prompt}
        ]

        try:
            raw_output = ask_llm(messages)
            print(f"\n📦 Raw LLM Output:\n{raw_output}")
            xml_resp = extract_response_xml(raw_output)
            answer, pids = parse_response(xml_resp)
            print(f"\n💡 Answer: {answer}")
            print("📄 Cited PIDs:", ', '.join(pids) if pids else "None")
            memory.save_context({'question': query}, {'answer': answer})
        except Exception as e:
            print(f"\n❌ Error: {e}")
            continue


if __name__ == '__main__':
    chatbot()
