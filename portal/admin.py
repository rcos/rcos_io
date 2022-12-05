from django.contrib import admin

from .models import *

admin.site.site_header = "RCOS IO Administration"
# admin.site.site_title = ""

# Register your models here.

admin.site.register(Semester)
admin.site.register(User)
admin.site.register(Project)
admin.site.register(Enrollment)

