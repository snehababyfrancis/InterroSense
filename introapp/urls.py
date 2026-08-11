from django.urls import path
from . import views


urlpatterns = [
    path("", views.index, name="index"),
    path("police/", views.police, name="police"),
    path("reports/", views.reports, name="reports"),
    path("generate_questions/", views.generate_questions, name="generate_questions"),
    path("save_questions/", views.save_questions, name="save_questions"),
    path("load_questions/", views.load_questions, name="load_questions"),
    path("accused/", views.accused, name="accused"),
    path("collect_fst", views.collect_fst, name="collect_fst"),
    path("analyze_results/", views.analyze_results, name="analyze_results"),
    path("reports/", views.reports, name="report"),

]

