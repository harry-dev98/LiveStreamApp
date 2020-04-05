from django.db import models

def dir(instance, filename):
    # file will be uploaded to MEDIA_ROOT/user_<id>/<filename>
    return 'ocr/class_{0}/{1}'.format(instance._class, filename)

class OCRData(models.Model):
    # recievedImg = models.ImageField(upload_to=dir)
    url = models.CharField(max_length=200, blank=False, null=False, unique=True)
    timestamp = models.DateTimeField(auto_now=True)
    _class = models.IntegerField(help_text="mandatory to tell the class")
    section = models.CharField(max_length=50, help_text="mandatory to tell the section")

    def __str__(self):
        return "{}{}".format(self._class, self.section)
    