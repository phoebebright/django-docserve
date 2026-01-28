# setup.py

from setuptools import setup, find_packages

setup(
    name='django-docserve',
    version='0.3.38',
    packages=find_packages(),
    include_package_data=True,
    license='MIT License',
    description='A reusable Django app to serve MkDocs documentation based on user roles.',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/phoebebright/django-docserve',
    author='Phoebe Bright',
    author_email='phoebebright310@gmail.com',
    classifiers=[
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'Programming Language :: Python :: 3',
    ],
    install_requires=[
        'Django>=3.2,<5.3',
        'mkdocs-material>=9.1.15',
        'setuptools>=65.5.1',
    ],
)
