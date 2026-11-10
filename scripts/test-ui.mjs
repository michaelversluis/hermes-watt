import {build} from 'esbuild'
import {resolve} from 'node:path'
await build({entryPoints:['tests/desktop.render.jsx'],bundle:true,platform:'node',format:'esm',packages:'external',outfile:'.dev/desktop-tests.mjs',alias:{'@hermes/plugin-sdk':resolve('demo/sdk.js')}})
await import(resolve('.dev/desktop-tests.mjs'))
const {JSDOM}=await import('jsdom')
const dom=new JSDOM('<!doctype html><html><body></body></html>',{url:'http://127.0.0.1/'})
for(const key of ['window','document','HTMLElement','Event','MouseEvent'])globalThis[key]=dom.window[key]
globalThis.IS_REACT_ACT_ENVIRONMENT=true
await build({entryPoints:['tests/desktop.interaction.jsx'],bundle:true,platform:'node',format:'esm',packages:'external',outfile:'.dev/desktop-interaction.mjs',alias:{'@hermes/plugin-sdk':resolve('demo/sdk.js')}})
try {await import(resolve('.dev/desktop-interaction.mjs'))} finally {dom.window.close()}
