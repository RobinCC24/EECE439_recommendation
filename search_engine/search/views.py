# search/views.py
from django.core.paginator import Paginator
import pandas as pd
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from .models import Surgeon
from .forms import CSVUploadForm, SurgeonForm
from django.db.models import Q

def surgeon_list(request):
    name = request.GET.get('name', '')
    specialty = request.GET.get('specialty', '')
    city = request.GET.get('city', '')
    max_fees = request.GET.get('max_fees', None)
    min_rating = request.GET.get('min_rating', None)
    sort = request.GET.get('sort', 'first_name')
    direction = request.GET.get('direction', 'asc')

    surgeons = Surgeon.objects.all()

    if name:
        surgeons = surgeons.filter(Q(first_name__icontains=name) | Q(last_name__icontains=name))
    if specialty:
        surgeons = surgeons.filter(specialty__icontains=specialty)
    if city:
        surgeons = surgeons.filter(city__icontains=city)
    if max_fees:
        try:
            max_fees = float(max_fees)
            surgeons = surgeons.filter(fees__lte=max_fees)
        except ValueError:
            pass
    if min_rating:
        try:
            min_rating = float(min_rating)
            surgeons = surgeons.filter(rating__gte=min_rating)
        except ValueError:
            pass

    if sort in ['first_name', 'specialty', 'city', 'fees', 'rating']:
        if direction == 'desc':
            sort = f'-{sort}'
        surgeons = surgeons.order_by(sort)

    next_directions = {
        column: 'asc' if sort != column or direction == 'desc' else 'desc'
        for column in ['first_name', 'specialty', 'city', 'fees', 'rating']
    }

    paginator = Paginator(surgeons, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(
        request,
        'search/surgeon_list.html',
        {
            'page_obj': page_obj,
            'sort': sort,
            'direction': direction,  
            'next_directions': next_directions,  
            'name': name,
            'specialty': specialty,
            'city': city,
            'max_fees': max_fees,
            'min_rating': min_rating,
        }
    )
def surgeon_create(request):
    if request.method == 'POST':
        form = SurgeonForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('surgeon-list')
    else:
        form = SurgeonForm()
    return render(request, 'search/surgeon_form.html', {'form': form})

def surgeon_update(request, pk):
    surgeon = get_object_or_404(Surgeon, pk=pk)
    if request.method == 'POST':
        form = SurgeonForm(request.POST, instance=surgeon)
        if form.is_valid():
            form.save()
            return redirect('surgeon-list')
    else:
        form = SurgeonForm(instance=surgeon)
    return render(request, 'search/surgeon_form.html', {'form': form})

def surgeon_delete(request, pk):
    surgeon = get_object_or_404(Surgeon, pk=pk)
    if request.method == 'POST':
        surgeon.delete()
        return redirect('surgeon-list')
    return render(request, 'search/surgeon_confirm_delete.html', {'surgeon': surgeon})

def home_view(request):
    return render(request, 'search/home.html')

def bulk_upload_view(request):
    if request.method == "POST":
        form = CSVUploadForm(request.POST, request.FILES)
        if form.is_valid():
            csv_file = request.FILES['csv_file']
            try:
                # Read CSV file
                data = pd.read_csv(csv_file)

                # Validate required columns
                required_columns = [
                    'first_name', 'last_name', 'specialty', 'city',
                    'address', 'phone_number', 'email', 'fees',
                    'rating', 'hospital_name', 'available_hours'
                ]
                if not all(col in data.columns for col in required_columns):
                    messages.error(request, "Missing required columns in CSV file.")
                    return redirect('bulk-upload')

                # Bulk create Surgeon objects
                surgeons = [
                    Surgeon(
                        first_name=row['first_name'],
                        last_name=row['last_name'],
                        specialty=row['specialty'],
                        city=row['city'],
                        address=row['address'],
                        phone_number=row['phone_number'],
                        email=row['email'],
                        fees=row['fees'],
                        rating=row['rating'],
                        hospital_name=row['hospital_name'],
                        available_hours=row['available_hours']
                    )
                    for _, row in data.iterrows()
                ]
                Surgeon.objects.bulk_create(surgeons)

                messages.success(request, "Surgeons uploaded successfully!")
                return redirect('surgeon-list')
            except Exception as e:
                messages.error(request, f"Error processing file: {e}")
                return redirect('bulk-upload')
    else:
        form = CSVUploadForm()

    return render(request, 'search/bulk_upload.html', {'form': form})


