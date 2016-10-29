from distutils.core import setup

setup(name='m',
      version='0.1.0',
      packages=['m', 'm.security'],
      install_requires=['WebOb>=1.6.1'],
      author = "comyn",
      author_email = "me@xueming.li",
      description = "This is a very light web framework",
      license = "Apache License 2.0",
)