from groq import Groq
import os

key = os.environ.get("GROQ_API_KEY")
client = Groq(api_key=key)

def askLlama(prompt):
    completion = client.chat.completions.create(
        model="llama3-70b-8192",
        messages=[
            {
                "role": "user",
                "content": prompt + "\nReply in short concise paragraph"
            },
            {
                "role": "assistant",
                "content": """Welcome to IntelliShelf!

                            I'm happy to assist you with your library experience. Please feel free to ask me any questions about the books or the borrowing process.
                            Remember to scan your RFID card first to identify yourself, and then scan the book you'd like to borrow or return. Our IOT-enabled system will take care of the rest.
                            You can check the current status of your transaction on the LCD display.
                            If you need any help or have questions, I'm here to chat with you. What can I assist you with today?
                            Type 'books' to search for a specific book, 'borrow' to borrow a book, 'return' to return a book, or ask me any other question you may have!"""
            },
        ],
        temperature=1,
        max_tokens=1024,
        top_p=1,
        stream=True,
        stop=None,
    )
    reply = ""
    for chunk in completion:
        reply += chunk.choices[0].delta.content or ""
    return reply

# reply = askLlama(input())

# print(reply)

