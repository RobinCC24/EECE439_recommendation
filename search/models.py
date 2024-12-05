from django.db import models

class Surgeon(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    specialty = models.CharField(max_length=100)
    city = models.CharField(max_length=100)
    address = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=15)
    email = models.EmailField()
    fees = models.DecimalField(max_digits=10, decimal_places=2)
    rating = models.DecimalField(max_digits=3, decimal_places=2, null=True, blank=True)  # Rating out of 5
    hospital_name = models.CharField(max_length=255)
    available_hours = models.CharField(max_length=255)

def __str__(self):
        return f'{self.first_name} {self.last_name}, {self.specialty}'