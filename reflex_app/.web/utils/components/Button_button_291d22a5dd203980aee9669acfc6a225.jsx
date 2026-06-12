
import {Fragment,memo,useContext,useEffect} from "react"
import {isTrue} from "$/utils/state"
import {StateContexts} from "$/utils/context"
import {jsx} from "@emotion/react"






export const Button_button_291d22a5dd203980aee9669acfc6a225 = memo(({children}) => {
    const reflex___state____state__cura___state____app_state = useContext(StateContexts.reflex___state____state__cura___state____app_state)



    return(
        jsx("button",{css:({ ["width"] : "100%", ["padding"] : "12px", ["background"] : (reflex___state____state__cura___state____app_state.is_loading_rx_state_ ? "#252535" : "#818cf8"), ["color"] : "#fff", ["border"] : "none", ["borderRadius"] : "8px", ["fontFamily"] : "Rajdhani, system-ui, sans-serif", ["--default-font-family"] : "Rajdhani, system-ui, sans-serif", ["fontSize"] : "13px", ["letterSpacing"] : "0.08em", ["cursor"] : "pointer", ["textAlign"] : "center", ["marginTop"] : "4px", ["boxShadow"] : "0 4px 14px #818cf84d", ["&:hover"] : ({ ["opacity"] : "0.9" }) }),disabled:reflex___state____state__cura___state____app_state.is_loading_rx_state_,type:"submit"},children)
    )
});
