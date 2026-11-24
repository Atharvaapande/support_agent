import os
from typing import TypedDict, List, Dict, Any, Optional
from langgraph.graph import StateGraph, START, END
from langchain_groq import ChatGroq 
from langchain_core.messages import HumanMessage

class Email(TypedDict):
    email: Dict[str, Any]
    is_spam: Optional[bool]
    response_mail: Dict[str, Any]