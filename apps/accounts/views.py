from rest_framework import permissions, response, views

from .serializers import AccountMeSerializer


class AccountMeView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return response.Response(AccountMeSerializer(request.user).data)
