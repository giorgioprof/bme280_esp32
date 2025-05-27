class MissingConfig(Exception):
    message = 'There is no config file on the device'
    
    def __str__(self):
        return self.message
    
    
class InvalidConfig(Exception):
    message = 'Invalid configuration'

    def __str__(self):
        return self.message
