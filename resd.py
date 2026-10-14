import os
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("UNIPROT_API_KEY")
print(f"读取到的密钥是：{api_key}")