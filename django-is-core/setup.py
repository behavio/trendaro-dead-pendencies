from setuptools import setup, find_packages

from is_core.version import get_version

setup(
    name='django-is-core',
    version=get_version(),
    description="Information systems core.",
    keywords='django, admin, information systems, REST',
    author='Lubos Matl',
    author_email='matllubos@gmail.com',
    url='https://github.com/matllubos/django-is-core',
    license='LGPL',
    package_dir={'is_core': 'is_core'},
    include_package_data=True,
    packages=find_packages(),
    classifiers=[
        'Development Status :: 6 - Beta',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: GNU LESSER GENERAL PUBLIC LICENSE (LGPL)',
        'Natural Language :: Czech',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Internet :: WWW/HTTP :: Site Management',
    ],
    install_requires=[
        'django>=1.8',
        'django-class-based-auth-views>=0.3',
        'python-dateutil>=2.2',
        'pytz',
        'factory-boy>=2.5.2',
        'django-apptemplates @ https://github.com/behavio/trendaro-dead-pendencies/releases/download/v1.1/django-apptemplates-0.3.tar.gz',
        'django-piston @ https://github.com/behavio/trendaro-dead-pendencies/releases/download/v1.1/django-piston-1.2.10.tar.gz',
        'django-block-snippets @ https://github.com/behavio/trendaro-dead-pendencies/releases/download/v1.1/django-block-snippets-0.1.1.tar.gz',
        'django-chamber @ https://github.com/behavio/trendaro-dead-pendencies/releases/download/v1.1/django-chamber-0.1.7.tar.gz',
        'django-project-info @ https://github.com/behavio/trendaro-dead-pendencies/releases/download/v1.1/django-project-info-0.2.5.tar.gz',
    ],
    zip_safe=False
)
