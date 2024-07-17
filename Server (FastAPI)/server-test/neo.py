from py2neo import Graph

graph = Graph("bolt://localhost:7687", auth=("neo4j", "12345678"))

def borrow_or_return(idA, idB) -> bool:
    query = """
    MATCH (a:User {id: $idA})-[:BORROWED]->(b:Book {id: $idB})
    return b
    """
    cursor = graph.run(query, idA=idA, idB=idB)
    if len(cursor.data()) == 0:
        query = """
        MATCH (a:User {id: $idA}), (b:Book {id: $idB})
        CREATE (a)-[:BORROWED]->(b)
        """
        graph.run(query, idA=idA, idB=idB)
        return True
    else:
        query = """
        MATCH (a:User {id: $idA})-[r:BORROWED]->(b:Book {id: $idB})
        DELETE r
        """
        graph.run(query, idA=idA, idB=idB)
        return False
