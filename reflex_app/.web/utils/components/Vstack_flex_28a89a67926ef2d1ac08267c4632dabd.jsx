
import {Fragment,memo,useContext,useEffect} from "react"
import {isTrue} from "$/utils/state"
import {Flex as RadixThemesFlex} from "@radix-ui/themes"
import {StateContexts} from "$/utils/context"
import {jsx} from "@emotion/react"






export const Vstack_flex_28a89a67926ef2d1ac08267c4632dabd = memo(({children}) => {
    const reflex___state____state__cura___state____app_state = useContext(StateContexts.reflex___state____state__cura___state____app_state)



    return(
        jsx(RadixThemesFlex,{align:"start",className:"rx-Stack",css:({ ["background"] : "rgba(255,255,255,0.08)", ["borderRadius"] : "8px", ["padding"] : "10px 12px", ["border"] : (reflex___state____state__cura___state____app_state.wi_active_rx_state_ ? "1px solid #FF9F0A33" : "1px solid rgba(255,255,255,0.08)"), ["gap"] : "7px", ["width"] : "100%" }),direction:"column",gap:"3"},children)
    )
});
