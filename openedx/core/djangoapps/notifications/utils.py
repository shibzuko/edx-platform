"""
Utils function for notifications app
"""
from typing import Dict, List

from common.djangoapps.student.models import CourseEnrollment
from lms.djangoapps.discussion.toggles import ENABLE_REPORTED_CONTENT_NOTIFICATIONS
from openedx.core.djangoapps.django_comment_common.models import Role
from openedx.core.lib.cache_utils import request_cached

from .config.waffle import ENABLE_COURSEWIDE_NOTIFICATIONS, SHOW_NOTIFICATIONS_TRAY


def find_app_in_normalized_apps(app_name, apps_list):
    """
    Returns app preference based on app_name
    """
    for app in apps_list:
        if app.get('name') == app_name:
            return app
    return None


def find_pref_in_normalized_prefs(pref_name, app_name, prefs_list):
    """
    Returns preference based on preference_name and app_name
    """
    for pref in prefs_list:
        if pref.get('name') == pref_name and pref.get('app_name') == app_name:
            return pref
    return None


def get_show_notifications_tray(user):
    """
    Returns show_notifications_tray as boolean for the courses in which user is enrolled
    """
    show_notifications_tray = False
    learner_enrollments_course_ids = CourseEnrollment.objects.filter(
        user=user,
        is_active=True
    ).values_list('course_id', flat=True)

    for course_id in learner_enrollments_course_ids:
        if SHOW_NOTIFICATIONS_TRAY.is_enabled(course_id):
            show_notifications_tray = True
            break

    return show_notifications_tray


def get_list_in_batches(input_list, batch_size):
    """
    Divides the list of objects into list of list of objects each of length batch_size.
    """
    list_length = len(input_list)
    for index in range(0, list_length, batch_size):
        yield input_list[index: index + batch_size]


def filter_course_wide_preferences(course_key, preferences):
    """
    If course wide notifications is disabled for course, it filters course_wide
    preferences from response
    """
    if ENABLE_COURSEWIDE_NOTIFICATIONS.is_enabled(course_key):
        return preferences
    course_wide_notification_types = ['new_discussion_post', 'new_question_post']

    if not ENABLE_REPORTED_CONTENT_NOTIFICATIONS.is_enabled(course_key):
        course_wide_notification_types.append('content_reported')

    config = preferences['notification_preference_config']
    for app_prefs in config.values():
        notification_types = app_prefs['notification_types']
        for course_wide_type in course_wide_notification_types:
            if course_wide_type in notification_types.keys():
                notification_types.pop(course_wide_type)
    return preferences


def get_user_forum_roles(user_id: int, course_id: str) -> List[str]:
    """
    Get forum roles for the given user in the specified course.

    :param user_id: User ID
    :param course_id: Course ID
    :return: List of forum roles
    """
    return list(Role.objects.filter(course_id=course_id, users__id=user_id).values_list('name', flat=True))


@request_cached()
def get_notification_types_with_visibility_settings() -> Dict[str, List[str]]:
    """
    Get notification types with their visibility settings.

    :return: List of dictionaries with notification type names and corresponding visibility settings
    """
    from .base_notification import COURSE_NOTIFICATION_TYPES

    notification_types_with_visibility_settings = {}
    for notification_type in COURSE_NOTIFICATION_TYPES.values():
        if notification_type.get('visible_to'):
            notification_types_with_visibility_settings[notification_type['name']] = notification_type['visible_to']

    return notification_types_with_visibility_settings


def filter_out_visible_notifications(
    user_preferences: dict,
    notifications_with_visibility: Dict[str, List[str]],
    user_forum_roles: List[str]
) -> dict:
    """
    Filter out notifications visible to forum roles from user preferences.

    :param user_preferences: User preferences dictionary
    :param notifications_with_visibility: List of dictionaries with notification type names and
    corresponding visibility settings
    :param user_forum_roles: List of forum roles for the user
    :return: Updated user preferences dictionary
    """
    for key in user_preferences:
        if 'notification_types' in user_preferences[key]:
            # Iterate over the types to remove and pop them from the dictionary
            for notification_type, is_visible_to in notifications_with_visibility.items():
                is_visible = False
                for role in is_visible_to:
                    if role in user_forum_roles:
                        is_visible = True
                        break
                if is_visible:
                    continue

                user_preferences[key]['notification_types'].pop(notification_type)
    return user_preferences


def remove_preferences_with_no_access(preferences: dict, user) -> dict:
    """
    Filter out notifications visible to forum roles from user preferences.

    :param preferences: User preferences dictionary
    :param user: User object
    :return: Updated user preferences dictionary
    """
    user_preferences = preferences['notification_preference_config']
    user_forum_roles = get_user_forum_roles(user.id, preferences['course_id'])
    notifications_with_visibility_settings = get_notification_types_with_visibility_settings()
    preferences['notification_preference_config'] = filter_out_visible_notifications(
        user_preferences,
        notifications_with_visibility_settings,
        user_forum_roles
    )
    return preferences
