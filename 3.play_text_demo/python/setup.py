from setuptools import find_packages, setup
import os
from glob import glob

package_name = 'play_text_demo_py'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob('launch/*.py')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='ryan',
    maintainer_email='ryan.liu@x-humanoid.com',
    description='Play text demo using lyre TTS service (Python)',
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'play_text_node = play_text_demo.play_text_node:main',
        ],
    },
)