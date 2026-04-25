from rest_framework import serializers
from .models import Project, ApiGroup


class ApiGroupSerializer(serializers.ModelSerializer):
    children = serializers.SerializerMethodField()

    class Meta:
        model = ApiGroup
        fields = ['id', 'project', 'name', 'description', 'parent', 'children', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']

    def get_children(self, obj):
        children = obj.children.all()
        return ApiGroupSerializer(children, many=True).data


class ApiGroupSimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = ApiGroup
        fields = ['id', 'name']


class ProjectSerializer(serializers.ModelSerializer):
    groups = ApiGroupSimpleSerializer(many=True, read_only=True)
    api_count = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = ['id', 'name', 'description', 'base_url', 'groups', 'api_count', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']

    def get_api_count(self, obj):
        return obj.apis.count()
