from .models import Category
# context processor
def menu_links(request):
    links = Category.objects.all()
    return dict(links=links)
