from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import api_view
from .models import Account, Destination
from .serializers import AccountSerializer, DestinationSerializer
import requests

class AccountViewSet(viewsets.ModelViewSet):
    queryset = Account.objects.all()
    serializer_class = AccountSerializer

    def destroy(self, request, *args, **kwargs):
        account = self.get_object()
        account.destinations.all().delete()
        return super().destroy(request, *args, **kwargs)

class DestinationViewSet(viewsets.ModelViewSet):
    queryset = Destination.objects.all()
    serializer_class = DestinationSerializer

    def get_queryset(self):
        account_id = self.request.query_params.get('account_id')
        if account_id:
            return self.queryset.filter(account__account_id=account_id)
        return self.queryset

@api_view(['POST'])
def incoming_data(request):
    token = request.headers.get('CL-X-TOKEN')
    if not token:
        return Response({"error": "Un Authenticate"}, status=status.HTTP_401_UNAUTHORIZED)

    try:
        account = Account.objects.get(app_secret_token=token)
    except Account.DoesNotExist:
        return Response({"error": "Un Authenticate"}, status=status.HTTP_401_UNAUTHORIZED)

    data = request.data
    destinations = account.destinations.all()

    for destination in destinations:
        headers = destination.headers
        method = destination.http_method.upper()
        url = destination.url

        if method == 'GET':
            response = requests.get(url, headers=headers, params=data)
        elif method in ['POST', 'PUT']:
            response = requests.request(method, url, headers=headers, json=data)
        else:
            continue

        if response.status_code != 200:
            return Response({"error": "Failed to send data"}, status=status.HTTP_400_BAD_REQUEST)

    return Response({"status": "Data sent successfully"}, status=status.HTTP_200_OK)
