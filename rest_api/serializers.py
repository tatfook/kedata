
from datetime import datetime

from rest_framework import serializers
from brain.snippet import Snippet
from brain.mind import Mind
from brain. config import getlogger

log = getlogger(__name__)


class SnippetSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    title = serializers.CharField(required=False, allow_blank=True, max_length=100)
    desc = serializers.CharField(style={'base_template': 'textarea.html'})
    vote = serializers.IntegerField(required=True)    
    private = serializers.BooleanField(default=False ) #TODO: default
    url = serializers.URLField(required=False, allow_null=True)
    tags = serializers.ListField(default=[])
    attachment = serializers.CharField(required=False, allow_null=True)    
    children = serializers.ListField(default=[])
    # context = 
    in_frames = serializers.ListField(read_only=True, required=False, source='get_in_frames')    
    # annots = serializers.CharField(read_only=True, required=False)     
    init_time = serializers.DateTimeField(read_only=True, default=datetime.now().isoformat(), initial=datetime.now().isoformat())
    update_time = serializers.DateTimeField(read_only=True, default=datetime.now().isoformat(), initial=datetime.now().isoformat())

    def create(self, validated_data):
        """
        Create and return a new `Snippet` instance, given the validated data.
        """
        log.info('creating a new snippet...')
        username = self.context.get('username')
        mind = Mind(username) #TODO:
        log.debug('validated_data: %s', validated_data)
        return mind.create_snippet(**validated_data)

    def update(self, instance, validated_data):
        """
        Update and return an existing `Snippet` instance, given the validated data.
        """
        instance.title = validated_data.get('title', instance.title)
        instance.desc = validated_data.get('desc', instance.desc)
        instance.vote = validated_data.get('vote', instance.vote)
        instance.private = validated_data.get('private', instance.private)        
        instance.url = validated_data.get('url', instance.url)
        instance.tags = validated_data.get('tags', instance.tags)
        instance.attachment = validated_data.get('attachment', instance.attachment)
        instance.children = validated.get('children', instance.children)
        instance.init_time = validated_data.get('init_time', instance.init_time)
        instance.save()
        return instance


class TagSerializer(serializers.Serializer):    
    name = serializers.CharField(required=False, allow_blank=False, max_length=100)
    desc = serializers.CharField(required=False, style={'base_template': 'textarea.html'})    
    private = serializers.BooleanField(default=False) #TODO: default    
    in_tagtrees = serializers.ListField(read_only=True, required=False, source='get_in_tagtrees')   
    init_time = serializers.DateTimeField(read_only=True, default=datetime.now().isoformat(), initial=datetime.now().isoformat())
    update_time = serializers.DateTimeField(read_only=True, default=datetime.now().isoformat(), initial=datetime.now().isoformat())

    def create(self, validated_data):
        """
        Create and return a new `Snippet` instance, given the validated data.
        """
        log.info('creating a new tag...')
        username = self.context.get('username')
        mind = Mind(username) #TODO:
        log.debug('validated_data: %s', validated_data)
        return mind.create_tag(**validated_data)

    def update(self, instance, validated_data):
        """
        Update and return an existing `Snippet` instance, given the validated data.
        """
        
        instance.desc = validated_data.get('desc', instance.desc)        
        instance.private = validated_data.get('private', instance.private)                
        instance.init_time = validated_data.get('init_time', instance.init_time)        
        #allow the post form having no field "name"
        if validated_data.get('name'):
            log.info('Updating the tag name...')
            username = self.context.get('username')
            mind = Mind(username) 
            #TODO:support updating name together with other fields at the same time
            mind.update_tag_name(instance.name, validated_data.get('name'))
        else:
            log.info('Updating the tag...')
            #name is not in the post data. 
            instance.save()    
        return instance



class FrameSerializer(SnippetSerializer):
    id = serializers.IntegerField(read_only=True)
    title = serializers.CharField(required=False, allow_blank=True, max_length=100)
    desc = serializers.CharField(style={'base_template': 'textarea.html'})
    vote = serializers.IntegerField(required=True)    
    private = serializers.BooleanField(default=False ) #TODO: default    
    tags = serializers.ListField(default=[])
    attachment = serializers.CharField(required=False, allow_null=True)    
    children = serializers.ListField(default=[])
    in_frames = serializers.ListField(read_only=True, required=False, source='get_in_frames')    
    # annots = serializers.CharField(read_only=True, required=False)     
    init_time = serializers.DateTimeField(read_only=True, default=datetime.now().isoformat(), initial=datetime.now().isoformat())
    update_time = serializers.DateTimeField(read_only=True, default=datetime.now().isoformat(), initial=datetime.now().isoformat())



    def create(self, validated_data):
        """
        Create and return a new `Frame` instance, given the validated data.
        """
        log.info('creating a new frame...')
        username = self.context.get('username')
        mind = Mind(username) #TODO:
        log.debug('validated_data: %s', validated_data)
        return mind.create_frame(**validated_data)

    def update(self, instance, validated_data):
        """
        Update and return an existing `Snippet` instance, given the validated data.
        """
        instance.title = validated_data.get('title', instance.title)
        instance.desc = validated_data.get('desc', instance.desc)
        instance.vote = validated_data.get('vote', instance.vote)
        instance.private = validated_data.get('private', instance.private)        
        # instance.url = validated_data.get('url', instance.url)
        instance.tags = validated_data.get('tags', instance.tags)
        instance.attachment = validated_data.get('attachment', instance.attachment)
        instance.children = validated.get('children', instance.children)
        instance.init_time = validated_data.get('init_time', instance.init_time)
        instance.save()
        return instance