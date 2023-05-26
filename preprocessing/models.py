from django.db import models

# Create your models here.
class UnprocessedData(models.Model):
    full_text = models.TextField()
    username = models.TextField()
    created_at = models.TextField()
    user_created_at = models.TextField()
    class Meta:
        db_table = "unprocessed_data"