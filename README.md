# Django Request Log

Reusable model and utils for parsing and storing request info in a Django app.

## Background

We have a number of Django apps that record information about a request: url,
session_key, user-agent etc. Currently all of the models recreate the same request parsing logic, and store the information in their own model tables.

This app is designed to centralise request logging in a single model.

It consists of three classes, `RequestParser`, `AbstractRequestLog` (abstract model) and `RequestLog` (which is a concrete model). The `RequestParser` is not a Django model, but a helper class that exposes the properties of an HttpRequest that we want to store:

* user
* session_key
* http_method
* http_user_agent
* http_referer
* request_path
* query_string
* remote_addr

Most of these are straight passthrough properties to the `request` or `session`, but the `remote_addr` has a little more logic in it.

## Usage

Using the `VisitorLog` class from `django-visitor-pass` as an example, this is how the class looks today:

```python
# models.py from django-visitor-pass
class VisitorLog(models.Model):

    visitor = models.ForeignKey(Visitor, on_delete=CASCADE)
    session_key = models.CharField(blank=True, max_length=40)
    http_method = models.CharField(max_length=10)
    request_uri = models.URLField()
    remote_addr = models.CharField(max_length=100)
    query_string = models.TextField(blank=True)
    http_user_agent = models.TextField()
    http_referer = models.TextField()
    timestamp = models.DateTimeField(default=tz_now)
```

The `AbstractRequestLog` is an abstract model, which you can use to subclass your own model, incorporating all of the fields above.

```python
class VisitorLog(AbstractRequestLog):

    visitor = models.ForeignKey(Visitor, on_delete=CASCADE)
    timestamp = models.DateTimeField(default=tz_now)
```

The `RequestLog` is a concrete subclass of `AbstractRequestLog`, which you can add to your model via foreign key or one-to-one field, if you wish to consolidate all logging in a single table:

```python
# models.py from django-visitor-pass
class VisitorLog(models.Model):

    visitor = models.ForeignKey(Visitor, on_delete=CASCADE)
    request_log = OneToOneField(RequestLog)
    timestamp = models.DateTimeField(default=tz_now)
```

## Configuration

Add `request_log` to `INSTALLED_APPS` in your `settings.py` if you wish to use `RequestLog`:

```python
# settings.py
INSTALLED_APPS = [
    ...
    "request_log",
]
```

## License

MIT
