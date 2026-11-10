import React from 'react'
import {createRoot} from 'react-dom/client'
import {QueryClient,QueryClientProvider} from '@tanstack/react-query'
import {WattPage} from '../desktop/plugin.js'
const client=new QueryClient()
const ctx={rest:async (path,options={})=>{
 const response=await fetch('/api/plugins/hermes-watt'+path,{method:options.method||'GET',headers:options.body?{'Content-Type':'application/json'}:{},body:options.body?JSON.stringify(options.body):undefined,signal:AbortSignal.timeout(10000)})
 if(!response.ok)throw new Error('Request unavailable')
 return response.json()
}}
createRoot(document.getElementById('root')).render(<QueryClientProvider client={client}><WattPage ctx={ctx}/></QueryClientProvider>)
