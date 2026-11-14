import tempfile
import re

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import OrganizationProfile


@override_settings(
    SECURE_SSL_REDIRECT=False,
    SESSION_COOKIE_SECURE=False,
    CSRF_COOKIE_SECURE=False,
)
class AuthenticationFlowTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='quester',
            email='quester@example.com',
            password='OpenQuest-test-password-2026'
        )
        self.admin = get_user_model().objects.create_superuser(
            username='site-admin',
            email='site-admin@example.com',
            password='OpenQuest-admin-password-2026',
        )

    def test_login_page_renders(self):
        response = self.client.get(reverse('login'))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/login.html')
        self.assertContains(response, 'Welcome back.')

    def test_registration_entry_offers_both_account_types(self):
        response = self.client.get(reverse('register'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Join as an individual')
        self.assertContains(response, 'Join as an organization')
        self.assertContains(response, reverse('register_individual'))
        self.assertContains(response, reverse('register_organization'))

    def test_user_can_log_in_and_log_out(self):
        response = self.client.post(
            reverse('login'),
            {
                'username': 'quester',
                'password': 'OpenQuest-test-password-2026'
            },
            follow=True
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['user'].is_authenticated)
        self.assertContains(response, 'Hi, quester')

        response = self.client.post(reverse('logout'), follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context['user'].is_authenticated)
        self.assertContains(response, 'Log in')

    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    def test_password_reset_link_changes_password(self):
        response = self.client.post(
            reverse('password_reset'),
            {'email': self.user.email},
        )

        self.assertRedirects(response, reverse('password_reset_done'))
        self.assertEqual(len(mail.outbox), 1)
        match = re.search(
            r'/accounts/password-reset/confirm/([^/]+)/([^/]+)/',
            mail.outbox[0].body,
        )
        self.assertIsNotNone(match)
        uid, token = match.groups()
        response = self.client.get(
            reverse(
                'password_reset_confirm',
                kwargs={'uidb64': uid, 'token': token},
            )
        )
        self.assertEqual(response.status_code, 302)

        response = self.client.post(
            response.url,
            {
                'new_password1': 'Blue!Cedar_Orbit-7421',
                'new_password2': 'Blue!Cedar_Orbit-7421',
            },
        )
        self.assertRedirects(response, reverse('password_reset_complete'))
        self.assertTrue(
            self.client.login(
                username='quester',
                password='Blue!Cedar_Orbit-7421',
            )
        )

    def test_pending_organization_can_complete_profile(self):
        organization = get_user_model().objects.create_user(
            username='organization',
            email='organization@example.com',
            password='OpenQuest-test-password-2026',
            role=get_user_model().Role.ORGANIZATION
        )
        self.client.force_login(organization)

        home_response = self.client.get(reverse('home'))
        self.assertContains(home_response, 'Complete profile')

        profile_response = self.client.get(
            reverse('complete_organization_profile')
        )
        self.assertEqual(profile_response.status_code, 200)
        self.assertTemplateUsed(
            profile_response,
            'accounts/complete_organization_profile.html'
        )

    def test_registration_creates_an_individual_account(self):
        response = self.client.post(
            reverse('register_individual'),
            {
                'username': 'new-maker',
                'email': 'new-maker@example.com',
                'password1': 'OpenQuest-unique-password-2026!',
                'password2': 'OpenQuest-unique-password-2026!',
            },
            follow=True,
        )

        user = get_user_model().objects.get(username='new-maker')
        self.assertEqual(user.role, get_user_model().Role.INDIVIDUAL)
        self.assertTrue(response.context['user'].is_authenticated)

    def test_organization_can_submit_profile(self):
        organization = get_user_model().objects.create_user(
            username='new-organization',
            email='org@example.com',
            password='OpenQuest-test-password-2026',
            role=get_user_model().Role.ORGANIZATION,
        )
        self.client.force_login(organization)

        response = self.client.post(
            reverse('complete_organization_profile'),
            {
                'organization_name': 'Good Work Lab',
                'description': 'A team working on useful tools.',
                'official_website': '',
                'organization_email': 'hello@goodwork.example',
                'registration_number': 'OQ-GOOD-WORK-01',
            },
            follow=True,
        )

        self.assertRedirects(response, reverse('home'))
        self.assertEqual(
            OrganizationProfile.objects.get().user,
            organization,
        )

    def test_user_can_update_their_profile(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse('profile'),
            {
                'bio': 'I like making useful things with good people.',
                'location': 'Remote',
                'skills': 'Research, design',
                'website': '',
            },
        )

        self.assertRedirects(response, reverse('profile'))
        self.user.profile.refresh_from_db()
        self.assertEqual(self.user.profile.location, 'Remote')

    def test_rejected_organization_can_resubmit_profile(self):
        organization = get_user_model().objects.create_user(
            username='rejected-organization',
            email='rejected@example.com',
            password='OpenQuest-test-password-2026',
            role=get_user_model().Role.ORGANIZATION,
            organization_status=get_user_model().OrganizationStatus.REJECTED,
        )
        OrganizationProfile.objects.create(
            user=organization,
            organization_name='Good Work Lab',
            description='A team working on useful tools.',
            organization_email='hello@goodwork.example',
            registration_number='OQ-GOOD-WORK-02',
            admin_remarks='Please update your organization details.',
        )
        self.client.force_login(organization)

        response = self.client.post(
            reverse('complete_organization_profile'),
            {
                'organization_name': 'Good Work Lab',
                'description': 'Updated organization information.',
                'official_website': '',
                'organization_email': 'hello@goodwork.example',
                'registration_number': 'OQ-GOOD-WORK-02',
            },
            follow=True,
        )

        organization.refresh_from_db()
        self.assertRedirects(response, reverse('home'))
        self.assertEqual(
            organization.organization_status,
            get_user_model().OrganizationStatus.PENDING,
        )

    def test_admin_can_create_custom_users(self):
        self.client.force_login(self.admin)
        add_url = reverse('admin:accounts_user_add')

        page = self.client.get(add_url)
        self.assertEqual(page.status_code, 200)
        self.assertContains(page, 'organization_status')

        response = self.client.post(
            add_url,
            {
                'username': 'admin-created-org',
                'email': 'admin-created-org@example.com',
                'role': get_user_model().Role.ORGANIZATION,
                'organization_status': get_user_model().OrganizationStatus.PENDING,
                'is_email_verified': '',
                'password1': 'Mint!River_Studio-5927',
                'password2': 'Mint!River_Studio-5927',
                '_save': 'Save',
            },
            follow=True,
        )

        created = get_user_model().objects.get(username='admin-created-org')
        self.assertEqual(created.email, 'admin-created-org@example.com')
        self.assertEqual(created.role, get_user_model().Role.ORGANIZATION)
        self.assertTrue(response.redirect_chain)

    def test_admin_can_approve_an_organization_profile(self):
        organization = get_user_model().objects.create_user(
            username='reviewed-org',
            email='reviewed-org@example.com',
            password='OpenQuest-test-password-2026',
            role=get_user_model().Role.ORGANIZATION,
        )
        profile = OrganizationProfile.objects.create(
            user=organization,
            organization_name='Reviewed Organization',
            description='A team ready to collaborate.',
            organization_email='contact@reviewed.example',
            registration_number='OQ-REVIEWED-01',
        )
        self.client.force_login(self.admin)

        response = self.client.post(
            reverse('admin:accounts_organizationprofile_changelist'),
            {
                'action': 'approve_organizations',
                'index': '0',
                '_selected_action': [str(profile.pk)],
            },
            follow=True,
        )

        organization.refresh_from_db()
        self.assertEqual(
            organization.organization_status,
            get_user_model().OrganizationStatus.APPROVED,
        )
        self.assertTrue(response.redirect_chain)

    def test_verification_document_download_is_private(self):
        organization = get_user_model().objects.create_user(
            username='document-owner',
            email='document-owner@example.com',
            password='OpenQuest-test-password-2026',
            role=get_user_model().Role.ORGANIZATION,
        )
        self.client.force_login(organization)

        with tempfile.TemporaryDirectory() as media_root:
            with override_settings(MEDIA_ROOT=media_root):
                response = self.client.post(
                    reverse('complete_organization_profile'),
                    {
                        'organization_name': 'Document Owner Lab',
                        'description': 'A verified organization.',
                        'organization_email': 'hello@document-owner.example',
                        'registration_number': 'OQ-DOCUMENT-01',
                        'verification_document': SimpleUploadedFile(
                            'registration.pdf',
                            b'%PDF-1.4 organization proof',
                            content_type='application/pdf',
                        ),
                    },
                )
                self.assertRedirects(response, reverse('home'))
                profile = OrganizationProfile.objects.get(user=organization)
                download_url = reverse(
                    'download_verification_document',
                    args=(profile.pk,),
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

                self.client.force_login(organization)
                download = self.client.get(download_url)
                self.assertEqual(download.status_code, 200)
                self.assertEqual(
                    download['Content-Disposition'].split(';')[0],
                    'attachment',
                )
                download.close()
