"""Use copy-based Hugging Face caching when Windows symlinks are unavailable."""

from huggingface_hub import file_download


def _symlinks_are_unsupported(*args, **kwargs):
    return False


file_download.are_symlinks_supported = _symlinks_are_unsupported