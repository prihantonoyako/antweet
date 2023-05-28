from rest_framework import serializers
from preprocessing.models import UnprocessedData

class PreProcessSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    nama_akun = serializers.CharField(source='username')
    komentar = serializers.CharField(source='full_text')
    tanggal = serializers.CharField(source='created_at')
    # user_created_at = serializers.CharField()

class AdjustmentSerializer(serializers.Serializer):
    # id = serializers.IntegerField(read_only=True)
    text = serializers.CharField()
    
class ClassifierSerializer(serializers.Serializer):
    label = serializers.CharField()
    
    