# -*- coding: utf-8 -*-
#
# Copyright © Spyder Project Contributors
# Licensed under the terms of the MIT License
# (see spyder/__init__.py for details)

"""
File used to start IPython kernels
"""

import os
import os.path as osp
import sys


def sympy_config(mpl_backend):
    """Sympy configuration"""
    if mpl_backend is not None:
        lines = """
from sympy.interactive import init_session
init_session()
%matplotlib {0}
""".format(mpl_backend)
    else:
        lines = """
from sympy.interactive import init_session
init_session()
"""

    return lines


def kernel_config():
    """Create a config object with IPython kernel options"""
    external_interpreter = \
                   os.environ.get('EXTERNAL_INTERPRETER', '').lower() == "true"


    from IPython.core.application import get_ipython_dir
    from traitlets.config.loader import Config, load_pyconfig_files
    if not external_interpreter:
        from spyder.config.main import CONF
        from spyder.utils.programs import is_module_installed
    else:
        # We add "spyder" to sys.path for external interpreters,
        # so this works!
        # See create_kernel_spec of plugins/ipythonconsole
        from config.main import CONF
        from utils.programs import is_module_installed

    # ---- IPython config ----
    try:
        profile_path = osp.join(get_ipython_dir(), 'profile_default')
        cfg = load_pyconfig_files(['ipython_config.py',
                                   'ipython_kernel_config.py'],
                                  profile_path)
    except:
        cfg = Config()
    
    # ---- Spyder config ----
    spy_cfg = Config()
    
    # Until we implement Issue 1052
    spy_cfg.InteractiveShell.xmode = 'Plain'
    
    # Run lines of code at startup
    run_lines_o = CONF.get('ipython_console', 'startup/run_lines')
    if run_lines_o:
        spy_cfg.IPKernelApp.exec_lines = [x.strip() for x in run_lines_o.split(',')]
    else:
        spy_cfg.IPKernelApp.exec_lines = []
    
    # Pylab configuration
    mpl_backend = None
    mpl_installed = is_module_installed('matplotlib')
    pylab_o = CONF.get('ipython_console', 'pylab')

    if mpl_installed and pylab_o:
        # Get matplotlib backend
        if not external_interpreter:
            if os.environ["QT_API"] == 'pyqt5':
                qt_backend = 'qt5'
            else:
                qt_backend = 'qt'

            backend_o = CONF.get('ipython_console', 'pylab/backend', 0)
            backends = {0: 'inline', 1: qt_backend, 2: qt_backend, 3: 'osx',
                        4: 'gtk', 5: 'wx', 6: 'tk'}
            mpl_backend = backends[backend_o]
        else:
            mpl_backend = 'inline'

        # Automatically load Pylab and Numpy, or only set Matplotlib
        # backend
        autoload_pylab_o = CONF.get('ipython_console', 'pylab/autoload')
        if autoload_pylab_o:
            spy_cfg.IPKernelApp.exec_lines.append(
                                              "%pylab {0}".format(mpl_backend))
        else:
            spy_cfg.IPKernelApp.exec_lines.append(
                                         "%matplotlib {0}".format(mpl_backend))

        # Inline backend configuration
        if mpl_backend == 'inline':
           # Figure format
           format_o = CONF.get('ipython_console',
                               'pylab/inline/figure_format', 0)
           formats = {0: 'png', 1: 'svg'}
           spy_cfg.InlineBackend.figure_format = formats[format_o]
           
           # Resolution
           spy_cfg.InlineBackend.rc = {'figure.figsize': (6.0, 4.0),
                                   'savefig.dpi': 72,
                                   'font.size': 10,
                                   'figure.subplot.bottom': .125,
                                   'figure.facecolor': 'white',
                                   'figure.edgecolor': 'white'
                                   }
           resolution_o = CONF.get('ipython_console', 
                                   'pylab/inline/resolution')
           spy_cfg.InlineBackend.rc['savefig.dpi'] = resolution_o
           
           # Figure size
           width_o = float(CONF.get('ipython_console', 'pylab/inline/width'))
           height_o = float(CONF.get('ipython_console', 'pylab/inline/height'))
           spy_cfg.InlineBackend.rc['figure.figsize'] = (width_o, height_o)
    
    # Run a file at startup
    use_file_o = CONF.get('ipython_console', 'startup/use_run_file')
    run_file_o = CONF.get('ipython_console', 'startup/run_file')
    if use_file_o and run_file_o:
        spy_cfg.IPKernelApp.file_to_run = run_file_o
    
    # Autocall
    autocall_o = CONF.get('ipython_console', 'autocall')
    spy_cfg.ZMQInteractiveShell.autocall = autocall_o
    
    # To handle the banner by ourselves in IPython 3+
    spy_cfg.ZMQInteractiveShell.banner1 = ''
    
    # Greedy completer
    greedy_o = CONF.get('ipython_console', 'greedy_completer')
    spy_cfg.IPCompleter.greedy = greedy_o
    
    # Sympy loading
    sympy_o = CONF.get('ipython_console', 'symbolic_math')
    if sympy_o:
        lines = sympy_config(mpl_backend)
        spy_cfg.IPKernelApp.exec_lines.append(lines)

    # Merge IPython and Spyder configs. Spyder prefs will have prevalence
    # over IPython ones
    cfg._merge(spy_cfg)
    return cfg


def varexp(line):
    """
    Spyder's variable explorer magic
    
    Used to generate plots, histograms and images of the variables displayed
    on it.
    """
    ip = get_ipython()       #analysis:ignore
    funcname, name = line.split()
    import spyder.pyplot
    __fig__ = spyder.pyplot.figure();
    __items__ = getattr(spyder.pyplot, funcname[2:])(ip.user_ns[name])
    spyder.pyplot.show()
    del __fig__, __items__


def main():
    # Remove this module's path from sys.path:
    try:
        sys.path.remove(osp.dirname(__file__))
    except ValueError:
        pass

    try:
        locals().pop('__file__')
    except KeyError:
        pass
    __doc__ = ''
    __name__ = '__main__'

    # Add current directory to sys.path (like for any standard Python interpreter
    # executed in interactive mode):
    sys.path.insert(0, '')

    # Fire up the kernel instance.
    from ipykernel.kernelapp import IPKernelApp
    from spyder.widgets.externalshell.spyder_kernel import SpyderKernel

    ipk_temp = IPKernelApp.instance()
    ipk_temp.kernel_class = SpyderKernel
    try:
        ipk_temp.config = kernel_config()
    except:
        pass
    ipk_temp.initialize()

    # Grabbing the kernel's shell to share its namespace with our
    # Variable Explorer
    __ipythonshell__ = ipk_temp.shell

    # Issue 977: Since kernel.initialize() has completed execution, 
    # we can now allow the monitor to communicate the availablility of
    # the kernel to accept front end connections.
    __ipythonkernel__ = ipk_temp
    del ipk_temp

    # NOTE: Leave this and other magic modifications *after* setting
    # __ipythonkernel__ to not have problems while starting kernels
    __ipythonshell__.register_magic_function(varexp)

    # Start the (infinite) kernel event loop.
    __ipythonkernel__.start()


if __name__ == '__main__':
    main()
