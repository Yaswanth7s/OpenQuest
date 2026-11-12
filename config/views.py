
from django.shortcuts import render
from opportunities.models import Opportunity


def home(request):

    opportunities = Opportunity.objects.filter(
        status=Opportunity.Status.OPEN,
        organization__user__organization_status='APPROVED'
    ).select_related(
        'organization'
    ).order_by('-created_at')

    context = {
        'opportunities': opportunities
    }

    return render(
        request,
        'home.html',
        context
    )
