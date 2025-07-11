# PatentBot: LLM-Powered Patent Search Assistant

PatentBot is an AI-powered conversational assistant that allows users to search and query patent documents using natural language. It leverages a vector database (ChromaDB), an LLM from Hugging Face (Mistral), and scraped data from FreePatentsOnline to provide relevant patent information.

---

## Features

* 🔍 **Patent Retrieval**: Extracts and parses patents related to a specific topic using web scraping.
* 🧠 **LLM-Powered Q\&A**: Uses Mistral-7B via Hugging Face for intelligent answers based on retrieved patent contexts.
* 📦 **Vector Database Search**: Stores and searches patent content using ChromaDB with embeddings.
* 💬 **Conversational Memory**: Maintains interaction history for context-aware queries.
* ⚙️ **Robust XML Parsing**: Safely parses and validates structured responses from LLMs.

---

## Setup

### 1. Environment Variables

```bash
export HF_TOKEN="your_huggingface_token_here"
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

Required libraries include:

* `chromadb`
* `langchain`
* `huggingface_hub`
* `bs4`
* `requests`

---

## Workflow

### Step 1: Scrape Patent Data

Run the parser to collect up to 50 patents for a keyword/topic.

```bash
python parse.py
```

Output will be saved to `parsed_patents/<query>_50patents.csv`

### Step 2: Embed Patents in ChromaDB

Use the `tovectordb.py` script to convert the parsed patents into vector format.

```bash
python tovectordb.py
```

### Step 3: Run the Chatbot

Launch the conversational assistant:

```bash
python chat.py
```

Ask your patent-related questions in plain English.

---

## Example

```bash
🤖 PatentBot ready. Type 'exit' to quit.
🧠 You: I've a new method for unmanned coffee machine, is it already patented?
🔍 Found 3 relevant patent documents.
💡 Answer: The patent with ID 10997647 describes a method involving user arrival timing and automated order processing. Your idea appears distinct, but we recommend thorough review.
📄 Cited PIDs: 10997647
```

---

## Directory Structure

```
.
├── parsed_patents/             # Output folder for scraped patent CSVs
├── chroma_db_patents/         # ChromaDB vector store directory
├── chat.py                    # Main conversational interface
├── parse.py                   # Web scraper for FreePatentsOnline
├── tovectordb.py              # Embedding & indexing patents into vector DB
└── README.md                  # This documentation
```

---

## Future Enhancements

* 🔗 **Switch to Official Patent APIs**:

  * Replace scraping with structured APIs such as:

    * USPTO Open Data API
    * EPO's Open Patent Services (OPS)
    * Google Patent Public Datasets
  * This will ensure richer metadata and more reliable, large-scale ingestion.

* 🤖 **LLM Improvements**:

  * Upgrade to stronger models (e.g., GPT-4, Claude, Gemini Pro) for better reasoning.
  * Fine-tune LLM on patent data for improved technical language understanding.

* 📊 **Semantic Ranking**:

  * Use rerankers like Cohere or OpenAI's embeddings to reorder search results.

* 🧾 **Patent PDF Parsing**:

  * Integrate PDF extraction and OCR from patent PDFs directly.

---

