from setuptools import find_packages, setup

package_name = 'py_raton_gato'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/py_raton_gato/launch', ['launch/juego.launch.py']),
        ('share/py_raton_gato/config', ['config/juego.yaml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='pablo',
    maintainer_email='pcarneadol@gmail.com',
    description='TODO: Package description',
    license='Apache-2.0',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'raton = py_raton_gato.raton:main',
            'gato = py_raton_gato.gato:main',
            'juez = py_raton_gato.juez:main',
            #'spawner = py_raton_gato.spawner:main',
        ],
    },
)
