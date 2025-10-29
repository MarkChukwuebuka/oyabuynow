# search/documents.py
from elasticsearch_dsl import Document, Text, Keyword, Float, analyzer


text_analyzer = analyzer(
    'autocomplete',
    tokenizer="standard",
    filter=["lowercase", "asciifolding", "edge_ngram"]
)

class ProductDocument(Document):
    name = Text(analyzer=text_analyzer, fields={'raw': Keyword()})
    description = Text(analyzer=text_analyzer)
    category = Text(analyzer=text_analyzer)
    brand = Text(analyzer=text_analyzer)
    tags = Text(analyzer=text_analyzer)
    price = Float()
    discounted_price = Float()
    slug = Keyword()

    class Index:
        name = 'products'

    def save(self, **kwargs):
        self.meta.id = self.slug
        return super().save(**kwargs)

class CategoryDocument(Document):
    name = Text(analyzer=text_analyzer, fields={'raw': Keyword()})

    class Index:
        name = 'categories'

class BrandDocument(Document):
    name = Text(analyzer=text_analyzer, fields={'raw': Keyword()})

    class Index:
        name = 'brands'

class TagDocument(Document):
    name = Text(analyzer=text_analyzer, fields={'raw': Keyword()})

    class Index:
        name = 'tags'
