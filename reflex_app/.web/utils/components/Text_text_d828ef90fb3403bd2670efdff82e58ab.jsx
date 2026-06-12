
import {Fragment,memo,useContext,useEffect} from "react"
import {isTrue} from "$/utils/state"
import {Text as RadixThemesText} from "@radix-ui/themes"
import {StateContexts} from "$/utils/context"
import {jsx} from "@emotion/react"






export const Text_text_d828ef90fb3403bd2670efdff82e58ab = memo(({children}) => {
    const reflex___state____state__cura___state____app_state = useContext(StateContexts.reflex___state____state__cura___state____app_state)



    return(
        jsx(RadixThemesText,{as:"p",css:({ ["&"] : ((reflex___state____state__cura___state____app_state.edit_tx_type_rx_state_?.valueOf?.() === "out"?.valueOf?.()) ? ({ ["font_size"] : "9px", ["font_family"] : "'Share Tech Mono', monospace", ["letter_spacing"] : "0.08em", ["padding"] : "3px 10px", ["border_radius"] : "20px", ["color"] : "#f87171", ["background"] : "#f871711a", ["border"] : "1px solid #f8717155" }) : ({ ["font_size"] : "9px", ["font_family"] : "'Share Tech Mono', monospace", ["letter_spacing"] : "0.08em", ["padding"] : "3px 10px", ["border_radius"] : "20px", ["color"] : "#4e4e6a", ["background"] : "transparent", ["border"] : "1px solid #252535" })) })},children)
    )
});
