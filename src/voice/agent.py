"""
Knowledge-Grounded Voice Agent Core.
Implements conversation state machine, qualification logic, dynamic RAG tool calling,
anti-hallucination safe fallbacks, human escalation, and mock CRM lead generation.
"""

import os
import json
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime
from dotenv import load_dotenv

from groq import Groq
from src.kb.store import KnowledgeStore

load_dotenv()

class VoiceAgent:
    """
    SME Business Loan Qualification & Inbound Voice Agent.
    Strictly grounded in Question 2 Knowledge Base via dynamic tool calling.
    """

    SYSTEM_PROMPT = """You are 'Darwix Assistant', a professional, warm, and highly efficient AI loan qualification specialist for Darwix Capital.

Your primary objective is to evaluate whether a business borrower qualifies for an unsecured Working Capital Loan, answer their questions with strict accuracy, and handle objections.

CRITICAL OPERATIONAL RULES:
1. QUALIFICATION CRITERIA (Strict Underwriting Guidelines):
   - Minimum Operating History: At least 12 consecutive months in business.
   - Minimum Monthly Revenue: At least $15,000 verified average monthly bank revenue.
   - Minimum Credit Score: At least 620.
   - Clean profile: No active bankruptcies or judgments in the trailing 24 months.

2. KNOWLEDGE BASE GROUNDING & ANTI-HALLUCINATION:
   - You DO NOT have all internal policies, APR tables, or objection guidelines memorized in your prompt.
   - Whenever the caller asks about interest rates, fee terms, repayment rules, partnership benefits, or raises objections (e.g. why rates are higher than a bank), you MUST invoke the `query_knowledge_base` tool.
   - If the tool response indicates that the knowledge base does not have the answer, or if the user asks an out-of-scope question, you MUST explicitly state: "I don't have that specific information in our current guidelines, but I can have a senior loan specialist review this for you." NEVER invent or assume facts!

3. CONVERSATION FLOW:
   - Keep answers conversational, natural, and concise (ideal for voice: 2 to 3 sentences maximum per turn).
   - Collect qualification details organically: Business Name, Months/Years in Business, Average Monthly Revenue, Loan Amount requested, and estimated Credit Score.
   - If the caller explicitly requests a human, representative, or manager, immediately call the `escalate_to_human` tool and inform the caller gracefully.
   - Once all details are collected and qualified, call `create_crm_lead` to submit the file.
"""

    def __init__(self, kb_store: Optional[KnowledgeStore] = None):
        self.api_key = os.getenv("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError("GROQ_API_KEY not found in environment.")
        self.groq_client = Groq(api_key=self.api_key)
        self.model = "qwen/qwen3.8-27b"
        
        # Load Knowledge Base
        self.kb_store = kb_store or KnowledgeStore.load_from_processed("data/processed/knowledge_base.json")
        
        # Active sessions state
        self.sessions: Dict[str, Dict[str, Any]] = {}

    def get_or_create_session(self, session_id: Optional[str] = None) -> Dict[str, Any]:
        if not session_id or session_id not in self.sessions:
            s_id = session_id or str(uuid.uuid4())[:8]
            self.sessions[s_id] = {
                "session_id": s_id,
                "history": [{"role": "system", "content": self.SYSTEM_PROMPT}],
                "lead_data": {
                    "business_name": None,
                    "months_in_business": None,
                    "monthly_revenue": None,
                    "loan_amount_requested": None,
                    "credit_score": None,
                    "is_qualified": False,
                    "qualification_reason": "In progress"
                },
                "status": "IN_PROGRESS",
                "escalated": False,
                "escalation_reason": None,
                "citations_used": [],
                "created_at": datetime.now().isoformat()
            }
            return self.sessions[s_id]
        return self.sessions[session_id]

    def _get_tools_spec(self) -> List[Dict[str, Any]]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "query_knowledge_base",
                    "description": "Searches the official Darwix Capital underwriting policies, product terms, fees, FAQs, and objections knowledge base.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "The specific domain query (e.g. 'early repayment penalty', 'why rates higher than bank', 'origination fee')"
                            }
                        },
                        "required": ["query"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "create_crm_lead",
                    "description": "Submits a completed borrower qualification lead to the CRM underwriting queue.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "business_name": {"type": "string"},
                            "months_in_business": {"type": "integer"},
                            "monthly_revenue": {"type": "number"},
                            "loan_amount_requested": {"type": "number"},
                            "credit_score": {"type": "integer"},
                            "is_qualified": {"type": "boolean"},
                            "summary_notes": {"type": "string"}
                        },
                        "required": ["business_name", "months_in_business", "monthly_revenue", "is_qualified"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "escalate_to_human",
                    "description": "Escalates the call to a human loan officer or supervisor when requested or upon complex conflict.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "reason": {
                                "type": "string",
                                "description": "Reason for human transfer (e.g. caller requested human, out of scope policy, complex complaint)"
                            }
                        },
                        "required": ["reason"]
                    }
                }
            }
        ]

    def _execute_tool(self, tool_name: str, args: Dict[str, Any], session: Dict[str, Any]) -> str:
        """Executes agent tool calls deterministically."""
        if tool_name == "query_knowledge_base":
            query = args.get("query", "")
            results = self.kb_store.search(query=query, top_k=2)
            if not results or results[0].score < 0.45:
                return "KNOWLEDGE_BASE_RESULT: No sufficiently relevant policy found in the official guidelines. Explicitly inform the customer that information is unavailable and offer human follow-up."
            
            top_rec = results[0].record
            citation = results[0].citation
            session["citations_used"].append(citation)
            return (
                f"KNOWLEDGE_BASE_RESULT (Score: {results[0].score:.2f}, {citation}):\n"
                f"Title: {top_rec.title}\n"
                f"Content: {top_rec.content}\n"
                f"Note: Answer the caller using only this context."
            )

        elif tool_name == "create_crm_lead":
            lead_data = session["lead_data"]
            lead_data.update(args)
            lead_data["created_at"] = datetime.now().isoformat()
            
            # Persist mock CRM lead
            leads_dir = os.path.join("data", "leads")
            os.makedirs(leads_dir, exist_ok=True)
            lead_file = os.path.join(leads_dir, f"lead_{session['session_id']}.json")
            with open(lead_file, "w", encoding="utf-8") as f:
                json.dump(lead_data, f, indent=2)
                
            session["status"] = "QUALIFIED" if args.get("is_qualified") else "DISQUALIFIED"
            return f"CRM_ACTION_SUCCESS: Lead recorded with ID {session['session_id']}. Status: {session['status']}."

        elif tool_name == "escalate_to_human":
            reason = args.get("reason", "Customer request")
            session["escalated"] = True
            session["escalation_reason"] = reason
            session["status"] = "ESCALATED"
            return f"ESCALATION_TRIGGERED: Senior specialist queue notified. Reason: {reason}. Warmly inform the customer."

        return f"Unknown tool: {tool_name}"

    def process_turn(self, user_text: str, session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Executes one full conversation turn including tool calling and state updates.
        """
        session = self.get_or_create_session(session_id)
        session["history"].append({"role": "user", "content": user_text})

        # Step 1: Query LLM with available tools
        response = self.groq_client.chat.completions.create(
            model=self.model,
            messages=session["history"],
            tools=self._get_tools_spec(),
            tool_choice="auto",
            temperature=0.2,
            max_tokens=250
        )

        choice = response.choices[0]
        message = choice.message

        # Step 2: Handle Tool Calls if any
        if message.tool_calls:
            session["history"].append(message)
            for tool_call in message.tool_calls:
                fn_name = tool_call.function.name
                fn_args = json.loads(tool_call.function.arguments) if tool_call.function.arguments else {}
                tool_output = self._execute_tool(fn_name, fn_args, session)

                session["history"].append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": fn_name,
                    "content": tool_output
                })

            # Get final spoken response after tool feedback
            final_response = self.groq_client.chat.completions.create(
                model=self.model,
                messages=session["history"],
                temperature=0.2,
                max_tokens=250
            )
            bot_text = final_response.choices[0].message.content
        else:
            bot_text = message.content

        session["history"].append({"role": "assistant", "content": bot_text})

        return {
            "session_id": session["session_id"],
            "bot_response": bot_text,
            "status": session["status"],
            "escalated": session["escalated"],
            "citations_used": session["citations_used"],
            "lead_data": session["lead_data"]
        }
