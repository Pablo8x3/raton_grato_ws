import sys
if sys.prefix == '/usr':
    sys.real_prefix = sys.prefix
    sys.prefix = sys.exec_prefix = '/home/pablo/Documents/ros_practica/raton_grato_ws/install/py_raton_gato'
