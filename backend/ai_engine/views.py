from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status


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
