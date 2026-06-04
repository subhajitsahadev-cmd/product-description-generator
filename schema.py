from typing import List
from pydantic import BaseModel, Field

class Variant(BaseModel):
    title: str = Field(description="Catchy, clear product title")
    description: str = Field(description="Persuasive product description, 2-4 sentences")
    meta_title: str = Field(description="SEO meta ttile, 50-60 characters")
    meta_description: str = Field(description="SEO meta description, 150-160 characters, with a call to action")

class ProductCopy(BaseModel):
    variants: List[Variant] = Field(
        description="Exactly 3 DISTINCT variants. Make them different: "
                    "variant 1 feature-focused, variant 2 benefit-focused, variant 3 emotional/lifestyle."
    )