from langchain_mistralai import ChatMistralAI
from langchain_core.prompts import ChatPromptTemplate

from schema import ProductCopy

def build_pipeline(model_name: str = "mistral-small-2506", temperature: float = 0.1):

    prompt = ChatPromptTemplate.from_messages([
        ("system",
         "You are an expert e-commerce copywriter and SEO specialist. "
         "You only use the facts given to you and never invent specifications. "
         "You always return exactly 3 clearly different variants."),
        ("human", 
         "Product SKU: {sku}\n\n"
         "Source product information:\n{content}\n\n"
         "Generate exactly 3 distinct sets of: product title, description, "
         "SEO meta title, and SEO meta description.")
    ])

    llm = ChatMistralAI(model=model_name, temperature=temperature)

    structured_llm = llm.with_structured_output(ProductCopy)

    pipeline = prompt | structured_llm

    return pipeline

def generate_for_product(pipeline, sku, content) -> ProductCopy:
    """Run ONE product through the pipeline and get 3 variants back."""

    return pipeline.invoke({"sku": str(sku), "content": str(content)})