from django.urls import path
from . import views

urlpatterns = [
    path('surgeons/', views.surgeon_list, name='surgeon-list'),
    path('surgeons/new/', views.surgeon_create, name='surgeon-create'),
    path('surgeons/<int:pk>/edit/', views.surgeon_update, name='surgeon-update'),
    path('surgeons/<int:pk>/delete/', views.surgeon_delete, name='surgeon-delete'),
    path('bulk-upload/', views.bulk_upload_view, name='bulk-upload'),
    path('surgeons/recommendations/', views.surgeon_recommendations, name='surgeon-recommendations'),
]
