
DELETE /articles

PUT /articles
{
  "settings": {
    "analysis": {
      "filter": {
        "english_stop": {
          "type": "stop",
          "stopwords": "_english_"
        },
        "english_stemmer": {
          "type": "stemmer",
          "language": "english"
        },
        "synonym_filter": {
          "type": "synonym",
          "lenient": true,
          "synonyms": [
           "ai, artificial intelligence",
            "usa, united states, america",
            "ml, machine learning",
            "nlp, natural language processing"
          ]
        }
      },
      "analyzer": {
        "custom_english": {
          "tokenizer": "standard",
          "filter": [
            "lowercase",
            "english_stop",
            "english_stemmer",
            "synonym_filter"
          ]
        }
      }
    }
  },
  "mappings": {
    "properties": {
      "title": {
        "type": "text",
        "analyzer": "custom_english"
      },
      "content": {
        "type": "text",
        "analyzer": "custom_english"
      }
    }
  }
}
#bulk insert sample documents

PUT /articles/_doc/1
{ "title": "AI in Healthcare: Revolutionizing Patient Diagnosis", "content": "Artificial intelligence and machine learning are transforming healthcare. AI-based models help doctors predict diseases and personalize treatments.", "author": "Dr. Sarah Nguyen" }
PUT /articles/_doc/2
{ "title": "Natural Language Processing for Customer Support", "content": "NLP systems can understand and respond to user queries automatically, improving efficiency in customer service platforms.", "author": "James Patel" }
PUT /articles/_doc/3
{ "title": "Quantum Computing and the Future of AI", "content": "Quantum computers could significantly accelerate AI algorithms and complex simulations.", "author": "Maria Gonzalez" }
PUT /articles/_doc/4
{ "title": "The United States Pushes for Advanced AI Regulations", "content": "America is proposing new rules to ensure ethical use of artificial intelligence technologies.", "author": "Ethan Brooks" }
PUT /articles/_doc/5
{ "title": "Machine Learning Models for Predictive Analytics", "content": "ML models can analyze big data to make accurate business forecasts and recommendations.", "author": "Lina Park" }
PUT /articles/_doc/6
{ "title": "Neural Networks Explained", "content": "A neural network is a computational model inspired by how biological neurons work in the human brain.", "author": "Arjun Mehta" }
PUT /articles/_doc/7
{ "title": "Data Science Trends 2025", "content": "Data science continues to evolve with deep learning, NLP, and automation being key trends.", "author": "Sophia Rossi" }

GET /articles/_count

#basic search query
GET /articles/_search
{
  "query": {
    "match": {
      "content": "machine learning in healthcare "
    }
  }
}
#match phrase query
GET /articles/_search
{
  "query": {
    "match_phrase": {
      "content": {
        "query": "artificial intelligence technologies",
        "slop": 2
      }
    }
  }
}
#fuzzy query
GET /articles/_search
{
  "query": {
    "match": {
      "content": {
        "query": "inteligence",
        "fuzziness": "AUTO"
      }
    }
  }
}
#synonym query
GET /articles/_search
{
  "query": {
    "match": {
      "content": "usa"
    }
  }
}
#wildcard query
GET /articles/_search
{
  "query": {
    "wildcard": {
      "content": {
        "value": "americ*"
      }
    }
  }
}
#autocomplete using edge n-grams
GET /articles/_search
{
  "query": {
    "prefix": {
      "title": {
        "value": "ameri"
      }
    }
  }
}
#multi-match query
GET /articles/_search
{
  "query": {
    "multi_match": {
      "query": "data science trends",
      "fields": ["title", "content"]
    }
  }
}
#boosting query
GET /articles/_search
{
  "query": {
    "multi_match": {
      "query": "AI regulations",
      "fields": ["title^2", "content^3"]
    }
  }
}
#more like this query
GET /articles/_search
{
  "query": {
    "more_like_this": {
      "fields": ["content"],
      "like": "machine learning for disease prediction",
     "min_term_freq": 1,
      "min_doc_freq": 1,
      "max_query_terms": 25
    }
  }
}
#more like this using document id
GET /articles/_search
{
  "query": {
    "more_like_this": {
      "fields": ["content"],
      "like": [
        { "_index": "articles", "_id": "1" }
      ],
      "min_term_freq": 1,
      "min_doc_freq": 1
    }
  }
}
#analyze API to see how text is tokenized and analyzed
GET /articles/_analyze
{
  "field": "content",
  "text": "machine learning for disease prediction"
}