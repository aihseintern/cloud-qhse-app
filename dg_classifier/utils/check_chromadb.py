import chromadb

class CheckChromadb:
    def __init__(self):
        self.client = chromadb.PersistentClient(path='MSDS_vectorDB')
        
        # Get the list of collections
        collections = self.client.list_collections()
        
        # Check if the number of collections exceeds 5
        if len(collections) > 10:
            # Delete the first (oldest) collection
            oldest_collection = collections[0].name
            self.client.delete_collection(oldest_collection)
            print(f"Deleted oldest collection: {oldest_collection}")
        
        # Print all current collections
        for i, item in enumerate(self.client.list_collections()):
            print(f"Collection {i+1}: {item.name}")
