from discord.ext import commands

# define Python user-defined exceptions
class Error(commands.CommandError):
    # Base class for other exceptions
    pass


class PlayerNotFound(Error):
    # Raised when the Bungie API does not find the Player
    def __init__(self, message, payload=None):
        self.message = message
        self.payload = payload # you could add more args
    def __str__(self):
        return str(self.message)

class CharactersNotFound(Error):
    # Raised when a players characters could not be loaded from Bungie API
    def __init__(self, message, payload=None):
        self.message = message
        self.payload = payload # you could add more args
    def __str__(self):
        return str(self.message)

class PrivacyOnException(Error):
    # Raised when there is an issue loading a players inventory
    def __init__(self, message, payload=None):
        self.message = message
        self.payload = payload # you could add more args
    def __str__(self):
        return str(self.message)

class NotaDestinyClass(Error):
    # Raised if the user does not provide a valid Destiny class in their input
    def __init__(self, message, payload=None):
        self.message = message
        self.payload = payload # you could add more args
    def __str__(self):
        return str(self.message)

class NoCharacterOfClass(Error):
    # Raised if the user does not provide a valid Destiny class in their input
    def __init__(self, message, payload=None):
        self.message = message
        self.payload = payload # you could add more args
    def __str__(self):
        return str(self.message)

class SetupIncomplete(Error):
    # Raised if the user does not provide a valid Destiny class in their input
    def __init__(self, message, payload=None):
        self.message = message
        self.payload = payload # you could add more args
    def __str__(self):
        return str(self.message)

class OauthError(Error):
    # Raised if the user does not provide a valid Destiny class in their input
    def __init__(self, message, payload=None):
        self.message = message
        self.payload = payload # you could add more args
    def __str__(self):
        return str(self.message)

class NoValidItem(Error):
    # Raised if the user does not provide a valid Destiny class in their input
    def __init__(self, message, payload=None):
        self.message = message
        self.payload = payload # you could add more args
    def __str__(self):
        return str(self.message)

class ManifestLoadError(Error):
    # Raised if the user does not provide a valid Destiny class in their input
    def __init__(self, message, payload=None):
        self.message = message
        self.payload = payload # you could add more args
    def __str__(self):
        return str(self.message)

class ApiError(Error):
    # Raised if the user does not provide a valid Destiny class in their input
    def __init__(self, message, payload=None):
        self.message = message
        self.payload = payload # you could add more args
    def __str__(self):
        return str(self.message)

class RaidNotFound(Error):
    # Raised if the user does not provide a valid Destiny class in their input
    def __init__(self, message, payload=None):
        self.message = message
        self.payload = payload # you could add more args
    def __str__(self):
        return str(self.message)