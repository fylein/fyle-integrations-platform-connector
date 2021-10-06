import setuptools

with open('README.md', 'r') as f:
    long_description = f.read()

setuptools.setup(
    name='fyle_integrations_platform_connector',
    version='0.0.1',
    author='Siva Narayanan',
    author_email='siva@fyle.in',
    description='A common platform connector for all the Fyle Integrations to interact with Fyle Platform APIs',
    license='MIT',
    long_description=long_description,
    long_description_content_type='text/markdown',
    keywords=['fyle', 'api', 'python', 'integration', 'platform', 'connector'],
    url='https://github.com/fylein/fyle-integrations-platform-connector',
    packages=setuptools.find_packages(),
    install_requires=[
        'fyle_accounting_mappings>=0.17.0',
        'fyle>=v0.14.0'
    ],
    classifiers=[
        'Topic :: Internet :: WWW/HTTP',
        'Intended Audience :: Developers',
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ]
)
