from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.garage_dashboard, name='garage_dashboard'),
    path('profile/', views.garage_profile, name='garage_profile'),
    path('add-service/', views.add_service, name='add_service'),
    path('delete-service/<int:pk>/', views.delete_service, name='delete_service'),

     # ✅ Service Type Management

    path('service-types/', views.service_type_list, name='service_type_list'),
    path('service-types/add/', views.add_service_type, name='add_service_type'),
    path('service-types/<int:pk>/edit/', views.edit_service_type, name='edit_service_type'),
    path('service-types/<int:pk>/delete/', views.delete_service_type, name='delete_service_type'),

]


