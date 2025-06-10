<<<<<<< HEAD
# 📄 Document Research & Theme Identification Chatbot

This project is an interactive chatbot that can perform research across a large set of documents
(minimum 75 documents), identify common themes (multiple themes are possible), and
provide detailed, cited responses to user queries.

---

## Features

* **Multi-Format Document Processing:** Supports PDFs, text files, and image documents.
* **OCR Integration:** Uses Tesseract OCR to extract text from images or scanned PDFs.
* **LLM (Groq) Integration:** Connects to the Groq API to enable generative capabilities like answering questions.
* **Vector Search with FAISS:** Embeds documents using Sentence Transformers and stores them in FAISS for efficient similarity-based querying.
* **API Interface (Flask):** Exposes endpoints to upload, query, and fetch summaries.

---

## ⚙️ Tech Stack

| Layer           | Technology                      |
| --------------- | ------------------------------- |
| Language        | Python 3.10                     |
| Web Framework   | Flask                        |
| OCR Engine      | Tesseract + pytesseract         |
| LLM             | Groq API                        |
| NLP / Embedding | SentenceTransformers, LangChain |
| Vector DB       | FAISS                           |
| Deployment      | Docker, Hugging Face            |

---

## 📁 Project Structure

```
.
├── backend
│   ├── app
│   │   ├── api/            
│   │   ├── core/           
│   │   ├── services/       
│   │   ├── templates/      
│   │   ├── main.py         
│   │               
│   ├── Dockerfile          
│   └── requirements.txt    
├── data/ 
|___.env                  
├── README.md               
```

---

## 🐳 Running with Docker

### 1. Clone the repository

```bash
git clone 
cd wasserstoff-AiInternTask
```

### 2. Set your Groq API Key:  


Create a `.env` file in the root: 
```

GROQ_API_KEY=your_groq_api_key_here 
OPENAI_API_KEY=your_openapi_key_here

```

Ensure `.env` is in your `.gitignore`.

### 3. Build Docker image:

```bash
docker build --build-arg GROQ_API_KEY=$(grep GROQ_API_KEY .env | cut -d '=' -f2) -t document-qa-backend .
```

### 4. Run the Docker container

```bash
docker run -d -p 8080:8080 --name docqa document-qa-backend
```

Visit the app at: [http://localhost:8080]


=======
# wasserstoff-intern-task
This repository contains the research, analysis, and implementation details of a chatbot system focused on processing documents and identifying key themes. The project explores natural language processing techniques for understanding and extracting meaningful information, aiming to enhance chatbot interactions through contextual awareness.
>>>>>>> 10928588d2bc8e86086a9a68b2df04da865e8952
