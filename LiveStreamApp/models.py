from django.db import models
from django.urls import reverse

class Session(models.Model):
    sessId = models.CharField(max_length=30, primary_key=True)
    createTime = models.DateTimeField(auto_now=True)
    startTime = models.DateTimeField(auto_now=False)
    interval = models.IntegerField(blank=False, null=False)
    balance = models.FloatField(default=0)
    isActive = models.BooleanField(default=False)
    
    def __str__(self):
        return self.sessId

    def get_absolute_url(self):
        return reverse("Sessions_detail", kwargs={"pk": self.pk})

class Chat(models.Model):
    sessId = models.ForeignKey(Session, on_delete=models.CASCADE, related_name="ofSession")
    msg = models.CharField(max_length=1000)
    sender = models.CharField(max_length=100)
    recvTime = models.DateTimeField(auto_now=True)
