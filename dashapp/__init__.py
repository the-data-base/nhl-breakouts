from pkgutil import extend_path

# Declare the current directory as a package using pkgutil
__path__ = extend_path(__path__, __name__)
