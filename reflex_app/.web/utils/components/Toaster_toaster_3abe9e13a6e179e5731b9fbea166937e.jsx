
import {Fragment,memo,useContext,useEffect} from "react"
import {isTrue,refs} from "$/utils/state"
import {Toaster,toast} from "sonner"
import {ColorModeContext} from "$/utils/context"
import {jsx} from "@emotion/react"






export const Toaster_toaster_3abe9e13a6e179e5731b9fbea166937e = memo(({children}) => {
    const { resolvedColorMode } = useContext(ColorModeContext)
refs['__toast'] = toast


    return(
        jsx(Toaster,{closeButton:false,expand:true,position:"bottom-right",richColors:true,theme:resolvedColorMode},)
    )
});
