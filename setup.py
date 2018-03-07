from setuptools import setup

setup(
    name='quick-connect',
    version='1.2.1',
    packages=['quicknet'],
    package_data={'': ['server_example.py', 'client_example.py']},
    include_package_data=True,
    url='https://github.com/Zwork101/quick-net',
    license='MIT',
    author='Zwork101',
    author_email='zwork101@gmail.com',
    description='Sockets don\'t have to be a pain'
)
