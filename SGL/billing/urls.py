from django.urls import path
from .views import (
    BillListView,
    BillDetailView,
    BillUpdateView,
    print_bill,
    mark_bill_as_paid,
    BillCreateView,
    get_patient_analyses, PatientQRCodeView
)

app_name = 'billing'

urlpatterns = [
    path('', BillListView.as_view(), name='bill_list'),
    path('bill/<int:pk>/', BillDetailView.as_view(), name='bill_detail'),
    path('bill/<int:pk>/update/', BillUpdateView.as_view(), name='bill_update'),
    path('bill/<int:pk>/print/', print_bill, name='print_bill'),
    path('bill/<int:pk>/paid/', mark_bill_as_paid, name='mark_paid'),
    path('bill/create/', BillCreateView.as_view(), name='bill_create'),
    path('get-analyses/', get_patient_analyses, name='get_patient_analyses'),
path('api/patients/<int:pk>/qr/', PatientQRCodeView.as_view(), name='patient_qr_code'),


]