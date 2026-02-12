
import subprocess
import os, sys
import site
from importlib import reload, invalidate_caches

def init():
    # Get the path to the 'vendor' directory
    addon_path = os.path.dirname(__file__)
    vendor_path = os.path.join(addon_path, "user_files", "libs")
    models_path = os.path.join(addon_path, "user_files", "models")
    os.makedirs(vendor_path, exist_ok=True)
    os.makedirs(models_path, exist_ok=True)

    # Add vendor path to sys.path if it's not already there
    if vendor_path not in sys.path:
        sys.path.append(vendor_path)

    # Anki's ErrorHandler is missing a .flush() method, which some
    # libraries (and Python 3.13) expect. We add a dummy one here.
    if hasattr(sys.stderr, "flush") is False:
        # Most versions of Anki use a custom object for stderr
        try:
            type(sys.stderr).flush = lambda self: None
        except AttributeError:
            # If it's a read-only object, we can wrap it or ignore
            pass

    try:
        import llama_cpp
    except ImportError:
        # Use subprocess to run pip install
        print("anki-greek: installing 'llama_ccp' dependencies")
        try:
            env = os.environ.copy()
            env["CMAKE_ARGS"] = "-DGGML_METAL=on"
            subprocess.run(
                [sys.executable, "-m", "pip", "install", "truststore"],
                env=env
            )
            subprocess.run(
                [sys.executable, "-m", "pip", "install", "--no-cache-dir", "-r",
                    os.path.join(addon_path, "requirements.txt"), "--target", vendor_path],
                capture_output=True,
                text=True,
                check=True,
                env=env
            )
        except subprocess.CalledProcessError as e:
            print(f"anki-greek: Err: {e.stderr}\nOut: {e.stdout}")

        # Reload the site module to make the newly installed package available in sys.path
        invalidate_caches()
        reload(site)
        # Now you can import the package
        import llama_cpp

    return addon_path, vendor_path, models_path
