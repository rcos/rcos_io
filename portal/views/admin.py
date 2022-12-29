from csv import DictReader
from io import TextIOWrapper
from portal.forms import UploadSubmittyDataForm
from django.shortcuts import render


def upload_submitty_data(request):
    if request.method == "POST":
        form = UploadSubmittyDataForm(request.POST, request.FILES)
        if form.is_valid():
            print(form)
            file = request.FILES["submitty_csv"]

            users = []
            rows = TextIOWrapper(file, encoding="utf-8", newline="")
            for row in DictReader(rows):
                users.append(row)
            

    else:
        form = UploadSubmittyDataForm()
    
    return render(request, "portal/admin/upload.html", {"form": form})