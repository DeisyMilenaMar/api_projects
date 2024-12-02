from django.urls import path

from binance_trader_api.views import TransactionCreateView
from binance_trader_api.views import UserCreateView
from binance_trader_api.views import UserGetView

app_name = "binance_trader_api"

urlpatterns = [
    path(
        "transactions/create/",
        TransactionCreateView.as_view(),
        name="transactions_create",
    ),
    path("create/", UserCreateView.as_view(), name="user-create"),
    path("get/", UserGetView.as_view(), name="user-get"),
]
