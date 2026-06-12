
import {Fragment,memo,useContext,useEffect} from "react"
import {isTrue} from "$/utils/state"
import {Text as RadixThemesText} from "@radix-ui/themes"
import {StateContexts} from "$/utils/context"
import {jsx} from "@emotion/react"






export const Text_text_259df280e103d3e37409b5e849247418 = memo(({children}) => {
    const reflex___state____state__cura___state____app_state = useContext(StateContexts.reflex___state____state__cura___state____app_state)



    return(
        jsx(RadixThemesText,{as:"p",css:({ ["&"] : ((reflex___state____state__cura___state____app_state.edit_tx_type_rx_state_?.valueOf?.() === "xfr"?.valueOf?.()) ? ({ ["font_size"] : "9px", ["font_family"] : "'Share Tech Mono', monospace", ["letter_spacing"] : "0.08em", ["padding"] : "3px 10px", ["border_radius"] : "20px", ["color"] : "#8282a2", ["background"] : "#8282a21a", ["border"] : "1px solid #8282a255" }) : ({ ["font_size"] : "9px", ["font_family"] : "'Share Tech Mono', monospace", ["letter_spacing"] : "0.08em", ["padding"] : "3px 10px", ["border_radius"] : "20px", ["color"] : "#4e4e6a", ["background"] : "transparent", ["border"] : "1px solid #252535" })) })},children)
    )
});
