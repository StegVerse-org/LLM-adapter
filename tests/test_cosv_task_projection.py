import subprocess,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class TestLLMACOSV(unittest.TestCase):
    def test_projection(self):
        cp=subprocess.run([sys.executable,str(ROOT/"scripts/check_cosv_task_projection.py")],cwd=ROOT,text=True,capture_output=True)
        self.assertEqual(cp.returncode,0,cp.stdout+cp.stderr)
        self.assertIn("LLMA_COSV_TASK_PROJECTION_PASS",cp.stdout)
if __name__=="__main__": unittest.main()
