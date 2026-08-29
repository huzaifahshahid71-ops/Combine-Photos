from backend_workflow import WorkflowMixin
from backend_render import RenderMixin
from combine_photos_core import HEIF_AVAILABLE, TIFFFILE_AVAILABLE, ImageItem

class BackendMixin(WorkflowMixin, RenderMixin):
    pass
