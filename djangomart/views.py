from django.shortcuts import render
from store.models import Product
# views
def home(request):
    products = Product.objects.all()
    return render(request, 'home.html', {'products': products})