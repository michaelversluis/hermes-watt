"""Loopback development preview; production uses the Hermes authenticated namespace."""
import argparse
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import uvicorn
from dashboard import plugin_api

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data',required=True)
    parser.add_argument('--port',type=int,default=18180)
    args=parser.parse_args()
    root=Path(args.data).resolve()
    app=FastAPI()
    plugin_api.storage_root=lambda: root
    plugin_api.experiment_settings=lambda: {'endpoint':'http://127.0.0.1:18082/v1','model':'Qwen3-1.7B-Q8_0'}
    app.include_router(plugin_api.router,prefix='/api/plugins/hermes-watt')
    app.mount('/',StaticFiles(directory=Path(__file__).resolve().parents[1]/'.dev/preview',html=True),name='preview')
    uvicorn.run(app,host='127.0.0.1',port=args.port,access_log=False)
