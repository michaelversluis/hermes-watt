// Development-only adapter. The shipped plugin imports the real Hermes SDK.
export {useQuery, useMutation, QueryClient, QueryClientProvider} from '@tanstack/react-query'
export const host={state:{profile:{get:()=> 'demo'},gateway:{get:()=> 'open'}},navigate:()=>{}}
export const useValue=atom=>atom.get()
export const gatewayActivationEpoch=()=>0
export const ROUTES_AREA='routes'
export const SIDEBAR_NAV_AREA='sidebar.nav'
export const PALETTE_AREA='palette'
