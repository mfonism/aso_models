from django.db import models
from django.utils import timezone


class AbstractShrewdModel(models.Model):
    '''
    I am quite shrewd about the things I'll let you do with me.

    I won't let you delete me unless you really need to. Because
    once you delete me, I go into nothingness - You can't get me back.
    Which is really risky, especially considering the fact that you
    often visit your recycle bin to restore things you thought
    you didn't need at some point in time.

    Anyways, the gist is, anytime you call `delete` on me I'll just
    keep myself out of your way. I'll go into my (soft) deleted state.
    You'll know where to find me when you realise the errors of
    your ways and feel sorry :)
    '''
    class Meta:
        abstract = True

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    activated_at = models.DateTimeField(
        default=timezone.now, blank=True, null=True
    )
    deleted_at = models.DateTimeField(blank=True, null=True)

    objects = models.Manager()
