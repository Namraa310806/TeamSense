from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from ai_services.embedding_service import EmbeddingService
from ai_services.vector_store import FaissVectorStore

@api_view(['POST'])
def ai_query(request):
    """RAG-based AI query endpoint.

    Input:
        query: str - the question to ask
        employee_id: int (optional) - filter to specific employee
    """
    query = request.data.get('query', '')
    employee_id = request.data.get('employee_id')

    if not query:
        return Response({'error': 'Query is required'}, status=status.HTTP_400_BAD_REQUEST)

    from .rag import rag_query
    result = rag_query(query, employee_id=employee_id)

    return Response(result)

from ai_services.embedding_service import EmbeddingService
from ai_services.vector_store import FaissVectorStore
from rest_framework.views import APIView

# Example: 384 for all-MiniLM-L6-v2
EMBEDDING_DIM = 384
VECTOR_INDEX_PATH = 'faiss.index'
META_PATH = 'faiss_meta.pkl'

embedding_service = EmbeddingService()
vector_store = FaissVectorStore(dim=EMBEDDING_DIM, index_path=VECTOR_INDEX_PATH, meta_path=META_PATH)

class SemanticSearchAPI(APIView):
    def post(self, request):
        query = request.data.get('query')
        if not query:
            return Response({'error': 'Query is required.'}, status=status.HTTP_400_BAD_REQUEST)
        query_vec = embedding_service.embed_text(query)
        results = vector_store.search(query_vec, top_k=5)
        return Response({'results': results})
