# Runtime hook for transformers to prevent inspect.getsource errors in frozen apps
import sys

# Only run if frozen
if getattr(sys, 'frozen', False):
    try:
        import transformers.utils.doc

        # Monkeypatch get_docstring_indentation_level because inspect.getsource fails on frozen code
        def dummy_get_docstring_indentation_level(docstring):
            return 0

        transformers.utils.doc.get_docstring_indentation_level = dummy_get_docstring_indentation_level
        print("Hook: patched transformers.utils.doc.get_docstring_indentation_level")
    except ImportError:
        pass
