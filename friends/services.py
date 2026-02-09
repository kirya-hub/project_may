from django.contrib.auth import get_user_model
from django.db.models import Exists, OuterRef, Q
from .models import Follow

User = get_user_model()


def with_follow_flags(qs, me):
    """
    Добавляет к каждому пользователю флаги:
    - is_following: я подписан на него
    - is_follower: он подписан на меня
    - is_friend: взаимная подписка
    """
    if not me or not me.is_authenticated:
        return qs.annotate(
            is_following=Exists(Follow.objects.none()),
            is_follower=Exists(Follow.objects.none()),
            is_friend=Exists(Follow.objects.none()),
        )

    following_exists = Follow.objects.filter(follower=me, following=OuterRef("pk"))
    follower_exists = Follow.objects.filter(follower=OuterRef("pk"), following=me)

    return qs.annotate(
        is_following=Exists(following_exists),
        is_follower=Exists(follower_exists),
    ).annotate(
        is_friend=Q(is_following=True) & Q(is_follower=True)
    )


def friends_qs(me):
    """Пользователи, с которыми взаимная подписка."""
    if not me.is_authenticated:
        return User.objects.none()

    my_following = Follow.objects.filter(follower=me).values_list("following_id", flat=True)
    my_followers = Follow.objects.filter(following=me).values_list("follower_id", flat=True)
    return User.objects.filter(id__in=my_following).filter(id__in=my_followers)
