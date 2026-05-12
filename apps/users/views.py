from __future__ import annotations

from typing import TYPE_CHECKING

from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views.generic import DetailView
from django.views.generic import RedirectView
from django.views.generic import UpdateView
from django.views.generic import ListView
from django.views.generic import CreateView
from django.views.generic import DeleteView
from django.views.generic import FormView
from django.urls import reverse_lazy
from django.contrib.auth.forms import AdminPasswordChangeForm
from django.shortcuts import get_object_or_404

from apps.users.models import User
from apps.users.forms import UserCreateForm, UserUpdateAdminForm

if TYPE_CHECKING:
    from django.db.models import QuerySet


class UserDetailView(LoginRequiredMixin, DetailView):
    model = User
    slug_field = "id"
    slug_url_kwarg = "id"


user_detail_view = UserDetailView.as_view()


class UserUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = User
    fields = ["name"]
    success_message = _("Information successfully updated")

    def get_success_url(self) -> str:
        assert self.request.user.is_authenticated  # type guard
        return self.request.user.get_absolute_url()

    def get_object(self, queryset: QuerySet | None = None) -> User:
        assert self.request.user.is_authenticated  # type guard
        return self.request.user


user_update_view = UserUpdateView.as_view()


class UserRedirectView(LoginRequiredMixin, RedirectView):
    permanent = False

    def get_redirect_url(self) -> str:
        return reverse("users:detail", kwargs={"pk": self.request.user.pk})


user_redirect_view = UserRedirectView.as_view()


class UserListView(LoginRequiredMixin, ListView):
    model = User
    template_name = "users/user_list.html"
    context_object_name = "users"


user_list_view = UserListView.as_view()


class UserCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    model = User
    form_class = UserCreateForm
    template_name = "users/user_form_admin.html"
    success_message = _("User successfully created")
    success_url = reverse_lazy("users:list")


user_create_view = UserCreateView.as_view()


class UserUpdateAdminView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = User
    form_class = UserUpdateAdminForm
    template_name = "users/user_form_admin.html"
    success_message = _("User successfully updated")
    success_url = reverse_lazy("users:list")


user_update_admin_view = UserUpdateAdminView.as_view()


class UserDeleteView(LoginRequiredMixin, SuccessMessageMixin, DeleteView):
    model = User
    template_name = "users/user_confirm_delete.html"
    success_message = _("User successfully deleted")
    success_url = reverse_lazy("users:list")


user_delete_view = UserDeleteView.as_view()


class UserPasswordChangeView(LoginRequiredMixin, SuccessMessageMixin, FormView):
    template_name = "users/user_password_change.html"
    form_class = AdminPasswordChangeForm
    success_message = _("User password successfully changed")
    success_url = reverse_lazy("users:list")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = get_object_or_404(User, pk=self.kwargs['pk'])
        return kwargs

    def form_valid(self, form):
        form.save()
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['target_user'] = get_object_or_404(User, pk=self.kwargs['pk'])
        return context


user_password_change_view = UserPasswordChangeView.as_view()
