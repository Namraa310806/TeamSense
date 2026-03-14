from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from django.http import HttpResponseRedirect
from employees.models import Employee
from .models import Feedback, Document
from .serializers import FeedbackSerializer
from accounts.permissions import IsHR, IsExecutive
from .tasks import parse_csv_task, ingest_zoho_data
from .zoho_connector import ZohoOAuth


@api_view(['POST'])
@permission_classes([IsHR, IsExecutive])
def upload_feedback_csv(request):
    if 'file' not in request.FILES:
        return Response({'error': 'No file'}, status=status.HTTP_400_BAD_REQUEST)
    file = request.FILES['file']
    parse_csv_task.delay(file.name, request.user.id)
    return Response({'status': 'processing', 'file': file.name})


@api_view(['GET'])
def feedback_list(request):
    feedbacks = Feedback.objects.select_related('employee').all()
    return Response(FeedbackSerializer(feedbacks, many=True).data)


@api_view(['GET'])
def zoho_auth(request):
    auth_url = f'https://accounts.zoho.com/oauth/v2/auth?scope=ZohoPeople.employees.ALL&client_id=1000.IWODHOTGDFG94MSNMF0G75QX8YE77V&response_type=token&access_type=offline&redirect_uri=http://localhost:8000/api/ingestion/zoho-callback/'
    return HttpResponseRedirect(auth_url)


@api_view(['GET'])
def zoho_callback(request):
    code = request.GET.get('code')
    if code:
        token_data = ZohoOAuth.get_token(code)
        access_token = token_data.get('access_token')
        if access_token:
            ingest_zoho_data.delay(access_token)
            return Response({'status': 'Ingestion queued', 'token': access_token[:20] + '...'})
    return Response({'error': 'Auth failed'}, status=status.HTTP_400_BAD_REQUEST)

