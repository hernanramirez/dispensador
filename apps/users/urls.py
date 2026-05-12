from django.urls import path

from .views import user_detail_view
from .views import user_redirect_view
from .views import user_update_view
from .views import user_list_view
from .views import user_create_view
from .views import user_update_admin_view
from .views import user_delete_view
from .views import user_password_change_view

app_name = "users"
urlpatterns = [
    path("list/", view=user_list_view, name="list"),
    path("create/", view=user_create_view, name="create"),
    path("<int:pk>/update/", view=user_update_admin_view, name="update_admin"),
    path("<int:pk>/delete/", view=user_delete_view, name="delete"),
    path("<int:pk>/password/", view=user_password_change_view, name="password"),
    path("~redirect/", view=user_redirect_view, name="redirect"),
    path("~update/", view=user_update_view, name="update"),
    path("<int:pk>/", view=user_detail_view, name="detail"),
]
