
from django.shortcuts import render
from opportunities.models import Application, Opportunity


def home(request):

    opportunities = Opportunity.objects.filter(
        status=Opportunity.Status.OPEN,
        organization__user__organization_status='APPROVED'
    ).select_related(
        'organization'
    ).order_by('-created_at')

    applied_opportunity_ids = set()
    if request.user.is_authenticated and request.user.role == 'INDIVIDUAL':
        applied_opportunity_ids = set(
            Application.objects.filter(
                applicant=request.user,
            ).values_list('opportunity_id', flat=True)
        )

    context = {
        'opportunities': opportunities,
        'applied_opportunity_ids': applied_opportunity_ids,
    }

    return render(
        request,
        'home.html',
        context
    )
