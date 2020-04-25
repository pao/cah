from setuptools import setup, find_packages

setup(
    name = "BerryCAH",
    version = "0.1",
    packages = find_packages(exclude=['tests']),
    
    install_requires = """
        PyYAML==3.10
        Twisted==20.3.0
        autobahn==0.5.9
        pystache==0.5.3
        zope.interface==4.4.2
    """,
    
    include_package_data = True,

)
