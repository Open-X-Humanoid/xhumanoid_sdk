from setuptools import find_packages, setup
import os
from glob import glob

package_name = 'xhumanoid_mujoco_sim'

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
    description='MuJoCo simulators exposing the xhumanoid_sdk robot and dexterous hand interfaces',
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'sim_node = xhumanoid_mujoco_sim.sim_node:main',
            'hand_sim_node = xhumanoid_mujoco_sim.hand_sim_node:main',
        ],
    },
)
