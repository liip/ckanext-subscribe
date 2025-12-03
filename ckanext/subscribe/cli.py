import datetime
import time

import ckan.plugins as p
import click
from ckan import model

from ckanext.activity.model import Activity


@click.group()
def subscribe():
    pass


@subscribe.command("send-any-notifications")
@click.option(
    "--repeatedly",
    "-r",
    default=False,
    help="Repeat every 10s",
)
@click.pass_context
def send_any_notifications(ctx, repeatedly):
    """Check for activity and for any subscribers, send emails with the notifications."""
    flask_app = ctx.meta["flask_app"]

    with flask_app.test_request_context():
        while True:
            p.toolkit.get_action("subscribe_send_any_notifications")(
                {"model": model, "ignore_auth": True}, {}
            )
            if not repeatedly:
                break
            click.echo("Repeating in 10s")
            time.sleep(10)


@subscribe.command("create-test-activity")
@click.argument(
    "object_id",
    type=str,
    required=True,
)
def create_test_activity(object_id):
    """Create some activity for testing purposes, for a given existing object.

    OBJECT_ID is the name or id of an existing package, group, or organization.
    """
    obj = model.Package.get(object_id) or model.Group.get(object_id)
    assert obj, "Object could not be found"
    site_user = p.toolkit.get_action("get_site_user")(
        {"model": model, "ignore_auth": True}, {}
    )
    site_user_obj = model.User.get(site_user["name"])
    activity = Activity(
        user_id=site_user_obj.id,
        object_id=obj.id,
        activity_type="test activity",
    )
    activity.timestamp = datetime.datetime.now()
    model.Session.add(activity)
    click.echo(activity)
    model.Session.commit()


@subscribe.command("delete-test-activity")
def _delete_test_activity():
    """Delete any test activity (i.e. clean up after doing 'create-test-activity').
    Works for test activity on all objects.
    """
    test_activity = (
        model.Session.query(Activity).filter_by(activity_type="test activity").all()
    )
    for activity in test_activity:
        model.Session.delete(activity)
    click.echo("Done!")
