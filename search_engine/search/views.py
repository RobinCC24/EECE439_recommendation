# search/views.py
from decimal import Decimal
from django.core.paginator import Paginator
import pandas as pd
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from sklearn.neighbors import NearestNeighbors
from .models import Surgeon
from .forms import CSVUploadForm, SurgeonForm
from django.db.models import Q
from sklearn.preprocessing import MinMaxScaler
import spacy


def surgeon_list(request):
    name = request.GET.get('name', '').strip()
    specialty = request.GET.get('specialty', '').strip()
    city = request.GET.get('city', '').strip()
    max_fees = request.GET.get('max_fees', None)
    min_rating = request.GET.get('min_rating', None)
    sort = request.GET.get('sort', 'first_name')
    direction = request.GET.get('direction', 'asc')

    surgeons = Surgeon.objects.all()

    if name:
        # Split the name input into parts (e.g., ["John", "Doe"])
        name_parts = name.split()
        
        # Filter by first and last name parts
        if len(name_parts) == 1:
            # If only one part is provided, search both first_name and last_name
            surgeons = surgeons.filter(Q(first_name__icontains=name_parts[0]) | Q(last_name__icontains=name_parts[0]))
        elif len(name_parts) > 1:
            # If multiple parts are provided, assume first_name and last_name
            surgeons = surgeons.filter(
                Q(first_name__icontains=name_parts[0], last_name__icontains=name_parts[1]) |
                Q(first_name__icontains=name_parts[1], last_name__icontains=name_parts[0])  # Handle reversed order
            )
    if specialty:
        surgeons = surgeons.filter(specialty__icontains=specialty)
    if city:
        surgeons = surgeons.filter(Q(city__icontains=city) | Q(city__icontains=city.split(",")[0]))
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


nlp = spacy.load('en_core_web_sm')

def extract_preferences(query):
    doc = nlp(query)
    city = None
    min_rating = None
    max_fees = None

    keywords = {
        "top-rated": 5,  
        "high rating": 4.0,
        "low rating": 2.5,  
        "cheap": 1000, 
        "affordable": 2500,  
        "expensive": 7000  
    }

    for word in query.lower().split():
        if word in keywords:
            if "rating" in word or "rated" in word:
                min_rating = keywords[word]
            elif "cheap" in word or "affordable" in word:
                max_fees = keywords[word]
            elif "expensive" in word:
                max_fees = keywords[word]  

    for ent in doc.ents:
        if ent.label_ == "GPE":  
            city = ent.text
        elif ent.label_ == "CARDINAL":  
            # Handle phrases like "less than 4000" or "more than 3"
            text = ent.text.lower()
            if "less than" in text:
                try:
                    max_fees = float(text.replace("less than", "").strip())
                except ValueError:
                    pass
            elif "more than" in text:
                try:
                    min_rating = float(text.replace("more than", "").strip())
                except ValueError:
                    pass
            else:
                try:
                    num = float(text)
                    if 0 <= num <= 5:  # Assume it's a rating
                        min_rating = num
                    elif num > 5:      # Assume it's a fee
                        max_fees = num
                except ValueError:
                    pass

    return city, min_rating, max_fees

def surgeon_recommendations(request):
    if request.GET.get('query', ''):
        query = request.GET.get('query', '')
        
        city, min_rating, max_fees = extract_preferences(query)
        
        min_rating = min_rating if min_rating is not None else 5
        max_fees = max_fees if max_fees is not None else 1000

        surgeons = Surgeon.objects.all()
        if city:
            surgeons = surgeons.filter(city__icontains=city)
        
        if not surgeons.exists():
            return render(request, 'search/recommendations.html', {'recommendations': []})

        surgeon_data = []
        surgeon_objects = []
        for surgeon in surgeons:
            surgeon_data.append([float(surgeon.rating), float(surgeon.fees)])
            surgeon_objects.append(surgeon)

        scaler = MinMaxScaler()
        normalized_data = scaler.fit_transform(surgeon_data)

        user_vector = scaler.transform([[min_rating, max_fees]])

        knn = NearestNeighbors(n_neighbors=5, metric='euclidean')
        knn.fit(normalized_data)
        distances, indices = knn.kneighbors(user_vector)

        recommended_surgeons = [surgeon_objects[i] for i in indices.flatten()]

        return render(request, 'search/recommendations.html', {
            'recommendations': recommended_surgeons,
            'query': query  
        })
    else:
        return render(request, 'search/recommendations.html', {'recommendations': []})

