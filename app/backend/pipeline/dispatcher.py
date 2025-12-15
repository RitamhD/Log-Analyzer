from app.backend.embeddings.encoder import encode_messages



def dispatch_for_analysis(events: list[dict]):
    """
    Temporary stub.
    This will:-
    1. generate embeddings
    2. run DBSCAN
    3. assign severity
    4. persist results
    """
    
    texts = [e["clean_message"] for e in events]
    embeddings = encode_messages(texts)

    for event, vector in zip(events, embeddings):
        event["embedding"] = vector
    print(f"Received batch of {len(events)} events for analysis")
    # Later DBSCAN will consume events with embeddings
