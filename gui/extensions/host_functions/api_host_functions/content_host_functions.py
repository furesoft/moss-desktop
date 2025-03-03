from rm_api import Content
from .. import definitions as d


@d.host_fn()
def moss_api_content_new_notebook(page_count: int = 1):
    content = Content.new_notebook(d.api.author_id, page_count)

    d.extension_manager.content_objects[id(content)] = content

    return id(content)


@d.host_fn()
def moss_api_content_new_pdf():
    content = Content.new_pdf()

    d.extension_manager.content_objects[id(content)] = content

    return id(content)


@d.host_fn()
def moss_api_content_new_epub():
    content = Content.new_epub()

    d.extension_manager.content_objects[id(content)] = content

    return id(content)
