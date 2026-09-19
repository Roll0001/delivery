from django.db.models import Q
from django.shortcuts import render

from .models import RestorantInfo

def home(request):
	query = request.GET.get('q', '').strip()
	restaurants = RestorantInfo.objects.all().order_by('name')
	if query:
		restaurants = restaurants.filter(
			Q(name__icontains=query) | Q(address__icontains=query)
		)

	return render(request, 'home.html', {
		'restaurants': restaurants,
		'query': query,
	})
