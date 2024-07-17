from pyaiml21 import Kernel
from py2neo import Graph, Node, Relationship
import glob
from nltk.tokenize import sent_tokenize
from extra import askLlama

kernel = Kernel()
graph = Graph("bolt://localhost:7687", auth=("neo4j", "12345678"))
aiml_files = glob.glob(r"aimls/*.aiml")


for file in aiml_files:
    kernel.learn_aiml(file)

def newNode(type: str, name: str, extra: str, id: str):
    type, name, extra, id = type.strip(), name.strip(), extra.strip(), id.strip()
    if type == "student":
        query = """
        MERGE (c:IntelliShelf {name: "app"})
        CREATE (c)-[:HAS_USER]->(u:User {name: $name, department: $dept, id: $id})
        """
    elif type == "book":
        query = """
        MERGE (c:IntelliShelf {name: "app"})
        CREATE (c)-[:HAS_BOOK]->(u:Book {name: $name, author: $dept, id: $id})
        """
    graph.run(query, name=name, dept=extra, id=id)

def add_chat(user_id, user_prompt, bot_reply):
    query = """
    MATCH (u:User {id: $user_id})-[:HAS_MEM]->(m:EpisodicMemory)-[:HAS_EP]->(e:Episode)
    WITH e ORDER BY e.ep_no DESC LIMIT 1
    SET e.chat = e.chat + [$user_prompt, $bot_reply]
    SET e.endTimeStamp = datetime()
    RETURN e
    """
    
    graph.run(query, user_id=user_id, user_prompt=user_prompt, bot_reply=bot_reply)

def create_episode(user_id):
    query = """
    MATCH (u:User {id: $user_id}) WITH u
    MERGE (u)-[:HAS_MEM]->(m:EpisodicMemory) WITH m
    OPTIONAL MATCH (m)-[:HAS_EP]->(e:Episode)
    RETURN COALESCE(MAX(e.ep_no), 0) AS max_ep_no
    """
    
    result = graph.run(query, user_id=user_id).data()
    max_ep_no = result[0]['max_ep_no'] if result else 0
    new_ep_no = max_ep_no + 1
    
    create_query = """
    MATCH (u:User {id: $user_id})
    MATCH (u)-[:HAS_MEM]->(m:EpisodicMemory) WITH m
    CREATE (m)-[:HAS_EP]->(e:Episode {ep_no: $new_ep_no, startTimeStamp: datetime(), endTimeStamp: datetime(), chat: []})
    RETURN e
    """
    
    graph.run(create_query, user_id=user_id, new_ep_no=new_ep_no)

def end_episode(user_id):
    query = """
    MATCH (u:User {id: $user_id})-[:HAS_MEM]->(m:EpisodicMemory)
    MATCH (m)-[:HAS_EP]->(e:Episode)
    RETURN COALESCE(MAX(e.ep_no), 0) AS max_ep_no
    """
    
    result = graph.run(query, user_id=user_id).data()
    max_ep_no = result[0]['max_ep_no'] if result else 0
    
    create_query = """
    MATCH (u:User {id: $user_id})
    MATCH (u)-[:HAS_MEM]->(m:EpisodicMemory)
    MATCH (m)-[:HAS_EP]->(e:Episode {ep_no: $max_ep_no})
    SET e.endTimeStamp = datetime()
    RETURN e
    """
    
    graph.run(create_query, user_id=user_id, max_ep_no=max_ep_no)

def chat_sensory(user_id, prompt_text):
    # Tokenize prompt into sentences
    sentences = sent_tokenize(prompt_text)
    
    # Create SensoryMemory nodes if they don't exist
    query = """
    MATCH (u:User {id: $user_id}) WITH u
    MERGE (u)-[:HAS_MEM]->(m:SensoryMemory)
    RETURN m
    """
    graph.run(query, user_id=user_id)

    # Create Prompt node
    prompt_query = """
    MATCH (u:User {id: $user_id})-[:HAS_MEM]->(m:SensoryMemory) WITH m
    MERGE (m)-[:HAS_PROMPT]->(p:Prompt {text: $prompt_text})
    """
    graph.run(prompt_query, user_id=user_id, prompt_text=prompt_text)

    # Create Sentences and Words
    for sentence_text in sentences:
        sentence_query = """
        MATCH (u:User {id: $user_id})-[:HAS_MEM]->(m:SensoryMemory) WITH m
        MATCH (m)-[:HAS_PROMPT]->(p:Prompt {text: $prompt_text}) WITH p
        MERGE (p)-[:HAS_SENT]->(s:Sentence {text: $sentence_text})
        """
        graph.run(sentence_query, user_id=user_id, prompt_text=prompt_text, sentence_text=sentence_text)
        
        # Split sentence into words and create Word nodes
        words = sentence_text.split()
        previous_word = None
        
        for word_text in words:
            word_query = """
            MATCH (u:User {id: $user_id})-[:HAS_MEM]->(m:SensoryMemory) WITH m
            MATCH (m)-[:HAS_PROMPT]->(p:Prompt {text: $prompt_text}) WITH p
            MATCH (p)-[:HAS_SENT]->(s:Sentence {text: $sentence_text}) WITH s
            MERGE (s)-[:HAS_WORD]->(w:Word {word: $word_text})
            """
            graph.run(word_query,user_id=user_id, prompt_text=prompt_text, sentence_text=sentence_text, word_text=word_text)
            
            if previous_word:
                next_query = """
                MATCH (u:User {id: $user_id})-[:HAS_MEM]->(m:SensoryMemory) WITH m
                MATCH (m)-[:HAS_PROMPT]->(p:Prompt {text: $prompt_text}) WITH p
                MATCH (p)-[:HAS_SENT]->(s:Sentence {text: $sentence_text}) WITH s
                MERGE (s)-[:HAS_WORD]->(w1:Word {word: $prev_word})
                MERGE (s)-[:HAS_WORD]->(w2:Word {word: $current_word})
                MERGE (w1)-[:NEXT]->(w2)
                """
                graph.run(next_query, user_id=user_id, prompt_text=prompt_text, sentence_text=sentence_text, prev_word=previous_word, current_word=word_text)
            
            previous_word = word_text

def getBooks(user_id):
    query = """
    MATCH (a:User {id: $idA})-[:BORROWED]->(b:Book)
    return b
    """
    cursor = graph.run(query, idA=user_id)
    return cursor.data()

def chat_response(prompt: str, user_id: str) -> str | None:
    chat_sensory(user_id, prompt)
    response = kernel.respond(prompt, user_id)
    listBooks = kernel.get_predicate("list", user_id)
    if listBooks.lower() == "true":
        print("listing borrowed books")
        books = getBooks(user_id)
        kernel.setPredicate("list", "false", user_id)
        l = len(books)
        if l == 0:
            response = "You have not borrowed any book"
        else:
            response = "You have:"
            for i in range(l):
                # print(type(books[i]['b']['name']))
                response += f"""
{i+1}. {books[i]['b']['name']}     by     {books[i]['b']['author']}"""

    add_chat(user_id, prompt, response)
    if response.lower() == "unknown":
        print("going to LLAMA 3")
        response = askLlama(prompt)
    return response
