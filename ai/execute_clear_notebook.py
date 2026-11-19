"""Execute the self-contained teaching notebook and retain partial outputs on failure."""
from pathlib import Path
import os,nbformat,asyncio
from nbclient import NotebookClient
ROOT=Path(__file__).resolve().parent
os.environ['JUPYTER_PATH']=str(ROOT/'.jupyter/share/jupyter')
os.environ['HF_HUB_OFFLINE']='1'
if os.name=='nt':asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
source=ROOT/'notebooks/UpShift_Clear_Steps.ipynb'
target=ROOT/'notebooks/UpShift_Clear_Steps_Executed.ipynb'
notebook=nbformat.read(source,as_version=4)
def progress(cell,cell_index,**kwargs):
    if cell.cell_type=='markdown':print(cell.source.splitlines()[0],flush=True)
client=NotebookClient(notebook,timeout=2400,kernel_name='upshift-ai',
    resources={'metadata':{'path':str(ROOT)}},on_cell_start=progress)
try:
    client.execute()
except BaseException:
    nbformat.write(notebook,ROOT/'notebooks/UpShift_Clear_Steps_Partial.ipynb')
    raise
else:
    nbformat.write(notebook,target)
    code=[c for c in notebook.cells if c.cell_type=='code']
    assert all(c.execution_count is not None for c in code)
    assert not any(o.output_type=='error'for c in code for o in c.outputs)
    print('PASSED:',len(code),'executed code cells;',target,flush=True)
