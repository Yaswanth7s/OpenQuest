from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Team, TeamMembership


@receiver(post_save, sender=Team)
def create_team_leader_membership(sender, instance, created, **kwargs):

    if created:
        TeamMembership.objects.get_or_create(
            team=instance,
            user=instance.leader,
            defaults={
                'role': TeamMembership.MembershipRole.LEADER
            }
        )