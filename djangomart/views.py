from django.shortcuts import render
from store.models import Product
# Views
def home(request):
    products = Product.objects.all()
    return render(request, 'home.html', {'products': products})