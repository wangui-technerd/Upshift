"""Execute the generated notebook against the completed local artifacts."""
from pathlib import Path
import os,sys,subprocess
ROOT=Path(__file__).resolve().parent
os.environ['JUPYTER_PATH']=str(ROOT/'.jupyter/share/jupyter')
os.environ['HF_HUB_OFFLINE']='1'
os.environ['UPSHIFT_RESUMES']=r'C:\Users\HAFSA\Downloads\archive\Resume\Resume.csv'
os.environ['UPSHIFT_JOBS']=r'C:\Users\HAFSA\Downloads\postings.csv'
os.environ['UPSHIFT_SKILLS']=r'C:\Users\HAFSA\Downloads\skills_en.csv'
subprocess.run([sys.executable,'-m','ipykernel','install','--prefix',str(ROOT/'.jupyter'),'--name','upshift-ai','--display-name','UpShift AI (Python 3.12)'],check=True)
import nbformat
from nbclient import NotebookClient
notebook=nbformat.read(ROOT/'notebooks/UpShift_AI_Complete.ipynb',as_version=4)
client=NotebookClient(notebook,timeout=900,kernel_name='upshift-ai',resources={'metadata':{'path':str(ROOT)}})
client.execute()
target=ROOT/'notebooks/UpShift_AI_Complete_Executed.ipynb'
nbformat.write(notebook,target)
assert all(cell.execution_count is not None for cell in notebook.cells if cell.cell_type=='code')
assert not any(output.output_type=='error' for cell in notebook.cells if cell.cell_type=='code' for output in cell.outputs)
print('Executed without errors:',target,flush=True)
