from setuptools import find_packages, setup
import os
from glob import glob

package_name = 'point_cloud_display_py'

setup(
    name=package_name,
    version='0.0.1',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob('launch/*.py')),
        (os.path.join('share', package_name, 'rviz'), glob('rviz/*.rviz')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='ryan',
    maintainer_email='ryan.liu@x-humanoid.com',
    description='ROS2 point cloud display node for Livox LiDAR visualization (Python)',
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'point_cloud_display_node = point_cloud_display.point_cloud_display_node:main',
        ],
    },
)