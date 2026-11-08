import {build} from 'esbuild'
import {resolve} from 'node:path'
await build({entryPoints:['tests/desktop.render.jsx'],bundle:true,platform:'node',format:'esm',packages:'external',outfile:'.dev/desktop-tests.mjs',alias:{'@hermes/plugin-sdk':resolve('demo/sdk.js')}})
await import(resolve('.dev/desktop-tests.mjs'))
