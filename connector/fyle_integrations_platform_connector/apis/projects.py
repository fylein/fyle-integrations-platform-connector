from .base import Base


class Projects(Base):
    """Class for Projects APIs."""

    def __init__(self):
        Base.__init__(self, attribute_type='PROJECT', query_params={'is_enabled': 'eq.true'})
