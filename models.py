import json

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.utils.text import slugify

from .validators import validate_validator_list, validate_json_dict


class Term(models.Model):
    name = models.CharField(max_length=55, unique=True)
    slug = models.SlugField(max_length=55, unique=True)
    description = models.TextField(blank=True)
    validators = models.TextField(blank=True, validators=[validate_validator_list])

    user = models.ForeignKey(User, on_delete=models.PROTECT, null=True, blank=True)
    created = models.DateTimeField("created", auto_now_add=True)
    modified = models.DateTimeField("modified", auto_now=True)


class Tag(models.Model):
    key = models.ForeignKey(Term, on_delete=models.PROTECT)
    value = models.TextField(blank=True)

    def save(self, *args, **kwargs):
        # update object modified field
        self.object.modified = timezone.now()
        super(Tag, self).save(*args, **kwargs)

    def __str__(self):
        return '%s="%s"' % (self.key.slug, self.value)


class Location(models.Model):
    name = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(unique=True)
    parent = models.ForeignKey('self', on_delete=models.PROTECT, null=True, blank=True)

    user = models.ForeignKey(User, on_delete=models.PROTECT, null=True, blank=True, editable=False)
    created = models.DateTimeField("created", auto_now_add=True)
    modified = models.DateTimeField("modified", auto_now=True)

    description = models.TextField(blank=True)
    geometry = models.TextField(blank=True)

    def __str__(self):
        return self.name


class LocationTag(Tag):
    object = models.ForeignKey(Location, on_delete=models.CASCADE)


class Sample(models.Model):
    name = models.CharField(max_length=25, blank=True)
    slug = models.CharField(max_length=55, unique=True, editable=False)
    parent = models.ForeignKey('self', on_delete=models.PROTECT, null=True, blank=True, editable=False)

    user = models.ForeignKey(User, on_delete=models.PROTECT, null=True, blank=True, editable=False)
    created = models.DateTimeField("created", auto_now_add=True)
    modified = models.DateTimeField("modified", auto_now=True)

    collected = models.DateTimeField("collected", blank=True, null=True)
    location = models.ForeignKey(Location, on_delete=models.PROTECT, blank=True, null=True)

    def save(self, *args, **kwargs):
        if not self.pk:
            self.set_slug()
        super(Sample, self).save(*args, **kwargs)

    def set_slug(self):
        dt = self.collected if self.collected else self.created if self.created else timezone.now()
        location_slug = self.location.slug[:10] if self.location else ""
        user = self.user.username if self.user else ""
        hint = slugify(self.name)

        for date_fun in [self.short_date, self.long_date, self.longest_date]:
            dt_str = date_fun(dt)
            id_str = "_".join(item for item in [user, dt_str, location_slug, hint] if item)
            id_str = id_str[:55]
            other_objects = Sample.objects.filter(slug=id_str)
            if len(other_objects) == 0:
                self.slug = id_str
                return

        self.slug = str(self.pk)

    def short_date(self, dt):
        return str(dt.date())

    def long_date(self, dt):
        return "%sT%s.%s.%s" % (dt.date(), dt.hour, dt.minute, dt.second)

    def longest_date(self, dt):
        return ("%sT%s" % (dt.date(), dt.time())).replace(":", ".")

    def __str__(self):
        return self.slug


class SampleTag(Tag):
    sample = models.ForeignKey(Sample, on_delete=models.CASCADE)


class Parameter(models.Model):
    name = models.CharField(max_length=55, unique=True)
    slug = models.SlugField(unique=True)
    parent = models.ForeignKey('self', on_delete=models.PROTECT, null=True, blank=True)

    user = models.ForeignKey(User, on_delete=models.PROTECT, null=True, blank=True)
    created = models.DateTimeField("created", auto_now_add=True)
    modified = models.DateTimeField("modified", auto_now=True)
    validators = models.TextField(blank=True, validators=[validate_validator_list])

    description = models.TextField(blank=True)

    def __str__(self):
        return self.name


class ParameterTag(Tag):
    param = models.ForeignKey(Parameter, on_delete=models.CASCADE)


class Measurement(models.Model):
    param = models.ForeignKey(Parameter, on_delete=models.PROTECT)
    sample = models.ForeignKey(Sample, on_delete=models.CASCADE)
    value = models.TextField(blank=True)
    tags = models.TextField(blank=True, validators=validate_json_dict)

    user = models.ForeignKey(User, on_delete=models.PROTECT, null=True, blank=True, editable=False)
    created = models.DateTimeField("created", auto_now_add=True)
    modified = models.DateTimeField("modified", auto_now=True)

    def parse_tags(self):
        return json.load(self.tags)

    def set_tags(self, **kwargs):
        tags_dict = self.parse_tags()
        for key, value in kwargs.items():
            tags_dict[key] = value
        self.tags = json.dumps(tags_dict)

    def __str__(self):
        if self.tags:
            str_out = "%s = %s %s" % (self.param, self.value, self.tags)
            # limit output to 150 chars or so
            if len(str_out) > 147:
                return str_out[:147] + "..."
            else:
                return str_out
        else:
            return "%s = %s" % (self.param, self.value)
