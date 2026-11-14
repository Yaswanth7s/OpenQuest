import tempfile
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from .models import (
    Challenge,
    Comment,
    Review,
    Submission,
    Team,
    TeamMembership,
)


@override_settings(
    SECURE_SSL_REDIRECT=False,
    SESSION_COOKIE_SECURE=False,
    CSRF_COOKIE_SECURE=False,
)
class CommunityWorkflowTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.member = user_model.objects.create_user(
            username='maker',
            email='maker@example.com',
            password='OpenQuest-test-password-2026',
        )
        self.challenge = Challenge.objects.create(
            title='Make city transit more accessible',
            description='Help residents find accessible routes.',
            challenge_type=Challenge.ChallengeType.COMMUNITY,
            category=Challenge.Category.SOCIAL,
            created_by=self.member,
            deadline=timezone.localdate() + timedelta(days=14),
        )

    def test_challenge_list_and_detail_render(self):
        list_response = self.client.get(
            reverse('community:challenge_list')
        )
        detail_response = self.client.get(
            reverse(
                'community:challenge_detail',
                args=(self.challenge.pk,),
            )
        )

        self.assertContains(list_response, self.challenge.title)
        self.assertContains(detail_response, 'The challenge')
        self.assertTemplateUsed(
            detail_response,
            'community/challenge_detail.html',
        )

    def test_create_submit_and_review_pages_render(self):
        self.client.force_login(self.member)

        self.assertEqual(
            self.client.get(
                reverse('community:create_challenge')
            ).status_code,
            200,
        )
        self.assertEqual(
            self.client.get(
                reverse(
                    'community:create_team',
                    args=(self.challenge.pk,),
                )
            ).status_code,
            200,
        )

        team = Team.objects.create(
            challenge=self.challenge,
            leader=self.member,
            name='Access Allies',
        )
        self.assertEqual(
            self.client.get(
                reverse(
                    'community:submit_project',
                    args=(self.challenge.pk, team.pk),
                )
            ).status_code,
            200,
        )
        submission = Submission.objects.create(
            challenge=self.challenge,
            team=team,
            submitted_by=self.member,
            title='Route finder',
            description='A helpful route map.',
        )
        detail_response = self.client.get(
            reverse(
                'community:challenge_detail',
                args=(self.challenge.pk,),
            )
        )
        self.assertContains(detail_response, 'Route finder')
        self.assertContains(detail_response, 'Submit your work')

        reviewer = get_user_model().objects.create_user(
            username='reviewer',
            email='reviewer@example.com',
            password='OpenQuest-test-password-2026',
            role=get_user_model().Role.ORGANIZATION,
            organization_status=get_user_model().OrganizationStatus.APPROVED,
        )
        self.client.force_login(reviewer)
        review_response = self.client.get(
            reverse(
                'community:review_submission',
                args=(self.challenge.pk, submission.pk),
            )
        )
        self.assertEqual(review_response.status_code, 200)
        self.assertTemplateUsed(
            review_response,
            'community/review_form.html',
        )

    def test_authenticated_user_can_create_challenge(self):
        self.client.force_login(self.member)

        response = self.client.post(
            reverse('community:create_challenge'),
            {
                'title': 'Make public spaces more welcoming',
                'description': 'Design a small, testable improvement.',
                'challenge_type': Challenge.ChallengeType.COLLABORATION,
                'category': Challenge.Category.EDUCATION,
                'location': 'Remote',
                'deadline': (
                    timezone.localdate() + timedelta(days=20)
                ).isoformat(),
            },
        )

        challenge = Challenge.objects.get(
            title='Make public spaces more welcoming'
        )
        self.assertRedirects(
            response,
            reverse(
                'community:challenge_detail',
                args=(challenge.pk,),
            ),
        )
        self.assertEqual(challenge.created_by, self.member)

    def test_team_creation_adds_leader_and_joining_is_idempotent(self):
        self.client.force_login(self.member)
        create_response = self.client.post(
            reverse(
                'community:create_team',
                args=(self.challenge.pk,),
            ),
            {'name': 'Access Allies', 'description': 'We build maps.'},
        )
        team = Team.objects.get(name='Access Allies')
        self.assertRedirects(
            create_response,
            reverse(
                'community:challenge_detail',
                args=(self.challenge.pk,),
            ),
        )
        self.assertTrue(
            TeamMembership.objects.filter(
                team=team,
                user=self.member,
                role=TeamMembership.MembershipRole.LEADER,
            ).exists()
        )

        teammate = get_user_model().objects.create_user(
            username='teammate',
            email='teammate@example.com',
            password='OpenQuest-test-password-2026',
        )
        self.client.force_login(teammate)
        join_url = reverse(
            'community:join_team',
            args=(self.challenge.pk, team.pk),
        )
        self.client.post(join_url)
        self.client.post(join_url)

        self.assertEqual(
            TeamMembership.objects.filter(
                team=team,
                user=teammate,
            ).count(),
            1,
        )

    def test_only_team_members_can_submit_work(self):
        team = Team.objects.create(
            challenge=self.challenge,
            leader=self.member,
            name='Access Allies',
        )
        teammate = get_user_model().objects.create_user(
            username='teammate',
            email='teammate@example.com',
            password='OpenQuest-test-password-2026',
        )
        self.client.force_login(teammate)
        submit_url = reverse(
            'community:submit_project',
            args=(self.challenge.pk, team.pk),
        )

        denied_response = self.client.post(
            submit_url,
            {'title': 'Route finder', 'description': 'A helpful route map.'},
        )
        self.assertRedirects(
            denied_response,
            reverse(
                'community:challenge_detail',
                args=(self.challenge.pk,),
            ),
        )
        self.assertFalse(Submission.objects.exists())

        TeamMembership.objects.create(team=team, user=teammate)
        submitted_response = self.client.post(
            submit_url,
            {
                'title': 'Route finder',
                'description': 'A helpful route map.',
                'github_url': 'https://github.com/example/routes',
                'demo_url': '',
            },
        )

        self.assertRedirects(
            submitted_response,
            reverse(
                'community:challenge_detail',
                args=(self.challenge.pk,),
            ),
        )
        self.assertEqual(Submission.objects.get().submitted_by, teammate)

    def test_approved_organization_can_review_submission(self):
        team = Team.objects.create(
            challenge=self.challenge,
            leader=self.member,
            name='Access Allies',
        )
        submission = Submission.objects.create(
            challenge=self.challenge,
            team=team,
            submitted_by=self.member,
            title='Route finder',
            description='A helpful route map.',
        )
        reviewer = get_user_model().objects.create_user(
            username='reviewer',
            email='reviewer@example.com',
            password='OpenQuest-test-password-2026',
            role=get_user_model().Role.ORGANIZATION,
            organization_status=get_user_model().OrganizationStatus.APPROVED,
        )
        self.client.force_login(reviewer)

        response = self.client.post(
            reverse(
                'community:review_submission',
                args=(self.challenge.pk, submission.pk),
            ),
            {
                'decision': Review.ReviewDecision.SHORTLISTED,
                'feedback': 'A thoughtful, useful approach.',
            },
        )

        submission.refresh_from_db()
        self.assertRedirects(
            response,
            reverse(
                'community:challenge_detail',
                args=(self.challenge.pk,),
            ),
        )
        self.assertEqual(
            submission.status,
            Submission.SubmissionStatus.SHORTLISTED,
        )
        self.assertEqual(Review.objects.get().reviewer, reviewer)

    def test_individual_cannot_review_submission(self):
        team = Team.objects.create(
            challenge=self.challenge,
            leader=self.member,
            name='Access Allies',
        )
        submission = Submission.objects.create(
            challenge=self.challenge,
            team=team,
            submitted_by=self.member,
            title='Route finder',
            description='A helpful route map.',
        )
        individual = get_user_model().objects.create_user(
            username='other-maker',
            email='other@example.com',
            password='OpenQuest-test-password-2026',
        )
        self.client.force_login(individual)

        response = self.client.post(
            reverse(
                'community:review_submission',
                args=(self.challenge.pk, submission.pk),
            ),
            {
                'decision': Review.ReviewDecision.ACCEPTED,
                'feedback': 'Looks great.',
            },
        )

        self.assertRedirects(
            response,
            reverse(
                'community:challenge_detail',
                args=(self.challenge.pk,),
            ),
        )
        self.assertFalse(Review.objects.exists())

    def test_submission_attachment_download_requires_access(self):
        team = Team.objects.create(
            challenge=self.challenge,
            leader=self.member,
            name='Access Allies',
        )
        self.client.force_login(self.member)

        with tempfile.TemporaryDirectory() as media_root:
            with override_settings(MEDIA_ROOT=media_root):
                response = self.client.post(
                    reverse(
                        'community:submit_project',
                        args=(self.challenge.pk, team.pk),
                    ),
                    {
                        'title': 'Route finder',
                        'description': 'A helpful route map.',
                        'github_url': '',
                        'demo_url': '',
                        'attachment': SimpleUploadedFile(
                            'project.zip',
                            b'project artifact',
                            content_type='application/zip',
                        ),
                    },
                )
                self.assertRedirects(
                    response,
                    reverse(
                        'community:challenge_detail',
                        args=(self.challenge.pk,),
                    ),
                )
                submission = Submission.objects.get()
                download_url = reverse(
                    'community:download_submission_attachment',
                    args=(self.challenge.pk, submission.pk),
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

                self.client.force_login(self.member)
                download = self.client.get(download_url)
                self.assertEqual(download.status_code, 200)
                self.assertEqual(
                    download['Content-Disposition'].split(';')[0],
                    'attachment',
                )
                download.close()

    def test_authenticated_user_can_comment(self):
        self.client.force_login(self.member)

        response = self.client.post(
            reverse(
                'community:add_comment',
                args=(self.challenge.pk,),
            ),
            {'content': 'I would love to help test this.'},
        )

        self.assertRedirects(
            response,
            reverse(
                'community:challenge_detail',
                args=(self.challenge.pk,),
            ),
        )
        self.assertEqual(Comment.objects.get().author, self.member)

    def test_only_challenge_owner_can_change_challenge_status(self):
        teammate = get_user_model().objects.create_user(
            username='teammate',
            email='teammate@example.com',
            password='OpenQuest-test-password-2026',
        )
        self.client.force_login(teammate)
        update_url = reverse(
            'community:update_challenge_status',
            args=(self.challenge.pk,),
        )

        forbidden_response = self.client.post(
            update_url,
            {'status': Challenge.Status.CLOSED},
        )
        self.assertRedirects(
            forbidden_response,
            reverse(
                'community:challenge_detail',
                args=(self.challenge.pk,),
            ),
        )
        self.challenge.refresh_from_db()
        self.assertEqual(self.challenge.status, Challenge.Status.OPEN)

        self.client.force_login(self.member)
        allowed_response = self.client.post(
            update_url,
            {'status': Challenge.Status.CLOSED},
        )
        self.assertRedirects(
            allowed_response,
            reverse(
                'community:challenge_detail',
                args=(self.challenge.pk,),
            ),
        )
        self.challenge.refresh_from_db()
        self.assertEqual(self.challenge.status, Challenge.Status.CLOSED)

    def test_organization_accounts_cannot_participate_in_challenges(self):
        organization = get_user_model().objects.create_user(
            username='hiring-team',
            email='hiring-team@example.com',
            password='OpenQuest-test-password-2026',
            role=get_user_model().Role.ORGANIZATION,
            organization_status=get_user_model().OrganizationStatus.APPROVED,
        )
        team = Team.objects.create(
            challenge=self.challenge,
            leader=self.member,
            name='Access Allies',
        )
        self.client.force_login(organization)

        home_response = self.client.get(reverse('home'))
        self.assertNotContains(home_response, 'Explore challenges')
        self.assertNotContains(
            home_response,
            f'href="{reverse("community:challenge_list")}"',
        )

        challenge_list_response = self.client.get(
            reverse('community:challenge_list')
        )
        self.assertNotContains(
            challenge_list_response,
            f'href="{reverse("community:create_challenge")}"',
        )
        challenge_response = self.client.get(
            reverse(
                'community:challenge_detail',
                args=(self.challenge.pk,),
            )
        )
        self.assertNotContains(challenge_response, 'Join this team')
        self.assertNotContains(challenge_response, 'Start a team')
        self.assertNotContains(challenge_response, 'Post comment')

        challenge_response = self.client.post(
            reverse('community:create_challenge'),
            {
                'title': 'Organization challenge',
                'description': 'Organizations do not create community challenges.',
                'challenge_type': Challenge.ChallengeType.COMMUNITY,
                'category': Challenge.Category.OTHER,
                'location': '',
                'deadline': '',
            },
        )
        self.assertRedirects(challenge_response, reverse('home'))
        self.assertEqual(Challenge.objects.count(), 1)

        participation_requests = (
            (
                reverse(
                    'community:create_team',
                    args=(self.challenge.pk,),
                ),
                {'name': 'Hiring Team', 'description': ''},
            ),
            (
                reverse(
                    'community:join_team',
                    args=(self.challenge.pk, team.pk),
                ),
                {},
            ),
            (
                reverse(
                    'community:add_comment',
                    args=(self.challenge.pk,),
                ),
                {'content': 'This should not be posted.'},
            ),
            (
                reverse(
                    'community:submit_project',
                    args=(self.challenge.pk, team.pk),
                ),
                {
                    'title': 'Hiring team submission',
                    'description': 'Organizations do not submit challenge work.',
                },
            ),
        )
        for url, data in participation_requests:
            response = self.client.post(url, data)
            self.assertRedirects(response, reverse('home'))

        self.assertEqual(Team.objects.count(), 1)
        self.assertFalse(
            TeamMembership.objects.filter(
                team=team,
                user=organization,
            ).exists()
        )
        self.assertFalse(Comment.objects.exists())
        self.assertFalse(Submission.objects.exists())
