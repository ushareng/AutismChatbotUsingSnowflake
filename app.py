import streamlit as st # Import python packages
from snowflake.snowpark.context import get_active_session
session = get_active_session() # Get the current credentials

import pandas as pd

pd.set_option("max_colwidth",None)
num_chunks = 10 # Num-chunks provided as context. Play with this to check how it affects your accuracy

def create_prompt (myquestion):

    cmd = """
     with results as
     (SELECT RELATIVE_PATH,
       VECTOR_COSINE_SIMILARITY(docs_chunks_table.chunk_vec,
                SNOWFLAKE.CORTEX.EMBED_TEXT_768('e5-base-v2', ?)) as similarity,
       chunk
     from docs_chunks_table
     order by similarity desc
     limit ?)
     select chunk, relative_path from results 
     """
    
    df_context = session.sql(cmd, params=[myquestion, num_chunks]).to_pandas()      
    
    context_lenght = len(df_context) -1
    
    prompt_context = ""
    for i in range (0, context_lenght):
        prompt_context += df_context._get_value(i, 'CHUNK')
    
    prompt_context = prompt_context.replace("'", "")
    relative_path =  df_context._get_value(0,'RELATIVE_PATH')
    
    prompt = f"""
      'You are an expert assistance extracting information from context provided. 
       Answer the question based on the context. Be concise and do not hallucinate. 
      Context: {prompt_context}
      Question:  
       {myquestion} 
       Answer: '
       """
    
    return prompt

def complete(myquestion, model_name):

    prompt = create_prompt (myquestion)
    cmd = f"""
             select SNOWFLAKE.CORTEX.COMPLETE(?,?) as response
           """
    
    df_response = session.sql(cmd, params=[model_name, prompt]).collect()
    return df_response

def display_response (question, model):
    response = complete(question, model)
    res_text = response[0].RESPONSE
    st.markdown(res_text)

#Main code

st.title("Asking Questions related to Autism")

model = 'snowflake-arctic'
question = st.text_input("Enter question", placeholder="Tell me about Autiusm?", label_visibility="collapsed")


if question:
    display_response (question, model)