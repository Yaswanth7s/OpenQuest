
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required

from .forms import (
    IndividualRegistrationForm,
    OrganizationRegistrationForm,
    OrganizationProfileForm
)

from .models import OrganizationProfile

def register_individual(request):

    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':

        form = IndividualRegistrationForm(request.POST)

        if form.is_valid():

            user = form.save()

            login(request, user)

            messages.success(
                request,
                "Your individual account has been created successfully!"
            )

            return redirect('home')

    else:
        form = IndividualRegistrationForm()

    return render(
        request,
        'accounts/register.html',
        {
            'form': form,
            'account_type': 'Individual'
        }
    )


def register_organization(request):

    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':

        form = OrganizationRegistrationForm(request.POST)

        if form.is_valid():

            user = form.save()

            messages.success(
                request,
                "Your organization account has been created. "
                "Complete your organization profile while verification is pending."
            )

            login(request, user)

            return redirect('home')

    else:
        form = OrganizationRegistrationForm()

    return render(
        request,
        'accounts/register.html',
        {
            'form': form,
            'account_type': 'Organization'
        }
    )



@login_required
def complete_organization_profile(request):

    if request.user.role != 'ORGANIZATION':
        messages.error(
            request,
            "Only organization accounts can complete an organization profile."
        )
        return redirect('home')

    if request.user.organization_status != 'PENDING':
        messages.error(
            request,
            "Your organization profile cannot be submitted in its current status."
        )
        return redirect('home')

    organization_profile = OrganizationProfile.objects.filter(
        user=request.user
    ).first()

    if request.method == 'POST':

        form = OrganizationProfileForm(
            request.POST,
            request.FILES,
            instance=organization_profile
        )

        if form.is_valid():

            profile = form.save(commit=False)
            profile.user = request.user

            try:
                profile.full_clean()
                profile.save()

                messages.success(
                    request,
                    "Organization profile submitted successfully! "
                    "Your account is awaiting admin verification."
                )

                return redirect('home')

            except Exception as error:
                form.add_error(None, str(error))

    else:
        form = OrganizationProfileForm(
            instance=organization_profile
        )

    return render(
        request,
        'accounts/complete_organization_profile.html',
        {'form': form}
    )

