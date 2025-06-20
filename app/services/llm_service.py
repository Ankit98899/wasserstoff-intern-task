import os
import groq
from dotenv import load_dotenv
_current_dir = os.path.dirname(os.path.realpath(__file__))
_dotenv_path = os.path.abspath(os.path.join(_current_dir, "..", "api", "vectorDb", ".env"))

if os.path.exists(_dotenv_path):
    print(f"INFO (llm_service): Loading .env from: {_dotenv_path}")
    load_dotenv(dotenv_path=_dotenv_path)
else:
    print(f"WARNING (llm_service): .env file not found at {_dotenv_path}. Attempting to load from standard locations or existing environment variables.")
    load_dotenv() 

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

def get_groq_client():
    """Initializes and returns a Groq client if API key is available."""
    if GROQ_API_KEY:
        try:
            client = groq.Groq(api_key=GROQ_API_KEY)
            return client
        except Exception as e:
            print(f"ERROR (llm_service): Failed to initialize Groq client: {e}")
            return None
    else:
        print("WARNING (llm_service): GROQ_API_KEY environment variable not found. LLM features will be disabled.")
        return None

def get_llm_synthesis_with_citations(groq_client: groq.Groq, user_query: str, retrieved_chunks: list, llm_model_name: str = "llama3-8b-8192"):
    """
    Generates a synthesized answer, themes, and citations using a Groq LLM.

    Args:
        groq_client: The initialized Groq client.
        user_query: The user's original query.
        retrieved_chunks: A list of dictionaries, where each dict is a search result
                          from FAISS (must contain 'text', 'source_doc', 'chunk_num_in_doc').
                          It can also contain 'page_number' if available.
        llm_model_name: The Groq model to use (e.g., "llama3-8b-8192", "mixtral-8x7b-32768").

    Returns:
        A tuple: (llm_response_text, document_reference_mapping)
        llm_response_text: String containing the LLM's full response.
        document_reference_mapping: Dict mapping "Document Ref X" to actual source info.
        Returns (None, None) if an error occurs or no client.
    """
    if not groq_client:
        print("ERROR (llm_service): Groq client not initialized. Cannot make LLM call.")
        return None, None
    
    if not retrieved_chunks:
        print("INFO (llm_service): No chunks provided for LLM synthesis.")
        return "I couldn't find any relevant documents with the current search to answer your query or identify themes.", {}

    context_parts = []
    doc_ref_mapping = {} 

    for i, chunk_info in enumerate(retrieved_chunks):
        ref_id_for_llm = f"Document Ref {i+1}" 
        
        actual_source_info = f"{chunk_info.get('source_doc', 'Unknown Source')} (Chunk {chunk_info.get('chunk_num_in_doc', 'N/A')}"
        if 'page_number' in chunk_info and chunk_info['page_number'] is not None:
            actual_source_info += f", Page {chunk_info['page_number']}"
        actual_source_info += ")"
        doc_ref_mapping[ref_id_for_llm] = actual_source_info
        

        chunk_text_content = chunk_info.get('text', 'Error: Chunk text not found.')
        context_parts.append(f"{ref_id_for_llm}:\n\"{chunk_text_content}\"\n") 
    
    context_str = "\n".join(context_parts)

    prompt = f"""You are an AI research assistant. Your task is to answer a user's query based *only* on the provided document excerpts below. You must also identify common themes and cite your sources accurately using the provided 'Document Ref X' labels.

Provided Document Excerpts:
{context_str}

User Query: "{user_query}"

Instructions for your response:
1.  **Synthesized Answer:** Provide a direct and comprehensive answer to the User Query. Base your answer *strictly* on the information found in the "Provided Document Excerpts." Do not use any external knowledge. If the excerpts do not contain enough information to answer, explicitly state that.
2.  **Citations for Answer:** For every factual statement in your Synthesized Answer, you MUST cite the supporting 'Document Ref(s)' immediately after the statement or at the end of the sentence. Use the format (Document Ref X) or (Document Ref X, Document Ref Y).
3.  **Identified Themes:** After the answer, list any common themes that emerge from the excerpts relevant to the query. Each theme should be clearly described. If no clear themes emerge from the provided excerpts related to the query, state that.
4.  **Citations for Themes:** For each identified theme, you MUST cite all 'Document Ref(s)' that support or exemplify that theme. Use the format (Document Ref X, Document Ref Y).

Example Response Structure:

Synthesized Answer:
The sky is often blue due to Rayleigh scattering (Document Ref 1). Some reports also indicate that water can appear blue (Document Ref 2, Document Ref 3).

Identified Themes:
*   Atmospheric Optics: This theme is supported by discussions on light scattering (Document Ref 1).
*   Properties of Water: This theme is supported by observations about water's appearance (Document Ref 2, Document Ref 3).

Begin your response now.
"""

    print(f"INFO (llm_service): Sending prompt to Groq LLM (model: {llm_model_name}). Context length approx: {len(context_str)} chars.")

    try:
        chat_completion = groq_client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            model=llm_model_name,
            temperature=0.2,
        )
        response_content = chat_completion.choices[0].message.content
        print("INFO (llm_service): Groq LLM response received successfully.")
        return response_content, doc_ref_mapping
    except Exception as e:
        print(f"ERROR (llm_service): Groq API call failed: {e}")
        return None, None

if __name__ == '__main__':
    print("--- Testing llm_service.py ---")
    if not GROQ_API_KEY:
        print("GROQ_API_KEY not set. Please set it in your .env file at the expected location.")
    else:
        print(f"GROQ_API_KEY found (partially hidden): {GROQ_API_KEY[:5]}...{GROQ_API_KEY[-5:]}")
        
        client = get_groq_client()
        if client:
            print("Groq client initialized successfully.")
            print("Attempting to list available models (first 5)...")
            try:
                models = client.models.list().data
                if models:
                    for i, model in enumerate(models[:5]):
                        print(f"  - {model.id} (Owned by: {model.owned_by})")
                else:
                    print("No models returned by client.models.list()")
            except Exception as e:
                print(f"Error listing models: {e}")

        else:
            print("Groq client could not be initialized.")
    print("--- llm_service.py test finished ---")
 



