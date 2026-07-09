from setuptools import find_packages, setup
import os
from glob import glob

package_name = 'gps_data_display_py'

setup(
    name=package_name,
    version='0.0.1',
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
    description='ROS2 node for receiving and parsing GPS data from GPS driver (Python)',
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'gps_data_display_node = gps_data_display.gps_data_display_node:main',
        ],
    },
)