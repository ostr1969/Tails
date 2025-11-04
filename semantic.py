from elasticsearch import Elasticsearch
import time
es = Elasticsearch("http://localhost:9200")

index_name = "semantic_offline"

# Create index with dense_vector field
mapping = {
    "mappings": {
        "properties": {
            "text": {"type": "text"},
            "embedding": {"type": "dense_vector", "dims": 384}
        }
    }
}

# Delete old index if exists
if es.indices.exists(index=index_name):
    es.indices.delete(index=index_name)

es.indices.create(index=index_name, body=mapping)
print("Index created ✅")
start = time.time()
from sentence_transformers import SentenceTransformer
#C:\Users\barako\.cache\huggingface\hub
#model = SentenceTransformer("all-MiniLM-L6-v2")  # runs fully local
model = SentenceTransformer("C:\\Users\\barako\\.cache\\huggingface\\hub\\models--sentence-transformers--all-MiniLM-L6-v2\\snapshots\\c9745ed1d9f207416be6d2e6f8de32d1f16199bf")
print("offline Model loaded ✅ | Time taken: {:.4f} seconds".format(time.time() - start))
texts = [
    "A doctor examines patients and prescribes medication to treat illnesses. They often work in hospitals, clinics, or private practices, collaborating with nurses and specialists to ensure the best possible recovery for each patient through diagnosis, treatment, and prevention.",

    "Teachers guide students through new concepts, helping them understand complex ideas and develop critical thinking skills. In classrooms, they use lessons, exercises, and discussions to encourage curiosity and motivate learners to reach their full potential academically and personally.",

    "Pilots are responsible for flying aircraft safely between destinations. They monitor weather, communicate with air traffic control, and navigate using instruments. A pilot’s training includes emergency procedures and flight simulations to ensure passengers and crew arrive securely.",

    "Software engineers design and build applications that power modern life. They write code, test functionality, and solve technical challenges. Collaboration with designers and product managers ensures systems are efficient, reliable, and user-friendly.",

    "Forests are crucial ecosystems that absorb carbon dioxide, protect biodiversity, and regulate climate. Deforestation threatens wildlife habitats and accelerates global warming. Conservation programs aim to restore natural balance through sustainable management and reforestation.",

    "Investors analyze market trends, assess risks, and allocate capital to achieve profitable returns. Diversifying portfolios across stocks, bonds, and alternative assets helps reduce volatility while maintaining long-term growth potential in an ever-changing economy.",

    "Athletes train rigorously to improve strength, endurance, and skill. Competitive sports promote teamwork, discipline, and mental focus. Whether individual or team-based, athletic performance reflects dedication, strategy, and continuous self-improvement.",

    "Artists express emotion and ideas through painting, sculpture, or digital media. Creativity allows them to communicate visually what words often cannot. Art inspires reflection, challenges perception, and connects people across cultures and generations.",

    "Scientists conduct experiments to test hypotheses and discover new knowledge. Through careful observation, measurement, and analysis, they uncover patterns that explain natural phenomena. Scientific progress relies on curiosity, precision, and peer review.",

    "Farmers cultivate crops and raise livestock to supply food for communities. Modern agriculture combines technology, irrigation, and soil management to increase productivity while balancing sustainability and environmental protection."
]


# Create and store embeddings
for i, text in enumerate(texts):
    start = time.time()
    word_count = len(text.split())
    vector = model.encode(text).tolist()    
    es.index(index=index_name, id=i+1, document={"text": text, "embedding": vector})
    print(f"Indexing document {i+1} | Word count: {word_count} | Time taken: {time.time() - start:.4f} seconds")

es.indices.refresh(index=index_name)
print("Documents indexed ✅")

query = "tennis elbow treatment exercises"

query_vector = model.encode(query).tolist()

response = es.search(
    index=index_name,
    size=3,
    query={
        "script_score": {
            "query": {"match_all": {}},
            "script": {
                "source": "cosineSimilarity(params.query_vector, 'embedding') + 1.0",
                "params": {"query_vector": query_vector}
            }
        }
    }
)
print("search query:", query)
for hit in response["hits"]["hits"]:
    print(f"Score: {hit['_score']:.4f} | Text: {hit['_source']['text']}")