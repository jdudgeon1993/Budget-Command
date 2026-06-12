
import {Fragment,memo,useContext,useEffect} from "react"
import {isTrue,refs} from "$/utils/state"
import {Toaster,toast} from "sonner"
import {ColorModeContext} from "$/utils/context"
import {jsx} from "@emotion/react"






export const MemoizedToastProvider = memo(({}) => {
    const { resolvedColorMode } = useContext(ColorModeContext)
refs['__toast'] = toast


    return(
        jsx(Toaster,{closeButton:false,expand:true,position:"bottom-right",richColors:true,theme:resolvedColorMode},)
    )
});
