import streamlit as st
from langgrah_backend import chatbot
from langchain_core.messages import HumanMessage
import uuid
#****************** utility functions ******************#

def generate_thread_id():
   thread_id = str(uuid.uuid4())
   return thread_id

def reset_chat():
    thread_id = generate_thread_id()
    st.session_state['thread_id'] = thread_id
    add_thread(st.session_state['thread_id'])
    st.session_state['message_history'] = []

def add_thread(thread_id):
    if thread_id not in st.session_state['chat_threads']:
        st.session_state['chat_threads'].append(thread_id)

def load_conversation(thread_id):
    return chatbot.get_state(config=CONFIG).values['messages']
# _____________________________________________________________________

#session setup
if 'message_history' not in st.session_state:
    st.session_state['message_history'] = []
if 'thread_id' not in st.session_state:
    st.session_state['thread_id'] = generate_thread_id()

if 'chat_threads' not in st.session_state:
    st.session_state['chat_threads']= []
add_thread(st.session_state['thread_id'])

CONFIG = {'configurable': {'thread_id': st.session_state['thread_id']}}
# _____________________________________________________________________
#Sidebar ui
st.sidebar.title("LangGraph Chatbot")
if st.sidebar.button("new chat"):
    reset_chat()

st.sidebar.header("Conversation History")
for thread_id in st.session_state['chat_threads'][::-1]:
    if st.sidebar.button(thread_id):
        st.session_state['thread_id']=thread_id
        messages = load_conversation(thread_id)

        temp_messages = []
        for message in messages:
            if isinstance(message,HumanMessage):
                role='user'
            else:
                role='assistant'
            temp_messages.append({'role':role,'content':message.content})
        st.session_state['message_history'] = temp_messages

# Load conversation history with Markdown rendering
for message in st.session_state['message_history']:
    with st.chat_message(message['role']):
        st.text(message['content'])

user_input = st.chat_input('Type here')

if user_input: 
    # 1. Store and display user message
    st.session_state['message_history'].append({'role': 'user', 'content': user_input})
    with st.chat_message('user'):
        st.markdown(user_input)

    # 2. Stream AI response with proper content extraction
    with st.chat_message('assistant'):

        def stream_response():
            for message_chunk, metadata in chatbot.stream(
                {'messages': [HumanMessage(content=user_input)]},
                config=CONFIG,
                stream_mode='messages'
            ):
                # Handle standard string content
                if isinstance(message_chunk.content, str) and message_chunk.content:
                    yield message_chunk.content
                # Handle structured content blocks (e.g., Gemini list chunks)
                elif isinstance(message_chunk.content, list):
                    for part in message_chunk.content:
                        if isinstance(part, dict) and part.get('type') == 'text':
                            yield part.get('text', '')

        ai_message = st.write_stream(stream_response())

    # 3. Save assistant message to history
    st.session_state['message_history'].append({'role': 'assistant', 'content': ai_message})