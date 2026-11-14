import tempfile

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta

from accounts.models import OrganizationProfile

from .models import Application, Opportunity


@override_settings(
    SECURE_SSL_REDIRECT=False,
    SESSION_COOKIE_SECURE=False,
    CSRF_COOKIE_SECURE=False,
)
class OpportunityWorkflowTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.organization_user = user_model.objects.create_user(
            username='verified-team',
            email='team@example.com',
            password='OpenQuest-test-password-2026',
            role=user_model.Role.ORGANIZATION,
            organization_status=user_model.OrganizationStatus.APPROVED,
        )
        self.organization = OrganizationProfile.objects.create(
            user=self.organization_user,
            organization_name='Verified Team',
            description='A team building useful things.',
            organization_email='contact@example.com',
            registration_number='OQ-TEAM-001',
        )
        self.individual = user_model.objects.create_user(
            username='applicant',
            email='applicant@example.com',
            password='OpenQuest-test-password-2026',
            role=user_model.Role.INDIVIDUAL,
        )
        self.opportunity = Opportunity.objects.create(
            organization=self.organization,
            title='Junior Product Designer',
            description='Help us make useful tools.',
            opportunity_type=Opportunity.OpportunityType.INTERNSHIP,
            work_mode=Opportunity.WorkMode.REMOTE,
            status=Opportunity.Status.OPEN,
        )

    def test_approved_organization_can_publish_opportunity(self):
        self.client.force_login(self.organization_user)

        response = self.client.post(
            reverse('create_opportunity'),
            {
                'title': 'Community Research Intern',
                'description': 'Learn with our community team.',
                'opportunity_type': Opportunity.OpportunityType.INTERNSHIP,
                'work_mode': Opportunity.WorkMode.HYBRID,
                'location': 'Remote',
                'required_skills': 'Research, curiosity',
                'application_url': '',
                'application_deadline': '',
                'status': Opportunity.Status.OPEN,
            },
        )

        self.assertRedirects(response, reverse('home'))
        created = Opportunity.objects.get(title='Community Research Intern')
        self.assertEqual(created.organization, self.organization)
        self.assertEqual(created.status, Opportunity.Status.OPEN)

    def test_unapproved_organization_cannot_publish(self):
        user_model = get_user_model()
        unapproved = user_model.objects.create_user(
            username='new-team',
            email='new-team@example.com',
            password='OpenQuest-test-password-2026',
            role=user_model.Role.ORGANIZATION,
        )
        self.client.force_login(unapproved)

        response = self.client.post(
            reverse('create_opportunity'),
            {'title': 'Not allowed'},
        )

        self.assertRedirects(response, reverse('home'))
        self.assertEqual(Opportunity.objects.count(), 1)

    def test_publishing_rejects_a_past_deadline(self):
        self.client.force_login(self.organization_user)

        response = self.client.post(
            reverse('create_opportunity'),
            {
                'title': 'Expired role',
                'description': 'This should not be published.',
                'opportunity_type': Opportunity.OpportunityType.INTERNSHIP,
                'work_mode': Opportunity.WorkMode.REMOTE,
                'location': '',
                'required_skills': '',
                'application_url': '',
                'application_deadline': (
                    timezone.localdate() - timedelta(days=1)
                ).isoformat(),
                'status': Opportunity.Status.OPEN,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            'The application deadline cannot be in the past.',
        )
        self.assertEqual(Opportunity.objects.count(), 1)

    def test_individual_can_apply_once(self):
        self.client.force_login(self.individual)
        apply_url = reverse(
            'apply_for_opportunity',
            args=(self.opportunity.pk,),
        )
        payload = {
            'cover_letter': 'I would love to contribute to this team.',
        }

        response = self.client.post(apply_url, payload)

        self.assertRedirects(response, reverse('home'))
        application = Application.objects.get()
        self.assertEqual(application.applicant, self.individual)
        self.assertEqual(application.opportunity, self.opportunity)
        applications_page = self.client.get(reverse('my_applications'))
        self.assertContains(applications_page, self.opportunity.title)
        home_page = self.client.get(reverse('home'))
        self.assertContains(home_page, 'You’ve applied')
        self.assertContains(home_page, 'View your application')
        self.assertNotContains(home_page, 'I’m interested')

        duplicate_response = self.client.post(apply_url, payload)

        self.assertEqual(duplicate_response.status_code, 200)
        self.assertContains(
            duplicate_response,
            'You have already applied for this opportunity.',
        )
        self.assertEqual(Application.objects.count(), 1)

    def test_non_individual_cannot_apply(self):
        self.client.force_login(self.organization_user)

        response = self.client.post(
            reverse(
                'apply_for_opportunity',
                args=(self.opportunity.pk,),
            ),
            {'cover_letter': 'A test.'},
        )

        self.assertRedirects(response, reverse('home'))
        self.assertFalse(Application.objects.exists())

    def test_application_dashboard_status_and_resume_permissions(self):
        self.client.force_login(self.individual)

        with tempfile.TemporaryDirectory() as media_root:
            with override_settings(MEDIA_ROOT=media_root):
                apply_response = self.client.post(
                    reverse(
                        'apply_for_opportunity',
                        args=(self.opportunity.pk,),
                    ),
                    {
                        'cover_letter': 'I would love to join the team.',
                        'resume': SimpleUploadedFile(
                            'resume.pdf',
                            b'%PDF-1.4 example resume',
                            content_type='application/pdf',
                        ),
                    },
                )
                self.assertRedirects(apply_response, reverse('home'))
                application = Application.objects.get()
                download_url = reverse(
                    'download_resume',
                    args=(application.pk,),
                )

                stranger = get_user_model().objects.create_user(
                    username='stranger',
                    email='stranger@example.com',
                    password='OpenQuest-test-password-2026',
                )
                self.client.force_login(stranger)
                self.assertEqual(
                    self.client.get(download_url).status_code,
                    403,
                )

                self.client.force_login(self.organization_user)
                dashboard_response = self.client.get(
                    reverse('organization_dashboard')
                )
                self.assertContains(dashboard_response, 'applicant')
                resume_response = self.client.get(download_url)
                self.assertEqual(resume_response.status_code, 200)
                resume_response.close()
                status_response = self.client.post(
                    reverse(
                        'update_application_status',
                        args=(application.pk,),
                    ),
                    {
                        'status': Application.ApplicationStatus.SHORTLISTED,
                    },
                )
                self.assertRedirects(
                    status_response,
                    reverse('organization_dashboard'),
                )
                application.refresh_from_db()
                self.assertEqual(
                    application.status,
                    Application.ApplicationStatus.SHORTLISTED,
                )

    def test_applicant_can_withdraw_an_unresolved_application(self):
        application = Application.objects.create(
            opportunity=self.opportunity,
            applicant=self.individual,
            cover_letter='Please consider my application.',
        )
        self.client.force_login(self.individual)

        response = self.client.post(
            reverse('withdraw_application', args=(application.pk,)),
        )

        self.assertRedirects(response, reverse('my_applications'))
        application.refresh_from_db()
        self.assertEqual(
            application.status,
            Application.ApplicationStatus.WITHDRAWN,
        )
