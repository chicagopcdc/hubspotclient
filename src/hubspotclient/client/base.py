import abc
import six


class CrmClient(six.with_metaclass(abc.ABCMeta)):
    """
    Abstract class to define behavior of an hubspot client implementation.
    """

    # @abc.abstractmethod
    # def healthy(self):
    #     """Indicate whether the hubspot service is available."""

    @abc.abstractmethod
    def get_contact_by_email(self, email, hubspot_id=None):
        pass

    @abc.abstractmethod
    def get_contacts_by_committee(self, committee):
        pass

    @abc.abstractmethod
    def get_commitees_info(self, committee):
        pass

    # @abc.abstractmethod
    # def get_associated_company(self, resource_path):
    #     pass

    @abc.abstractmethod
    def create_contact(self, property_json):
        pass

    @abc.abstractmethod
    def update_contact(self, property_json):
        pass
