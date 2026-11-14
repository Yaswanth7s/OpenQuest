
from pathlib import Path
from mimetypes import guess_type

from django.core.exceptions import PermissionDenied
from django.http import FileResponse, Http404
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.db.models import Count
from django.views.decorators.http import require_POST

from .forms import (
    ApplicationForm,
    ApplicationStatusForm,
    OpportunityForm,
)
from .models import Opportunity, Application
from accounts.models import OrganizationProfile


@login_required
def my_applications(request):
    if request.user.role != 'INDIVIDUAL':
        messages.error(request, 'Only individual accounts have applications.')
        return redirect('home')

    applications = Application.objects.filter(
        applicant=request.user,
    ).select_related(
        'opportunity',
        'opportunity__organization',
    ).order_by('-applied_at')
    return render(
        request,
        'opportunities/my_applications.html',
        {'applications': applications},
    )


@login_required
def organization_dashboard(request):
    if (
        request.user.role != 'ORGANIZATION'
        or request.user.organization_status != 'APPROVED'
    ):
        messages.error(
            request,
            'Only approved organizations can view their application dashboard.',
        )
        return redirect('home')

    organization = OrganizationProfile.objects.filter(
        user=request.user,
    ).first()
    if not organization:
        messages.error(
            request,
            'Complete an organization profile before managing opportunities.',
        )
        return redirect('home')

    opportunities = Opportunity.objects.filter(
        organization__user=request.user,
    ).select_related(
        'organization',
    ).annotate(
        application_count=Count('applications'),
    ).order_by('-created_at')
    applications = Application.objects.filter(
        opportunity__organization__user=request.user,
    ).select_related(
        'applicant',
        'opportunity',
    ).order_by('-applied_at')
    return render(
        request,
        'opportunities/organization_dashboard.html',
        {
            'organization': organization,
            'opportunities': opportunities,
            'applications': applications,
        },
    )


@login_required
@require_POST
def update_application_status(request, application_id):
    if (
        request.user.role != 'ORGANIZATION'
        or request.user.organization_status != 'APPROVED'
    ):
        messages.error(request, 'Only approved organizations can review applications.')
        return redirect('home')

    application = get_object_or_404(
        Application.objects.select_related('opportunity'),
        pk=application_id,
        opportunity__organization__user=request.user,
    )
    form = ApplicationStatusForm(request.POST)
    if form.is_valid():
        application.status = form.cleaned_data['status']
        application.save(update_fields=('status', 'updated_at'))
        messages.success(
            request,
            f'Application status updated to {application.get_status_display()}.',
        )
    else:
        messages.error(request, 'Choose a valid application status.')
    return redirect('organization_dashboard')


@login_required
@require_POST
def withdraw_application(request, application_id):
    if request.user.role != 'INDIVIDUAL':
        messages.error(request, 'Only individual accounts can withdraw applications.')
        return redirect('home')

    application = get_object_or_404(
        Application,
        pk=application_id,
        applicant=request.user,
    )
    if application.status not in (
        Application.ApplicationStatus.SUBMITTED,
        Application.ApplicationStatus.UNDER_REVIEW,
        Application.ApplicationStatus.SHORTLISTED,
    ):
        messages.error(request, 'This application can no longer be withdrawn.')
    else:
        application.status = Application.ApplicationStatus.WITHDRAWN
        application.save(update_fields=('status', 'updated_at'))
        messages.success(request, 'Your application has been withdrawn.')
    return redirect('my_applications')


@login_required
def download_resume(request, application_id):
    application = get_object_or_404(
        Application.objects.select_related(
            'applicant',
            'opportunity__organization',
        ),
        pk=application_id,
    )
    is_owner = application.applicant_id == request.user.id
    is_employer = (
        request.user.role == 'ORGANIZATION'
        and request.user.organization_status == 'APPROVED'
        and application.opportunity.organization.user_id == request.user.id
    )
    if not (request.user.is_staff or request.user.is_superuser or is_owner or is_employer):
        raise PermissionDenied
    if not application.resume:
        raise Http404('This application does not include a resume.')
    try:
        resume = application.resume.open('rb')
    except FileNotFoundError as error:
        raise Http404('The uploaded resume is no longer available.') from error

    content_type = guess_type(application.resume.name)[0]
    response = FileResponse(
        resume,
        as_attachment=True,
        filename=Path(application.resume.name).name,
        content_type=content_type or 'application/octet-stream',
    )
    response.headers['Cache-Control'] = 'private, no-store'
    return response


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
