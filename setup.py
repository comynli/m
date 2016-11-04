from distutils.core import setup

setup(name='m',
      version='0.1.0',
      packages=['m', 'm.security', 'm.extensions', 'm.extensions.sqlalchemy'],
      install_requires=[
          'WebOb>=1.6.1',
          'sqlalchemy>=1.0.0',
          'pyhocon>=0.3.0',
      ],
      author="comyn",
      author_email="me@xueming.li",
      description="This is a very light web framework",
      license="Apache-2",
      )
