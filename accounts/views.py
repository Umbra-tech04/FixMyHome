from django.contrib.auth import login
from django.shortcuts import redirect, render

from accounts.forms import RegistrationForm


def register(request):
    form = RegistrationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        # Több backend van (axes + ModelBackend), ezért meg kell nevezni, melyik "léptette be".
        login(request, user, backend="django.contrib.auth.backends.ModelBackend")
        return redirect("home")
    return render(request, "accounts/register.html", {"form": form})
