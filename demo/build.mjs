import {build} from 'esbuild'
import {copyFile,mkdir} from 'node:fs/promises'
import {resolve} from 'node:path'
await mkdir('.dev/preview',{recursive:true})
await build({entryPoints:['demo/preview.jsx'],bundle:true,format:'esm',outfile:'.dev/preview/app.js',alias:{'@hermes/plugin-sdk':resolve('demo/sdk.js')},define:{'process.env.NODE_ENV':'"production"'}})
await copyFile('demo/index.html','.dev/preview/index.html')
