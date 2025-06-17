from google import genai

client = genai.Client(api_key="AIzaSyBtuSNec1HxWitVjUXpStmODN1aLmVxzQ8")

response = client.models.generate_content(
    model="gemini-2.5-flash-preview-05-20", contents="Explain how AI works in a few words"
)
print(response.text)