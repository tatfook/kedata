

import json

from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from django.conf import settings

from rest_framework import viewsets

from brain.snippet import Snippet
from brain.mind import Mind
from brain.storage import GitlabEsStorage
from .serializers import SnippetSerializer
from django.http import Http404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status


class SnippetList(APIView):
    """
    List all snippets, or create a new snippet.
    """

    def get(self, request, username, format=None):
        mind = Mind(username)
        snippets = mind.get_snippets()
        serializer = SnippetSerializer(snippets, context={'username':username}, many=True)
        return Response(serializer.data)

    def post(self, request, username, format=None):
        serializer = SnippetSerializer(data=request.data, context={'username':username})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



class SnippetDetail(APIView):
    """
    Retrieve, update or delete a snippet instance.
    """                

    def get_object(self, username, pk):
        print('get object')
        mind = Mind(username)
        try:                        
            return mind.get_snippet(pk)
        except Snippet.DoesNotExist:
            raise Http404

    def get(self, request, username, pk, format=None):
        snippet = self.get_object(username, pk)
        serializer = SnippetSerializer(snippet, context={'username':username})
        return Response(serializer.data)

    def put(self, request, username, pk, format=None):
        snippet = self.get_object(username, pk)
        serializer = SnippetSerializer(snippet, data=request.data, context={'username':username})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, username, pk, format=None):
        snippet = self.get_object(username, pk)
        snippet.discard()
        return Response(status=status.HTTP_204_NO_CONTENT)        



@csrf_exempt
def gitlab_hook(request):
    if request.method == 'POST' and request.content_type == 'application/json':
        print('Received the push event from gitlab.')
        push_event = json.loads(request.body)
        project_id = push_event.get('project_id', 0)
        username = GitlabEsStorage.get_project_username(project_id)
        storage = GitlabEsStorage(username)
        project_id = storage.gitlab_hook(push_event)
        return HttpResponse(str(project_id),  content_type="text/plain")
    print('Request not understood and not processed.')
    return HttpResponse('Request ignored!',  content_type="text/plain")



