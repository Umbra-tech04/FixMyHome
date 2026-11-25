from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.test import RequestFactory, TestCase
from django.urls import reverse
from django.views import View

from accounts.models import Role, User
from accounts.permissions import RoleRequiredMixin, role_required


@role_required(Role.MASTER, Role.SUPPORT)
def staff_view(request):
    return HttpResponse("ok")


class StaffView(RoleRequiredMixin, View):
    allowed_roles = (Role.MASTER, Role.SUPPORT)

    def get(self, request):
        return HttpResponse("ok")


class RolePermissionTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def request_as(self, user):
        request = self.factory.get("/vedett/")
        request.user = user
        return request

    def user_with_role(self, role):
        user, _ = User.objects.get_or_create(email=f"{role}@example.com", defaults={"name": role, "role": role})
        return user

    def views(self):
        return {"decorator": staff_view, "mixin": StaffView.as_view()}

    def test_anonymous_is_redirected_to_login_with_next(self):
        for name, view in self.views().items():
            with self.subTest(view=name):
                response = view(self.request_as(AnonymousUser()))
                self.assertEqual(response.status_code, 302)
                self.assertEqual(response["Location"], f"{reverse('login')}?next=/vedett/")

    def test_wrong_role_gets_403(self):
        for name, view in self.views().items():
            with self.subTest(view=name):
                with self.assertRaises(PermissionDenied):
                    view(self.request_as(self.user_with_role(Role.USER)))

    def test_allowed_role_passes(self):
        for role in (Role.MASTER, Role.SUPPORT):
            for name, view in self.views().items():
                with self.subTest(role=role, view=name):
                    response = view(self.request_as(self.user_with_role(role)))
                    self.assertEqual(response.status_code, 200)
