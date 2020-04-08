from django.db import models
from django.urls import reverse

COST_PER_HOUR = 100
class Session(models.Model):
    sessId = models.CharField(max_length=30, primary_key=True)
    createTime = models.DateTimeField(auto_now=True)
    startTime = models.DateTimeField(auto_now=False)
    interval = models.IntegerField(blank=False, null=False)
    balance = models.FloatField(default=0)
    isActive = models.BooleanField(default=False)

    def save(self):
        # self.interval += 15
        # self.balance -= (self.interval/60)*COST_PER_HOUR
        super(Session, self).save()

    def __str__(self):
        return self.sessId

    def get_absolute_url(self):
        return reverse("Sessions_detail", kwargs={"pk": self.pk})

class Chat(models.Model):
    sessId = models.ForeignKey(Session, on_delete=models.CASCADE, related_name="chat_ofSession")
    msg = models.CharField(max_length=1000)
    sender = models.CharField(max_length=100)
    recvTime = models.DateTimeField(auto_now=True)

class Peer(models.Model):
    sess = models.ForeignKey(Session, on_delete=models.CASCADE, related_name='peer_inSess')
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=100)
    clss = models.CharField(max_length=10, default="")
    section = models.CharField(max_length=20, default="")
    mob = models.CharField(max_length=10)
    who = models.CharField(max_length=10)
    login = models.DateTimeField(auto_now=True)
    logout = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name
    