from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint



def free_model():
    llm = HuggingFaceEndpoint(
        repo_id="Qwen/Qwen2.5-7B-Instruct",
        task="text-generation",
        max_new_tokens=512,
        huggingfacehub_api_token=HF_API_KEY,
    )

    model = ChatHuggingFace(llm=llm)
    return model
