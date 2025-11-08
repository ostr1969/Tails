{
  "query": {
    "query_string": {
      "query": "Effects AND Wearable",
      "fields": [
        "file.filename",
        "dwg_content.content",
        "dwg_content.layers",
        "dwg_content.contentrev",
        "dwg_content.imagenames",
        "content",
        "file.filename.text"
      ]
    }
  },
  "highlight": {
    "fields": {
      "content": {},
      "dwg_content.layers": {},
      "dwg_content.content": {},
      "dwg_content.contentrev": {},
      "dwg_content.imagenames": {},
      "file.filename.text": {},
      "file.filename": {}
    },
    "pre_tags": [
      "<em class=\"highlight\">"
    ],
    "post_tags": [
      "</em>"
    ]
  },
  "size": 1000
}