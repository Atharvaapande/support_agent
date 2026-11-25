from llama_index.core.tools import QueryEngineTool
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
import chromadb
import os
from dotenv import load_dotenv
from typing import TypedDict, List, Dict, Any, Optional
from langgraph.graph import StateGraph, START, END
from langchain_groq import ChatGroq 
from langchain_core.messages import HumanMessage
from llama_index.core import SimpleDirectoryReader, VectorStoreIndex
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.core.ingestion import IngestionPipeline
from llama_index.core.text_splitter import SentenceSplitter
import base64
from email.message import EmailMessage
from registerGmail import get_gmail_service
from llama_index.llms.groq import Groq

class EmailState(TypedDict):
    email: Dict[str, Any]
    is_spam: Optional[bool]
    is_query: Optional[bool]
    query: Optional[str]
    rag_ans: Optional[str]
    response_mail: Dict[str, Any]
    messages:List[Dict[str, Any]] 

load_dotenv()
llm = ChatGroq(model="openai/gpt-oss-120b", api_key=os.getenv('GROQ_API'),temperature=0)
llama_llm = Groq(model="openai/gpt-oss-120b", api_key=os.getenv("GROQ_API"))
embedding_model = HuggingFaceEmbedding(model_name="BAAI/bge-small-en-v1.5")
builder = StateGraph(EmailState)

# nodes
def read_mail(state: EmailState):
    """support agent logs the start of the process"""
    print(f"support agent recieved the mail from {state['email']['from']}, process started\n")
    return {}

def checkIsSpam(state: EmailState):
    """Support agent checks if the email is spam or legit"""

    prompt = f"""
    you have 2 tasks -
    1) check the given mail below and determine weather it is spam or legit, if it is spam reply with spam, if not spam then reply legit.
    2) check that is the email contain any query from user or it is just normal email, if it contain query the reply with query email else reply with normal email.

    email is as follow:
    email subject: {state['email']['subject']},
    from: {state['email']['from']},
    body: {state['email']['body']}
    """
    msg = [HumanMessage(content=prompt)]
    
    response = llm.invoke(msg)
    res = response.content.lower()
    is_spam = "spam" in res
    is_query = "query email" in res

    new_message = state.get('messages',[]) + [
        {'role': 'user', "content":prompt},
        {'role': 'assistant', "content": response}
    ]

    return {
        "is_spam": is_spam,
        "is_query": is_query,
        "messages": new_message
    }

def spamHandler(state: EmailState):
    """handle the spam email"""
    print("this is a spam email, and not processed further")
    return {}

def replyGenerator(state: EmailState):
    """Generates clean response without subject line or placeholders"""
    
    system_rules = """
    STRICT RULES FOR YOUR RESPONSE:
    1. DO NOT include any 'Subject:' line in your response (it is already in the email headers).
    2. Start directly with the greeting (e.g. 'Hi Atharva,').
    3. Do NOT use markdown tables (use clean bullet points instead).
    4. Do NOT leave placeholders like '[Your Name]', '[Company]', or '[Contact Information]'.
    5. Sign off simply as:
       Best regards,
       Support Team
    """

    if state['is_query']:
        prompt = f"""
        {system_rules}

        Answer the user's query politely using this reference:
        User query: {state['query']}
        Reference information: {state['rag_ans']}

        Original email:
        From: {state['email']['from']}
        Body: {state['email']['body']}
        """
    else:
        prompt = f"""
        {system_rules}

        Generate a polite response to this email:
        From: {state['email']['from']}
        Body: {state['email']['body']}
        """

    msg = [HumanMessage(content=prompt)]
    response = llm.invoke(msg)
    
    # Safety strip: removes any accidental 'Subject:' line if generated
    clean_body = response.content.strip()
    if clean_body.lower().startswith("**subject:") or clean_body.lower().startswith("subject:"):
        clean_body = clean_body.split("\n", 1)[-1].strip()

    return {
        "response_mail": clean_body,
        "messages": state.get('messages', []) + [{'role': 'assistant', 'content': clean_body}]
    }

def ragAgent(state: EmailState):
    """this agent help to retrive info from the vector db and generate a reply for the query email"""
    prompt = f"""
    extract the user query from the query email below and return me that query -
    email -
    email subject: {state['email']['subject']},
    from: {state['email']['from']},
    body: {state['email']['body']}
    """

    msg = [HumanMessage(content=prompt)]
    res = llm.invoke(msg)
    query = res.content.strip()
    rag_ans=query_engine.query(query)    
    return {
        "query":query,
        "rag_ans":rag_ans
    }

def send_reply(state: EmailState):
    service = get_gmail_service()
    
    msg = EmailMessage()
    msg.set_content(state["response_mail"])
    msg["To"] = state["email"]["from"]
    
    # Avoid duplicate "Re: Re:"
    subject = state["email"].get("subject", "")
    msg["Subject"] = subject if subject.lower().startswith("re:") else f"Re: {subject}"
    
    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
    
    service.users().messages().send(
        userId="me",
        body={"raw": raw, "threadId": state["email"].get("thread_id")}
    ).execute()
    
    print(f"✅ Clean reply sent to {state['email']['from']}")
    return {}

def route(state: EmailState)->str:
    """Route the flow to rag agent or to response generator based on the conditions"""
    if(state['is_query']==True and state['is_spam']==False):
        return "rag"
    elif(state['is_query']==False and state['is_spam']==False):
        return 'gen'
    else:
        return "spam"
     

# tools
doc = SimpleDirectoryReader(input_dir="./docs").load_data()
db = chromadb.PersistentClient(path="./db")
chroma_collection = db.get_or_create_collection('doc')
vector_store = ChromaVectorStore(chroma_collection=chroma_collection)

pipe = IngestionPipeline(
    transformations=[
        SentenceSplitter(chunk_size=70, chunk_overlap=5),
        embedding_model
    ],
    vector_store=vector_store
)

pipe.run(documents=doc)

index = VectorStoreIndex.from_vector_store(
    vector_store=vector_store,
    embed_model=embedding_model
)

query_engine = index.as_query_engine(
    llm=llama_llm,
    response_mode='tree_summarize'
)

query_engine_tool = QueryEngineTool.from_defaults(
    query_engine=query_engine,
    name="query engine",
    description="this tool helps to retrive information from the vector db related to the users query in the email",
    return_direct=False
)

# graph
builder.add_node('read_mail', read_mail)
builder.add_node('checkIsSpam',checkIsSpam)
builder.add_node('spamHandler',spamHandler)
builder.add_node('replyGenerator',replyGenerator)
builder.add_node('ragAgent',ragAgent)
builder.add_node("send_reply", send_reply)

builder.add_edge(START,'read_mail')
builder.add_edge('read_mail',"checkIsSpam")
builder.add_conditional_edges(
    'checkIsSpam',
    route,
    {
        "rag":"ragAgent",
        "gen":"replyGenerator",
        "spam":"spamHandler"     
    }
)
builder.add_edge("ragAgent", "replyGenerator")
builder.add_edge("replyGenerator", "send_reply")
builder.add_edge("send_reply",END)
builder.add_edge("spamHandler", END)

agent_app = builder.compile()

try:
    with open("graph.png", "wb") as f:
        f.write(agent_app.get_graph().draw_mermaid_png())
    print("Graph saved to graph.png!")
except Exception as e:
    print(e)

def run_agent(email_data: dict):
    return agent_app.invoke({"email": email_data})