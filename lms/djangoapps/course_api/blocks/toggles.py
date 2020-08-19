"""
Toggles for Course API.
"""


from openedx.core.djangoapps.waffle_utils import CourseWaffleFlag, WaffleFlag, WaffleFlagNamespace


COURSE_BLOCKS_API_NAMESPACE = WaffleFlagNamespace(name=u'course_blocks_api')

"""
.. toggle_name: course_blocks_api.hide_access_denials
.. toggle_implementation: WaffleFlag
.. toggle_default: False
.. toggle_description: Waffle flag to hide access denial messages in the course blocks.
.. toggle_category: course api
.. toggle_use_cases: incremental_release, open_edx
.. toggle_creation_date: ??
.. toggle_expiration_date: None
.. toggle_warnings: None
.. toggle_tickets: ??
.. toggle_status: supported
"""
HIDE_ACCESS_DENIALS_FLAG = WaffleFlag(
    waffle_namespace=COURSE_BLOCKS_API_NAMESPACE,
    flag_name=u'hide_access_denials',
    module_name=__name__,
)
