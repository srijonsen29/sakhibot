import sys
import os
from pathlib import Path

# Allow `python scripts/critique_loop.py` from backend/ directory
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.agents.legal_retriever import retrieve, SYSTEM_PROMPT
from app.core.groq_client import chat as groq_chat

EVALUATION_PROMPT = """You are an independent AI critique evaluator.
Your job is to check if the following legal response satisfies these quality rules:
1. CITATION_CHECK: The response must cite a specific Indian Act (e.g., "Domestic Violence Act", "POSH Act", "Section 498A") or legal section.
2. NEXT_STEP_CHECK: The response must provide a clear, practical next step the user can take (e.g., contacting the ICC, filing an FIR, calling 181).
3. HELPLINE_CHECK: The response must mention calling 181 (Women's Helpline) or the police.

Analyze the Response and output a structured analysis.
Then output "STATUS: APPROVED" if all conditions are met. Otherwise, output "STATUS: REJECTED" and list the missing elements.

Context:
{context}

Response:
{response}
"""

REFINEMENT_PROMPT = """You are SakhiBot, a legal rights assistant for women in India.
Your previous response was critique-reviewed and rejected.

Critique Feedback:
{feedback}

Original Question:
{query}

Context documents:
{context}

Please rewrite the response to address the critique completely. Ensure it:
1. Grounded only in the context.
2. Empathy-focused.
3. Contains clear citations of Acts.
4. Includes one clear, practical next step.
5. Reminds the user to call 181 (Women's Helpline) for immediate help.
"""

def evaluate_response(query: str, context: str, response: str) -> tuple[bool, str]:
    messages = [
        {"role": "system", "content": "You are a precise quality evaluator."},
        {"role": "user", "content": EVALUATION_PROMPT.format(context=context, response=response)}
    ]
    evaluation = groq_chat(messages, temperature=0.0)
    approved = "STATUS: APPROVED" in evaluation
    return approved, evaluation

def run_critique_loop(query: str):
    print("=" * 60)
    print(f"QUERY: {query}")
    print("=" * 60)
    
    # Step 1: Retrieve context
    print("[1] Retrieving context from ChromaDB...")
    retrieved = retrieve(query)
    chunks = retrieved["chunks"]
    context_str = "\n\n---\n\n".join(chunks)
    
    if not chunks:
        print("No context found. Exiting.")
        return
        
    # Step 2: Generate baseline response
    print("[2] Generating baseline response...")
    baseline_messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"Context documents:\n{context_str}\n\nQuestion: {query}"}
    ]
    baseline_response = groq_chat(baseline_messages, temperature=0.1)
    
    print("\n--- BASELINE RESPONSE ---")
    print(baseline_response)
    print("-" * 30)

    # Step 3: Critique/Evaluate
    print("[3] Evaluating response...")
    approved, critique = evaluate_response(query, context_str, baseline_response)
    print(f"Evaluation Critique:\n{critique}")
    
    if approved:
        print("\n✅ Response meets all quality guidelines first try! No refinement needed.")
        return
        
    # Step 4: Refine
    print("\n❌ Response failed evaluation. Initiating refinement...")
    refine_messages = [
        {"role": "system", "content": "You are a helpful assistant correcting a response."},
        {"role": "user", "content": REFINEMENT_PROMPT.format(feedback=critique, query=query, context=context_str)}
    ]
    refined_response = groq_chat(refine_messages, temperature=0.1)
    
    print("\n--- REFINED RESPONSE ---")
    print(refined_response)
    print("-" * 30)
    
    # Re-evaluate
    print("[5] Re-evaluating refined response...")
    still_approved, final_critique = evaluate_response(query, context_str, refined_response)
    if still_approved:
        print("\n✅ Refinement successful! Response now meets all quality standards.")
    else:
        print("\n⚠️ Refined response still failed check. Outputting final anyway.")

if __name__ == "__main__":
    test_query = "What rights do I have if my husband is beating me?"
    if len(sys.argv) > 1:
        test_query = " ".join(sys.argv[1:])
    run_critique_loop(test_query)
