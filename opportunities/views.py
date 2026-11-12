
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from .forms import OpportunityForm, ApplicationForm
from .models import Opportunity, Application
from accounts.models import OrganizationProfile


@login_required
def create_opportunity(request):

    if request.user.role != 'ORGANIZATION':
        messages.error(
            request,
            "Only organization accounts can create opportunities."
        )
        return redirect('home')

    if request.user.organization_status != 'APPROVED':
        messages.error(
            request,
            "Your organization must be approved before publishing opportunities."
        )
        return redirect('home')

    try:
        organization = request.user.organization_profile

    except OrganizationProfile.DoesNotExist:
        messages.error(
            request,
            "Please complete your organization profile first."
        )
        return redirect('home')

    if request.method == 'POST':

        form = OpportunityForm(request.POST)

        if form.is_valid():

            opportunity = form.save(commit=False)
            opportunity.organization = organization

            try:
                opportunity.full_clean()
                opportunity.save()

                messages.success(
                    request,
                    "Opportunity created successfully!"
                )

                return redirect('home')

            except ValidationError as error:
                form.add_error(None, error)

    else:
        form = OpportunityForm()

    return render(
        request,
        'opportunities/create_opportunity.html',
        {'form': form}
    )


@login_required
def apply_for_opportunity(request, opportunity_id):

    if request.user.role != 'INDIVIDUAL':
        messages.error(
            request,
            "Only individual accounts can apply."
        )
        return redirect('home')

    opportunity = get_object_or_404(
        Opportunity,
        id=opportunity_id
    )

    if request.method == 'POST':

        form = ApplicationForm(
            request.POST,
            request.FILES,
            opportunity=opportunity,
            applicant=request.user
        )

        if form.is_valid():

            if Application.objects.filter(
                opportunity=opportunity,
                applicant=request.user
            ).exists():

                form.add_error(
                    None,
                    "You have already applied for this opportunity."
                )

            else:
                application = form.save(commit=False)

                try:
                    application.full_clean()
                    application.save()

                    messages.success(
                        request,
                        "Your application was submitted successfully!"
                    )

                    return redirect('home')

                except ValidationError as error:
                    form.add_error(None, error)

                except IntegrityError:
                    form.add_error(
                        None,
                        "You have already applied for this opportunity."
                    )

    else:
        form = ApplicationForm(
            opportunity=opportunity,
            applicant=request.user
        )

    return render(
        request,
        'opportunities/apply_for_opportunity.html',
        {
            'form': form,
            'opportunity': opportunity
        }
    )
